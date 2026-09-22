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

    async def extract(
        self,
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
        current_field: str | None = None,
        current_question: str | None = None,
    ) -> InterviewExtraction:
        if not patient_text.strip():
            return InterviewExtraction()

        normalized_topic_value = normalize_topic(topic)

        if not self.enabled or self.provider != "lemonade":
            return self._fallback(
                patient_text=patient_text,
                known_fields=known_fields,
                topic=normalized_topic_value,
            )

        try:
            extraction = await self._call_lemonade(
                patient_text=patient_text,
                known_fields=known_fields,
                topic=normalized_topic_value,
                current_field=current_field,
                current_question=current_question,
            )

            extraction = self._sanitize(extraction)

            # When a topic is already established, never allow an incidental
            # symptom mentioned in the answer to change the interview topic.
            if normalized_topic_value:
                extraction = InterviewExtraction(
                    topic=normalized_topic_value,
                    fields=extraction.fields,
                    negatives=extraction.negatives,
                )

            extraction = self._enrich_obvious_facts(
                extraction=extraction,
                patient_text=patient_text,
            )

            return extraction

        except Exception:
            # Never let an LLM/provider failure trap the patient.
            return self._fallback(
                patient_text=patient_text,
                known_fields=known_fields,
                topic=normalized_topic_value,
            )

    async def _call_lemonade(
        self,
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
        current_field: str | None,
        current_question: str | None,
    ) -> InterviewExtraction:
        system_prompt = (
            "Extract clinical facts from only the latest patient answer. "
            "Return exactly one JSON object with keys topic, fields, negatives. "
            "Do not explain anything. Do not repeat the patient sentence. "
            "Extract every useful explicit fact, including multiple facts from one answer. "
            "The current question tells you what the patient is answering, but do not "
            "ignore other explicit clinical facts in the same answer. "
            "For example, if asked when the problem started and the patient says "
            "\"It started yesterday, feels like burning, and lying down makes it better\", "
            "extract onset, character, and relieving_factors. "
            "Keep every value concise. "
            "Use numeric severity for 0-10 pain scores. "
            "Use booleans for explicit yes/no facts when appropriate. "
            "Put explicitly denied facts in negatives. "
            "Never infer a negative from silence. "
            "Never invent a fact that the patient did not state. "
            "When a topic is already provided, do not change it merely because "
            "another symptom is mentioned in the answer, especially when that "
            "symptom is explicitly denied. "
            "Use only these field names: chief_complaint,onset,site,severity,character,"
            "timing,aggravating_factors,relieving_factors,radiation,associated_symptoms,"
            "breathing_difficulty,nausea_vomiting,vision_or_neuro,cough,wheeze,location,"
            "bowel_changes,appearance,itch_or_pain,spread,urinary_frequency,urinary_burning,"
            "urinary_blood,fever,fatigue,weight_change,past_medical_history,medications,allergies."
        )

        compact_known_fields = {
            key: value
            for key, value in known_fields.items()
            if key != "chief_complaint"
        }

        user_prompt = (
            f"Topic: {normalize_topic(topic)}\n"
            f"Current field: {current_field or 'unknown'}\n"
            f"Current question: {current_question or 'unknown'}\n"
            f"Known: {json.dumps(compact_known_fields, ensure_ascii=False, separators=(',', ':'))}\n"
            f"Answer: {patient_text.strip()}"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": 128,
            "enable_thinking": False,
        }

        if settings.lemonade_json_mode:
            payload["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(
            connect=5.0,
            read=self.timeout,
            write=5.0,
            pool=5.0,
        )

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
                str(part.get("text", "")) if isinstance(part, dict) else str(part)
                for part in content
            )

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Lemonade returned empty model content")

        parsed = self._parse_json(content)
        normalized = self._normalize_payload(parsed)

        return InterviewExtraction.model_validate(normalized)

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        cleaned = content.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

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
    def _sanitize(
        extraction: InterviewExtraction,
    ) -> InterviewExtraction:
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

        return InterviewExtraction(
            topic=topic,
            fields=fields,
            negatives=negatives,
        )

    @staticmethod
    def _enrich_obvious_facts(
        extraction: InterviewExtraction,
        patient_text: str,
    ) -> InterviewExtraction:
        """
        Add or correct high-confidence facts explicitly stated by the patient.

        The deterministic layer is intentionally conservative and only changes
        fields when the wording provides a strong direct signal.
        """
        text = patient_text.strip()
        normalized = re.sub(r"[,.!?।]+", "", text.lower())

        fields = dict(extraction.fields)
        negatives = list(extraction.negatives)
        topic = extraction.topic

        # ---------------------------------------------------------
        # ONSET
        # ---------------------------------------------------------

        onset_patterns = [
            (
                r"\bstarted\s+(?:after|around|before)\s+(.+?\b(?:yesterday|today|"
                r"this morning|this afternoon|this evening|last night))\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\bstarted\s+(.+?\b(?:yesterday|today|this morning|"
                r"this afternoon|this evening|last night))\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\b(?:started|began)\s+(yesterday|today|this morning|"
                r"this afternoon|this evening|last night)\b",
                lambda match: match.group(1).strip(),
            ),
        ]

        if "onset" not in fields:
            for pattern, formatter in onset_patterns:
                match = re.search(pattern, normalized)

                if match:
                    fields["onset"] = formatter(match)
                    break

        if "onset" not in fields:
            duration_match = re.search(
                r"\b(\d+)\s*(day|days|hour|hours|week|weeks|month|months|"
                r"year|years|दिन|दिनों|घंटा|घंटे|घंटों|हफ्ता|हफ्ते|हफ्तों|"
                r"सप्ताह|सप्ताहों|महीना|महीने|महीनों|साल)\b",
                normalized,
            )

            if duration_match:
                fields["onset"] = (
                    f"{duration_match.group(1)} "
                    f"{duration_match.group(2)}"
                )

        # ---------------------------------------------------------
        # CHARACTER
        # ---------------------------------------------------------

        character_patterns = (
            ("burning", ("burning sensation", "burning", "जलन")),
            ("pressure", ("pressure", "दबाव")),
            ("squeezing", ("squeezing", "सिकुड़ने जैसा")),
            ("stabbing", ("stabbing", "stab-like", "चुभने", "चुभता")),
            ("throbbing", ("throbbing", "धड़कता")),
            ("sharp", ("sharp", "तेज")),
            ("dull", ("dull", "हल्का दर्द")),
            ("aching", ("aching", "दर्द")),
        )

        if "character" not in fields:
            for value, phrases in character_patterns:
                if any(phrase in normalized for phrase in phrases):
                    fields["character"] = value
                    break

        # ---------------------------------------------------------
        # RELIEVING FACTORS
        # ---------------------------------------------------------

        relieving_patterns = (
            (
                r"\blying down\b.*\b(?:makes|made|is|was)\b.*\bbetter\b",
                "lying down",
            ),
            (
                r"\bbetter\b.*\bwhen i lie down\b",
                "lying down",
            ),
            (
                r"\bbetter when lying down\b",
                "lying down",
            ),
            (
                r"\bimproves when lying down\b",
                "lying down",
            ),
            (
                r"\bgets better when i lie down\b",
                "lying down",
            ),
            (
                r"\beases when i lie down\b",
                "lying down",
            ),
            (
                r"\bbetter after lying down\b",
                "lying down",
            ),
        )

        for pattern, value in relieving_patterns:
            if re.search(pattern, normalized):
                fields["relieving_factors"] = value
                break

        # ---------------------------------------------------------
        # AGGRAVATING FACTORS
        # ---------------------------------------------------------

        aggravating_patterns = (
            (
                r"\b(.{1,120}?)\s+(?:makes|make|made)\s+"
                r"(?:it\s+|the\s+pain\s+)?worse\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\b(.{1,120}?)\s+(?:worsens|worsen)\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\bworse when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bworsens when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bgets worse when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bworse with\b(.{1,80})",
                lambda match: f"with {match.group(1).strip()}",
            ),
            (
                r"\bgets worse with\b(.{1,80})",
                lambda match: f"with {match.group(1).strip()}",
            ),
        )

        for pattern, formatter in aggravating_patterns:
            match = re.search(pattern, normalized)

            if not match:
                continue

            detail = formatter(match).strip()

            parts = re.split(
                r"\s+\b(?:and|but)\b\s+",
                detail,
            )

            detail = parts[-1].strip()

            detail = re.sub(
                r"^(?:it|this|the pain)\s+"
                r"(?:feels like|seems like|is|was)\s+",
                "",
                detail,
            ).strip()

            if detail:
                fields["aggravating_factors"] = detail
                break

        # ---------------------------------------------------------
        # TIMING
        # ---------------------------------------------------------

        if "timing" not in fields:
            if re.search(
                r"\b(constant|all the time|nonstop|continuous)\b",
                normalized,
            ):
                fields["timing"] = "constant"
            elif re.search(
                r"\b(comes and goes|on and off|intermittent|sometimes)\b",
                normalized,
            ):
                fields["timing"] = "comes and goes"

        # ---------------------------------------------------------
        # SEVERITY
        # ---------------------------------------------------------

        if "severity" not in fields:
            severity_match = re.search(
                r"\b(10|[0-9])\s*(?:/|out of|में से)\s*10\b",
                normalized,
            )

            if severity_match:
                fields["severity"] = int(severity_match.group(1))

        # ---------------------------------------------------------
        # EXPLICIT NEGATIVES
        # ---------------------------------------------------------

        negative_patterns = {
            "nausea_vomiting": (
                "no nausea",
                "no vomiting",
                "not nauseous",
                "no nausea or vomiting",
                "i don't have nausea",
                "i don't have vomiting",
                "i do not have nausea",
                "i do not have vomiting",
                "मतली नहीं",
                "उल्टी नहीं",
                "मतली या उल्टी नहीं",
            ),
            "breathing_difficulty": (
                "no breathing difficulty",
                "no difficulty breathing",
                "no trouble breathing",
                "no trouble with breathing",
                "no shortness of breath",
                "i don't have trouble breathing",
                "i don't have any trouble breathing",
                "i do not have trouble breathing",
                "i do not have any trouble breathing",
                "i'm not having trouble breathing",
                "i am not having trouble breathing",
                "i'm breathing normally",
                "i am breathing normally",
                "breathing is normal",
                "सांस लेने में दिक्कत नहीं",
                "साँस लेने में दिक्कत नहीं",
                "सांस की कोई दिक्कत नहीं",
                "साँस की कोई दिक्कत नहीं",
                "सांस सामान्य है",
                "साँस सामान्य है",
            ),
            "cough": (
                "no cough",
                "i don't have a cough",
                "i do not have a cough",
                "खांसी नहीं",
                "खाँसी नहीं",
            ),
            "wheeze": (
                "no wheezing",
                "no wheeze",
                "i don't have wheezing",
                "i do not have wheezing",
                "घरघराहट नहीं",
                "सीटी जैसी आवाज नहीं",
                "सीटी जैसी आवाज़ नहीं",
            ),
            "urinary_burning": (
                "no burning while urinating",
                "no burning during urination",
                "i don't have burning while urinating",
                "i do not have burning while urinating",
                "पेशाब में जलन नहीं",
                "पेशाब करते समय जलन नहीं",
            ),
            "urinary_blood": (
                "no blood in urine",
                "i don't have blood in my urine",
                "i do not have blood in my urine",
                "पेशाब में खून नहीं",
                "पेशाब में रक्त नहीं",
            ),
            "vision_or_neuro": (
                "no numbness",
                "no weakness",
                "no vision changes",
                "i don't have numbness",
                "i don't have weakness",
                "सुन्नपन नहीं",
                "कमजोरी नहीं",
                "कमज़ोरी नहीं",
                "दृष्टि में बदलाव नहीं",
                "नजर में बदलाव नहीं",
                "नज़र में बदलाव नहीं",
            ),
        }

        for field, phrases in negative_patterns.items():
            if any(phrase in normalized for phrase in phrases):
                if field not in negatives:
                    negatives.append(field)

                fields.pop(field, None)

        # ---------------------------------------------------------
        # TOPIC
        # ---------------------------------------------------------

        # Only infer a new topic when the controller did not already establish
        # one. This prevents phrases such as "no nausea" from hijacking a
        # chest-pain interview into a gastrointestinal interview.
        if topic is None:
            topic_keywords = {
                "headache": (
                    "headache",
                    "head pain",
                    "migraine",
                    "सिरदर्द",
                    "सिर में दर्द",
                    "माइग्रेन",
                ),
                "chest_pain": (
                    "chest pain",
                    "chest pressure",
                    "chest discomfort",
                    "सीने में दर्द",
                    "सीने में दबाव",
                    "सीने में तकलीफ",
                    "सीने में तकलीफ़",
                ),
                "respiratory": (
                    "cough",
                    "breathless",
                    "shortness of breath",
                    "breathing problem",
                    "खांसी",
                    "खाँसी",
                    "सांस फूलना",
                    "साँस फूलना",
                    "सांस लेने में दिक्कत",
                    "साँस लेने में दिक्कत",
                ),
                "gastrointestinal": (
                    "stomach",
                    "abdomen",
                    "abdominal",
                    "diarrhea",
                    "vomiting",
                    "nausea",
                    "पेट",
                    "पेट में दर्द",
                    "दस्त",
                    "उल्टी",
                    "मतली",
                ),
                "skin": (
                    "rash",
                    "itching",
                    "skin",
                    "दाने",
                    "चकत्ते",
                    "खुजली",
                    "त्वचा",
                ),
                "urinary": (
                    "urine",
                    "urination",
                    "burning while urinating",
                    "पेशाब",
                    "मूत्र",
                    "पेशाब में जलन",
                    "पेशाब करते समय जलन",
                ),
            }

            for candidate, keywords in topic_keywords.items():
                if any(keyword in normalized for keyword in keywords):
                    topic = candidate
                    break

        return InterviewExtraction(
            topic=topic,
            fields=fields,
            negatives=negatives,
        )

    @classmethod
    def _fallback(
        cls,
        patient_text: str,
        known_fields: dict[str, Any],
        topic: str | None,
    ) -> InterviewExtraction:
        text = patient_text.strip()
        normalized = re.sub(r"[,.!?।]+", "", text.lower())

        fields: dict[str, Any] = {}
        topic_value = normalize_topic(topic)

        # ---------------------------------------------------------
        # TOPIC
        # ---------------------------------------------------------

        if topic_value is None:
            topic_keywords = {
                "headache": (
                    "headache",
                    "head pain",
                    "migraine",
                    "सिरदर्द",
                    "सिर में दर्द",
                    "माइग्रेन",
                ),
                "chest_pain": (
                    "chest pain",
                    "chest pressure",
                    "chest discomfort",
                    "सीने में दर्द",
                    "सीने में दबाव",
                    "सीने में तकलीफ",
                    "सीने में तकलीफ़",
                ),
                "respiratory": (
                    "cough",
                    "breathless",
                    "shortness of breath",
                    "breathing problem",
                    "खांसी",
                    "खाँसी",
                    "सांस फूलना",
                    "साँस फूलना",
                    "सांस लेने में दिक्कत",
                    "साँस लेने में दिक्कत",
                ),
                "gastrointestinal": (
                    "stomach",
                    "abdomen",
                    "abdominal",
                    "diarrhea",
                    "vomiting",
                    "nausea",
                    "पेट",
                    "पेट में दर्द",
                    "दस्त",
                    "उल्टी",
                    "मतली",
                ),
                "skin": (
                    "rash",
                    "itching",
                    "skin",
                    "दाने",
                    "चकत्ते",
                    "खुजली",
                    "त्वचा",
                ),
                "urinary": (
                    "urine",
                    "urination",
                    "burning while urinating",
                    "पेशाब",
                    "मूत्र",
                    "पेशाब में जलन",
                    "पेशाब करते समय जलन",
                ),
            }

            for candidate, keywords in topic_keywords.items():
                if any(keyword in normalized for keyword in keywords):
                    topic_value = candidate
                    break

        # ---------------------------------------------------------
        # SEVERITY
        # ---------------------------------------------------------

        severity_match = re.search(
            r"\b(10|[0-9])\s*(?:/|out of|में से)\s*10\b",
            normalized,
        )

        if severity_match:
            fields["severity"] = int(severity_match.group(1))

        # ---------------------------------------------------------
        # ONSET
        # ---------------------------------------------------------

        onset_patterns = [
            (
                r"\bstarted\s+(?:after|around|before)\s+(.+?\b(?:yesterday|today|"
                r"this morning|this afternoon|this evening|last night))\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\bstarted\s+(.+?\b(?:yesterday|today|this morning|"
                r"this afternoon|this evening|last night))\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\b(?:started|began)\s+(yesterday|today|this morning|"
                r"this afternoon|this evening|last night)\b",
                lambda match: match.group(1).strip(),
            ),
        ]

        for pattern, formatter in onset_patterns:
            match = re.search(pattern, normalized)

            if match:
                fields["onset"] = formatter(match)
                break

        if "onset" not in fields:
            onset_match = re.search(
                r"\b(\d+)\s*(day|days|hour|hours|week|weeks|month|months|year|years|"
                r"दिन|दिनों|घंटा|घंटे|घंटों|हफ्ता|हफ्ते|हफ्तों|सप्ताह|सप्ताहों|"
                r"महीना|महीने|महीनों|साल)\b",
                normalized,
            )

            if onset_match:
                fields["onset"] = (
                    f"{onset_match.group(1)} {onset_match.group(2)}"
                )

        # ---------------------------------------------------------
        # CHARACTER
        # ---------------------------------------------------------

        character_patterns = (
            ("burning", ("burning sensation", "burning", "जलन")),
            ("pressure", ("pressure", "दबाव")),
            ("squeezing", ("squeezing", "सिकुड़ने जैसा")),
            ("stabbing", ("stabbing", "stab-like", "चुभने", "चुभता")),
            ("throbbing", ("throbbing", "धड़कता")),
            ("sharp", ("sharp", "तेज")),
            ("dull", ("dull", "हल्का दर्द")),
            ("aching", ("aching", "दर्द")),
        )

        for value, phrases in character_patterns:
            if any(phrase in normalized for phrase in phrases):
                fields["character"] = value
                break

        # ---------------------------------------------------------
        # RELIEVING FACTORS
        # ---------------------------------------------------------

        relieving_patterns = (
            (
                r"\blying down\b.*\b(?:makes|made|is|was)\b.*\bbetter\b",
                "lying down",
            ),
            (
                r"\bbetter\b.*\bwhen i lie down\b",
                "lying down",
            ),
            (
                r"\bbetter when lying down\b",
                "lying down",
            ),
            (
                r"\bimproves when lying down\b",
                "lying down",
            ),
            (
                r"\bgets better when i lie down\b",
                "lying down",
            ),
            (
                r"\beases when i lie down\b",
                "lying down",
            ),
            (
                r"\bbetter after lying down\b",
                "lying down",
            ),
        )

        for pattern, value in relieving_patterns:
            if re.search(pattern, normalized):
                fields["relieving_factors"] = value
                break

        # ---------------------------------------------------------
        # AGGRAVATING FACTORS
        # ---------------------------------------------------------

        aggravating_patterns = (
            (
                r"\b(.{1,120}?)\s+(?:makes|make|made)\s+"
                r"(?:it\s+|the\s+pain\s+)?worse\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\b(.{1,120}?)\s+(?:worsens|worsen)\b",
                lambda match: match.group(1).strip(),
            ),
            (
                r"\bworse when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bworsens when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bgets worse when\b(.{1,80})",
                lambda match: f"when {match.group(1).strip()}",
            ),
            (
                r"\bworse with\b(.{1,80})",
                lambda match: f"with {match.group(1).strip()}",
            ),
            (
                r"\bgets worse with\b(.{1,80})",
                lambda match: f"with {match.group(1).strip()}",
            ),
        )

        for pattern, formatter in aggravating_patterns:
            match = re.search(pattern, normalized)

            if not match:
                continue

            detail = formatter(match).strip()

            parts = re.split(
                r"\s+\b(?:and|but)\b\s+",
                detail,
            )

            detail = parts[-1].strip()

            detail = re.sub(
                r"^(?:it|this|the pain)\s+"
                r"(?:feels like|seems like|is|was)\s+",
                "",
                detail,
            ).strip()

            if detail:
                fields["aggravating_factors"] = detail
                break

        # ---------------------------------------------------------
        # TIMING
        # ---------------------------------------------------------

        if re.search(
            r"\b(constant|all the time|nonstop|continuous)\b",
            normalized,
        ):
            fields["timing"] = "constant"
        elif re.search(
            r"\b(comes and goes|on and off|intermittent|sometimes)\b",
            normalized,
        ):
            fields["timing"] = "comes and goes"

        # ---------------------------------------------------------
        # CHIEF COMPLAINT
        # ---------------------------------------------------------

        if not known_fields.get("chief_complaint") and topic_value:
            fields["chief_complaint"] = topic_value.replace("_", " ")

        # ---------------------------------------------------------
        # NEGATIVES
        # ---------------------------------------------------------

        negative_patterns = {
            "nausea_vomiting": (
                "no nausea",
                "no vomiting",
                "not nauseous",
                "no nausea or vomiting",
                "i don't have nausea",
                "i don't have vomiting",
                "i do not have nausea",
                "i do not have vomiting",
                "मतली नहीं",
                "उल्टी नहीं",
                "मतली या उल्टी नहीं",
            ),
            "breathing_difficulty": (
                "no breathing difficulty",
                "no difficulty breathing",
                "no trouble breathing",
                "no trouble with breathing",
                "no shortness of breath",
                "i don't have trouble breathing",
                "i don't have any trouble breathing",
                "i do not have trouble breathing",
                "i do not have any trouble breathing",
                "i'm not having trouble breathing",
                "i am not having trouble breathing",
                "i'm breathing normally",
                "i am breathing normally",
                "breathing is normal",
                "सांस लेने में दिक्कत नहीं",
                "साँस लेने में दिक्कत नहीं",
                "सांस की कोई दिक्कत नहीं",
                "साँस की कोई दिक्कत नहीं",
                "सांस सामान्य है",
                "साँस सामान्य है",
            ),
            "cough": (
                "no cough",
                "i don't have a cough",
                "i do not have a cough",
                "खांसी नहीं",
                "खाँसी नहीं",
            ),
            "wheeze": (
                "no wheezing",
                "no wheeze",
                "i don't have wheezing",
                "i do not have wheezing",
                "घरघराहट नहीं",
                "सीटी जैसी आवाज नहीं",
                "सीटी जैसी आवाज़ नहीं",
            ),
            "urinary_burning": (
                "no burning while urinating",
                "no burning during urination",
                "i don't have burning while urinating",
                "i do not have burning while urinating",
                "पेशाब में जलन नहीं",
                "पेशाब करते समय जलन नहीं",
            ),
            "urinary_blood": (
                "no blood in urine",
                "i don't have blood in my urine",
                "i do not have blood in my urine",
                "पेशाब में खून नहीं",
                "पेशाब में रक्त नहीं",
            ),
            "vision_or_neuro": (
                "no numbness",
                "no weakness",
                "no vision changes",
                "i don't have numbness",
                "i don't have weakness",
                "सुन्नपन नहीं",
                "कमजोरी नहीं",
                "कमज़ोरी नहीं",
                "दृष्टि में बदलाव नहीं",
                "नजर में बदलाव नहीं",
                "नज़र में बदलाव नहीं",
            ),
        }

        negatives: list[str] = []

        for field, phrases in negative_patterns.items():
            if any(phrase in normalized for phrase in phrases):
                negatives.append(field)
                fields.pop(field, None)

        return InterviewExtraction(
            topic=topic_value,
            fields=fields,
            negatives=negatives,
        )