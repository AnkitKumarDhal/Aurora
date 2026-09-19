from __future__ import annotations

import json
import re
from typing import Any

import httpx

from backend.ai.clinical_schema import (
    InterviewExtraction,
    normalize_field_name,
)
from backend.ai.interview.objectives import normalize_topic
from backend.config import settings


class InterviewExtractor:
    """
    Uses the local LLM only for semantic fact extraction.

    It does not generate the next question and it does not decide
    whether the interview is complete.
    """

    def __init__(self) -> None:
        self.url = settings.lemonade_url
        self.model = settings.lemonade_model
        self.timeout = settings.lemonade_timeout
        self.enabled = settings.interview_ai_enabled
        self.provider = settings.interview_ai_provider

    async def extract(
        self,
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
    ) -> InterviewExtraction:
        if not patient_text.strip():
            return InterviewExtraction()

        if not self.enabled:
            return self._fallback(patient_text, known_fields, topic)

        if self.provider != "lemonade":
            return self._fallback(patient_text, known_fields, topic)

        try:
            result = await self._call_lemonade(
                patient_text=patient_text,
                known_fields=known_fields,
                topic=topic,
            )
            return result
        except Exception:
            # Interview must remain usable even when the local model is
            # temporarily unavailable.
            return self._fallback(patient_text, known_fields, topic)

    async def _call_lemonade(
        self,
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
    ) -> InterviewExtraction:
        system_prompt = """
You are Aurora's clinical fact extractor.

Extract facts from ONLY the patient's latest answer.

You are NOT a doctor.
You do NOT diagnose.
You do NOT choose the next question.
You do NOT decide whether the interview is complete.

Return ONLY valid JSON with this exact shape:

{
  "topic": "headache",
  "fields": {
    "field_name": "value"
  },
  "negatives": [
    "field_name"
  ]
}

Rules:
- Extract every useful fact explicitly stated in the latest answer.
- Multiple facts may be extracted from one answer.
- Preserve explicit negatives. "I do not have nausea" means
  negatives contains "nausea_vomiting".
- Never treat silence as a negative.
- Correct previously known information when the patient explicitly
  gives a new value.
- Use concise values.
- Use numeric values for severity when the patient gives 0-10 severity.
- Use booleans for clear yes/no facts when appropriate.
- Do not invent information.
- Use null topic when no topic can be inferred.
- Allowed field names are clinical interview fields such as:
  chief_complaint, onset, site, severity, character, timing,
  aggravating_factors, relieving_factors, radiation,
  associated_symptoms, breathing_difficulty, nausea_vomiting,
  vision_or_neuro, cough, wheeze, location, bowel_changes,
  appearance, itch_or_pain, spread, urinary_frequency,
  urinary_burning, urinary_blood, fever, fatigue, weight_change,
  past_medical_history, medications, allergies.
""".strip()

        user_prompt = (
            f"Current topic: {normalize_topic(topic)}\n"
            f"Known facts: {json.dumps(known_fields, ensure_ascii=False)}\n"
            f"Patient answer: {patient_text.strip()}"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0,
            "max_tokens": 128,
        }

        if settings.lemonade_json_mode:
            payload["response_format"] = {
                "type": "json_object",
            }

        payload["enable_thinking"] = False

        timeout = httpx.Timeout(
            connect=5.0,
            read=self.timeout,
            write=5.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self.url,
                json=payload,
            )

        response.raise_for_status()

        body = response.json()

        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )

        if isinstance(content, list):
            content = "".join(
                str(part.get("text", ""))
                if isinstance(part, dict)
                else str(part)
                for part in content
            )

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Lemonade returned empty model content")

        parsed = self._parse_json(content)

        extraction = InterviewExtraction.model_validate(parsed)

        return self._sanitize(extraction)

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        cleaned = content.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise

            value = json.loads(cleaned[start: end + 1])

        if not isinstance(value, dict):
            raise ValueError("LLM JSON root must be an object")

        return value

    @staticmethod
    def _sanitize(
        extraction: InterviewExtraction,
    ) -> InterviewExtraction:
        fields: dict[str, Any] = {}

        for raw_name, value in extraction.fields.items():
            normalized = normalize_field_name(raw_name)

            if normalized is None:
                continue

            if value is None:
                continue

            if isinstance(value, str):
                value = value.strip()

                if not value:
                    continue

            fields[normalized] = value

        negatives: list[str] = []

        for raw_name in extraction.negatives:
            normalized = normalize_field_name(raw_name)

            if normalized and normalized not in negatives:
                negatives.append(normalized)

        topic = normalize_topic(extraction.topic)

        if topic == "general" and extraction.topic is None:
            topic = None

        return InterviewExtraction(
            topic=topic,
            fields=fields,
            negatives=negatives,
        )

    @staticmethod
    def _fallback(
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
    ) -> InterviewExtraction:
        """
        Small deterministic safety net.

        The real path is the Lemonade extractor.
        This exists so a temporary model outage does not completely
        break the patient flow.
        """

        text = patient_text.strip()
        normalized = text.lower()

        fields: dict[str, Any] = {}

        if not known_fields.get("chief_complaint"):
            fields["chief_complaint"] = text

        topic_value = topic

        topic_keywords = {
            "headache": (
                "headache",
                "head pain",
                "migraine",
            ),
            "chest_pain": (
                "chest pain",
                "chest pressure",
                "chest discomfort",
            ),
            "respiratory": (
                "cough",
                "breathless",
                "shortness of breath",
                "breathing problem",
            ),
            "gastrointestinal": (
                "stomach",
                "abdomen",
                "abdominal",
                "diarrhea",
                "vomiting",
                "nausea",
            ),
            "skin": (
                "rash",
                "itching",
                "skin",
            ),
            "urinary": (
                "urine",
                "urination",
                "burning while urinating",
            ),
        }

        for candidate, keywords in topic_keywords.items():
            if any(keyword in normalized for keyword in keywords):
                topic_value = candidate
                break

        severity_match = re.search(
            r"\b([0-9]|10)\s*(?:/|out of)\s*10\b",
            normalized,
        )

        if severity_match:
            try:
                fields["severity"] = int(severity_match.group(1))
            except ValueError:
                pass

        negatives: list[str] = []

        negative_patterns = {
            "nausea_vomiting": (
                "no nausea",
                "no vomiting",
                "not nauseous",
                "no nausea or vomiting",
            ),
            "breathing_difficulty": (
                "no breathing difficulty",
                "no shortness of breath",
                "breathing is normal",
            ),
            "cough": (
                "no cough",
            ),
            "wheeze": (
                "no wheezing",
                "no wheeze",
            ),
            "urinary_burning": (
                "no burning while urinating",
                "no burning during urination",
            ),
            "urinary_blood": (
                "no blood in urine",
            ),
            "vision_or_neuro": (
                "no numbness",
                "no weakness",
                "no vision changes",
            ),
        }

        for field, phrases in negative_patterns.items():
            if any(phrase in normalized for phrase in phrases):
                negatives.append(field)

        onset_match = re.search(
            r"\b(\d+)\s*(day|days|hour|hours|week|weeks|month|months|year|years)\b",
            normalized,
        )

        if onset_match:
            fields["onset"] = (
                f"{onset_match.group(1)} {onset_match.group(2)}"
            )

        return InterviewExtraction(
            topic=topic_value,
            fields=fields,
            negatives=negatives,
        )
