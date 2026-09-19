from __future__ import annotations

import json
import re
from typing import Any

import httpx

from backend.ai.clinical_schema import InterviewExtraction, normalize_field_name
from backend.ai.interview.objectives import normalize_topic
from backend.config import settings


class InterviewExtractor:
    def __init__(self) -> None:
        self.url = settings.lemonade_url
        self.model = settings.lemonade_model
        self.timeout = settings.lemonade_timeout
        self.enabled = settings.interview_ai_enabled
        self.provider = settings.interview_ai_provider

    async def extract(self, patient_text: str, known_fields: dict[str, Any], topic: str | None) -> InterviewExtraction:
        if not patient_text.strip():
            return InterviewExtraction()

        if not self.enabled or self.provider != "lemonade":
            return self._fallback(patient_text, known_fields, topic)

        return await self._call_lemonade(patient_text, known_fields, topic)

    async def _call_lemonade(self, patient_text: str, known_fields: dict[str, Any], topic: str | None) -> InterviewExtraction:
        system_prompt = (
            "Extract clinical facts from only the latest patient answer. "
            "Return exactly one JSON object with keys topic, fields, negatives. "
            "Do not explain anything. Do not repeat the patient sentence. "
            "Extract every useful explicit fact, including multiple facts. "
            "Keep every value to at most 6 words. "
            "Use numeric severity for 0-10 pain scores. "
            "Use booleans for explicit yes/no facts when appropriate. "
            "Put explicitly denied facts in negatives. "
            "Never infer a negative from silence. "
            "Use only these field names: chief_complaint,onset,site,severity,character,"
            "timing,aggravating_factors,relieving_factors,radiation,associated_symptoms,"
            "breathing_difficulty,nausea_vomiting,vision_or_neuro,cough,wheeze,location,"
            "bowel_changes,appearance,itch_or_pain,spread,urinary_frequency,urinary_burning,"
            "urinary_blood,fever,fatigue,weight_change,past_medical_history,medications,allergies."
        )

        compact_known_fields = {
            key: value for key, value in known_fields.items() if key != "chief_complaint"}

        user_prompt = (
            f"Topic: {normalize_topic(topic)}\n"
            f"Known: {json.dumps(compact_known_fields,
                                 ensure_ascii=False, separators=(',', ':'))}\n"
            f"Answer: {patient_text.strip()}"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": 96,
            "enable_thinking": False,
        }

        if settings.lemonade_json_mode:
            payload["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(
            connect=5.0, read=self.timeout, write=5.0, pool=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(self.url, json=payload)

        response.raise_for_status()

        body = response.json()
        choices = body.get("choices")

        if not isinstance(choices, list) or not choices:
            raise ValueError("Lemonade returned no choices")

        message = choices[0].get("message", {})
        content = message.get("content")

        if isinstance(content, list):
            content = "".join(
                str(part.get("text", "")) if isinstance(
                    part, dict) else str(part)
                for part in content
            )

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Lemonade returned empty model content")

        parsed = self._parse_json(content)
        normalized = self._normalize_payload(parsed)

        return self._sanitize(InterviewExtraction.model_validate(normalized))

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        value = json.loads(cleaned)

        if not isinstance(value, dict):
            raise ValueError("LLM JSON root must be an object")

        return value

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)

        topic = normalized.get("topic")
        if topic is not None and not isinstance(topic, str):
            normalized["topic"] = None

        fields = normalized.get("fields")
        if not isinstance(fields, dict):
            normalized["fields"] = {}

        negatives = normalized.get("negatives")

        if isinstance(negatives, dict):
            normalized["negatives"] = [
                str(key)
                for key, value in negatives.items()
                if value is True
            ]
        elif isinstance(negatives, str):
            normalized["negatives"] = [negatives]
        elif not isinstance(negatives, list):
            normalized["negatives"] = []

        return normalized

    @staticmethod
    def _sanitize(extraction: InterviewExtraction) -> InterviewExtraction:
        fields: dict[str, Any] = {}

        for raw_name, value in extraction.fields.items():
            normalized = normalize_field_name(raw_name)

            if normalized is None or value is None:
                continue

            if isinstance(value, str):
                value = value.strip()

                if not value:
                    continue

                value = " ".join(value.split()[:12])

            fields[normalized] = value

        negatives: list[str] = []

        for raw_name in extraction.negatives:
            normalized = normalize_field_name(raw_name)

            if normalized and normalized not in negatives:
                negatives.append(normalized)

        topic = normalize_topic(extraction.topic)

        if topic == "general" and extraction.topic is None:
            topic = None

        return InterviewExtraction(topic=topic, fields=fields, negatives=negatives)

    @staticmethod
    def _fallback(patient_text: str, known_fields: dict[str, Any], topic: str | None) -> InterviewExtraction:
        text = patient_text.strip()
        normalized = text.lower()
        fields: dict[str, Any] = {}

        topic_value = topic

        topic_keywords = {
            "headache": ("headache", "head pain", "migraine"),
            "chest_pain": ("chest pain", "chest pressure", "chest discomfort"),
            "respiratory": ("cough", "breathless", "shortness of breath", "breathing problem"),
            "gastrointestinal": ("stomach", "abdomen", "abdominal", "diarrhea", "vomiting", "nausea"),
            "skin": ("rash", "itching", "skin"),
            "urinary": ("urine", "urination", "burning while urinating"),
        }

        for candidate, keywords in topic_keywords.items():
            if any(keyword in normalized for keyword in keywords):
                topic_value = candidate
                break

        severity_match = re.search(
            r"\b(10|[0-9])\s*(?:/|out of)\s*10\b", normalized)

        if severity_match:
            fields["severity"] = int(severity_match.group(1))

        onset_match = re.search(
            r"\b(\d+)\s*(day|days|hour|hours|week|weeks|month|months|year|years)\b",
            normalized,
        )

        if onset_match:
            fields["onset"] = f"{onset_match.group(1)} {onset_match.group(2)}"

        if not known_fields.get("chief_complaint") and topic_value:
            fields["chief_complaint"] = topic_value.replace("_", " ")

        negative_patterns = {
            "nausea_vomiting": ("no nausea", "no vomiting", "not nauseous", "no nausea or vomiting"),
            "breathing_difficulty": ("no breathing difficulty", "no shortness of breath", "breathing is normal"),
            "cough": ("no cough",),
            "wheeze": ("no wheezing", "no wheeze"),
            "urinary_burning": ("no burning while urinating", "no burning during urination"),
            "urinary_blood": ("no blood in urine",),
            "vision_or_neuro": ("no numbness", "no weakness", "no vision changes"),
        }

        negatives = [
            field
            for field, phrases in negative_patterns.items()
            if any(phrase in normalized for phrase in phrases)
        ]

        return InterviewExtraction(topic=topic_value, fields=fields, negatives=negatives)
