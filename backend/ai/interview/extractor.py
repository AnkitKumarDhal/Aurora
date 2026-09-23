from __future__ import annotations

import ast
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from backend.ai.interview.state import (
    InterviewState,
    REQUIRED_SECTIONS,
    SECTION_ORDER,
    normalize_field_name,
    normalize_section,
)
from backend.config import settings


logger = logging.getLogger("aurora.interview")


TOPIC_KEYWORDS = {
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
        "difficulty breathing",
        "breathing problem",
        "खांसी",
        "खाँसी",
        "सांस फूलना",
        "साँस फूलना",
    ),
    "gastrointestinal": (
        "constipation",
        "constipated",
        "hard stool",
        "hard stools",
        "diarrhea",
        "loose stools",
        "loose motions",
        "stomach pain",
        "abdominal pain",
        "abdomen",
        "vomiting",
        "nausea",
        "कब्ज",
        "दस्त",
        "पेट में दर्द",
        "उल्टी",
        "मतली",
    ),
    "skin": (
        "rash",
        "itching",
        "skin problem",
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
        "painful urination",
        "पेशाब",
        "मूत्र",
        "पेशाब में जलन",
    ),
    "musculoskeletal": (
        "back pain",
        "joint pain",
        "muscle pain",
        "neck pain",
        "कमर दर्द",
        "जोड़ों का दर्द",
    ),
    "neurological": (
        "numbness",
        "tingling",
        "weakness",
        "सुन्नपन",
        "झनझनाहट",
        "कमजोरी",
        "कमज़ोरी",
    ),
}

COMPLAINT_PATTERNS = (
    ("constipation", ("constipation", "constipated", "hard stools", "कब्ज")),
    ("diarrhea", ("diarrhea", "loose stools", "loose motions", "दस्त")),
    ("headache", ("headache", "head pain", "migraine", "सिरदर्द")),
    (
        "chest pain",
        (
            "chest pain",
            "chest pressure",
            "chest discomfort",
            "सीने में दर्द",
        ),
    ),
    ("cough", ("cough", "खांसी", "खाँसी")),
    (
        "breathing difficulty",
        (
            "shortness of breath",
            "breathless",
            "difficulty breathing",
        ),
    ),
    (
        "abdominal pain",
        (
            "stomach pain",
            "abdominal pain",
            "पेट में दर्द",
        ),
    ),
    ("vomiting", ("vomiting", "उल्टी")),
    ("nausea", ("nausea", "मतली")),
    ("rash", ("rash", "दाने", "चकत्ते")),
    ("itching", ("itching", "खुजली")),
    (
        "urinary problem",
        (
            "urine",
            "urination",
            "painful urination",
            "पेशाब",
        ),
    ),
    ("back pain", ("back pain", "कमर दर्द")),
    ("joint pain", ("joint pain", "जोड़ों का दर्द")),
)

FALLBACK_QUESTIONS = {
    "en": {
        "hpi": "What else about this problem would be important for the doctor to know?",
        "past_history": "Have you ever had any important medical condition or major surgery?",
        "drug_allergy": "Are you taking any regular medicines or supplements?",
        "family_history": "Is there any important medical condition in your family?",
        "personal_history": "Is there anything important about your daily life, such as your work, diet, sleep, tobacco, smoking, alcohol, or activity?",
        "review_of_systems": "Apart from the main problem, have you noticed any other symptoms or changes in your health?",
        "ayush": "Is there any relevant AYUSH or traditional-medicine information you would like to share?",
    },
    "hi": {
        "hpi": "इस समस्या के बारे में डॉक्टर के लिए और कौन सी महत्वपूर्ण बात जानना उपयोगी होगी?",
        "past_history": "क्या आपको पहले कोई महत्वपूर्ण बीमारी रही है या कोई बड़ी सर्जरी हुई है?",
        "drug_allergy": "क्या आप कोई नियमित दवा या सप्लीमेंट लेते हैं?",
        "family_history": "क्या आपके परिवार में कोई महत्वपूर्ण बीमारी रही है?",
        "personal_history": "आपके दैनिक जीवन में काम, भोजन, नींद, तंबाकू, धूम्रपान, शराब या शारीरिक गतिविधि से जुड़ी कोई महत्वपूर्ण बात है?",
        "review_of_systems": "मुख्य समस्या के अलावा क्या आपने कोई अन्य लक्षण या अपने स्वास्थ्य में कोई और बदलाव देखा है?",
        "ayush": "क्या आपके स्वास्थ्य से जुड़ी कोई महत्वपूर्ण आयुष या पारंपरिक चिकित्सा जानकारी है?",
    },
}


@dataclass
class InterviewPlan:
    topic: str | None = None
    section: str = "hpi"
    completed_sections: list[str] | None = None
    facts: list[dict[str, Any]] | None = None
    next_question: str | None = None
    completed: bool = False
    ai_used: bool = False

    def __post_init__(self) -> None:
        if self.completed_sections is None:
            self.completed_sections = []

        if self.facts is None:
            self.facts = []


class InterviewExtractor:
    def __init__(self) -> None:
        self.url = settings.lemonade_url
        self.model = settings.lemonade_model
        self.timeout = settings.lemonade_timeout
        self.enabled = settings.interview_ai_enabled
        self.provider = settings.interview_ai_provider

    async def plan(
        self,
        patient_text: str,
        state: InterviewState,
        conversation: list[dict[str, Any]],
        language: str | None,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> InterviewPlan:
        self._debug(
            "PLAN_START",
            session_id=session_id,
            turn_id=turn_id,
            topic=state.topic,
            section=state.current_section,
            completed_sections=sorted(state.completed_sections),
            known_fields=state.known_fields(),
            patient_text=patient_text,
            conversation_turns=len(conversation),
        )

        deterministic = self._deterministic_facts(
            patient_text=patient_text,
            current_section=state.current_section,
            current_question=(
                state.question_history[-1]
                if state.question_history
                else None
            ),
        )

        if not self.enabled or self.provider != "lemonade":
            plan = self.deterministic_fallback(
                patient_text=patient_text,
                state=state,
                language=language,
            )

            self._debug(
                "FALLBACK_PROVIDER_DISABLED",
                session_id=session_id,
                turn_id=turn_id,
                plan=self.plan_dict(plan),
            )

            return plan

        try:
            raw = await self._call_lemonade(
                patient_text=patient_text,
                state=state,
                conversation=conversation,
                language=language,
                session_id=session_id,
                turn_id=turn_id,
            )

            plan = self._sanitize_plan(
                raw,
                current_section=state.current_section,
                language=language,
            )

            plan.facts = self._merge_fact_lists(
                plan.facts,
                deterministic,
            )

            if not plan.topic:
                plan.topic = self._detect_topic(
                    patient_text
                )

            plan.ai_used = True

            if (
                not plan.next_question
                and not plan.completed
            ):
                plan.next_question = self._fallback_question(
                    state=state,
                    section=plan.section,
                    language=language,
                )

            self._debug(
                "PLAN_READY",
                session_id=session_id,
                turn_id=turn_id,
                plan=self.plan_dict(plan),
            )

            return plan

        except Exception as exc:
            self._debug(
                "PLAN_FAILURE",
                session_id=session_id,
                turn_id=turn_id,
                error_type=type(exc).__name__,
                error=str(exc),
            )

            plan = self.deterministic_fallback(
                patient_text=patient_text,
                state=state,
                language=language,
            )

            self._debug(
                "FALLBACK_AFTER_FAILURE",
                session_id=session_id,
                turn_id=turn_id,
                plan=self.plan_dict(plan),
            )

            return plan

    async def _call_lemonade(
        self,
        patient_text: str,
        state: InterviewState,
        conversation: list[dict[str, Any]],
        language: str | None,
        session_id: str | None,
        turn_id: str | None,
    ) -> dict[str, Any]:
        recent_conversation = conversation[-12:]

        user_prompt = (
            f"Language: {language or 'en'}\n"
            f"Current topic: {state.topic}\n"
            f"Current section: {state.current_section}\n"
            f"Completed sections: {json.dumps(
                sorted(state.completed_sections), ensure_ascii=False)}\n"
            f"Current known history: {json.dumps(
                state.section_summary(), ensure_ascii=False, default=str)}\n"
            f"Recent questions: {json.dumps(
                state.question_history[-8:], ensure_ascii=False)}\n"
            f"Recent conversation: {json.dumps(
                recent_conversation, ensure_ascii=False, default=str)}\n"
            f"Latest patient answer: {patient_text.strip()}"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0,
            "max_tokens": 384,
            "enable_thinking": False,
        }

        if settings.lemonade_json_mode:
            payload["response_format"] = {
                "type": "json_object",
            }

        self._debug(
            "LLM_REQUEST",
            session_id=session_id,
            turn_id=turn_id,
            model=self.model,
            url=self.url,
            section=state.current_section,
            prompt_tokens_estimate=len(user_prompt.split()),
            user_prompt=user_prompt,
        )

        started = time.monotonic()

        timeout = httpx.Timeout(
            connect=5.0,
            read=self.timeout,
            write=5.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:
            response = await client.post(
                self.url,
                json=payload,
            )

            if (
                response.status_code in {400, 404, 422}
                and "response_format" in payload
            ):
                retry_payload = dict(payload)
                retry_payload.pop(
                    "response_format",
                    None,
                )

                self._debug(
                    "LLM_JSON_MODE_RETRY",
                    session_id=session_id,
                    turn_id=turn_id,
                    status=response.status_code,
                    body=response.text[:4000],
                )

                response = await client.post(
                    self.url,
                    json=retry_payload,
                )

        elapsed_ms = round(
            (time.monotonic() - started) * 1000,
            2,
        )

        self._debug(
            "LLM_HTTP_RESPONSE",
            session_id=session_id,
            turn_id=turn_id,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
            body=response.text[:12000],
        )

        response.raise_for_status()

        body = response.json()

        choices = body.get("choices")

        if not isinstance(choices, list) or not choices:
            raise ValueError(
                "Lemonade returned no choices"
            )

        message = choices[0].get("message", {})

        content = (
            message.get("content")
            if isinstance(message, dict)
            else None
        )

        if isinstance(content, list):
            content = "".join(
                str(item.get("text", ""))
                if isinstance(item, dict)
                else str(item)
                for item in content
            )

        self._debug(
            "LLM_CONTENT_RAW",
            session_id=session_id,
            turn_id=turn_id,
            content=content,
            content_type=type(content).__name__,
        )

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "Lemonade returned empty assistant content"
            )

        return self._parse_model_response(
            content,
            session_id=session_id,
            turn_id=turn_id,
        )

    def _parse_model_response(
        self,
        content: str,
        session_id: str | None,
        turn_id: str | None,
    ) -> dict[str, Any]:
        cleaned = self._clean_json(content)

        try:
            result = json.loads(cleaned)

            if isinstance(result, dict):
                self._debug(
                    "JSON_PARSE_SUCCESS",
                    session_id=session_id,
                    turn_id=turn_id,
                    parser="json",
                )

                return result

        except json.JSONDecodeError as exc:
            self._debug(
                "JSON_PARSE_FAILED",
                session_id=session_id,
                turn_id=turn_id,
                parser="json",
                error=str(exc),
                content=cleaned,
            )

        repaired = self._repair_json(cleaned)

        try:
            result = json.loads(repaired)

            if isinstance(result, dict):
                self._debug(
                    "JSON_PARSE_SUCCESS",
                    session_id=session_id,
                    turn_id=turn_id,
                    parser="repaired_json",
                )

                return result

        except json.JSONDecodeError as exc:
            self._debug(
                "REPAIRED_JSON_FAILED",
                session_id=session_id,
                turn_id=turn_id,
                error=str(exc),
                content=repaired,
            )

        python_like = self._pythonize(repaired)

        try:
            result = ast.literal_eval(
                python_like
            )

            if isinstance(result, dict):
                self._debug(
                    "JSON_PARSE_SUCCESS",
                    session_id=session_id,
                    turn_id=turn_id,
                    parser="python_literal",
                )

                return result

        except Exception as exc:
            self._debug(
                "PYTHON_LITERAL_FAILED",
                session_id=session_id,
                turn_id=turn_id,
                error_type=type(exc).__name__,
                error=str(exc),
                content=python_like,
            )

        raise ValueError(
            "Lemonade returned malformed structured output"
        )

    def deterministic_fallback(
        self,
        patient_text: str,
        state: InterviewState,
        language: str | None,
    ) -> InterviewPlan:
        facts = self._deterministic_facts(
            patient_text=patient_text,
            current_section=state.current_section,
            current_question=(
                state.question_history[-1]
                if state.question_history
                else None
            ),
        )

        topic = (
            self._detect_topic(patient_text)
            or state.topic
        )

        normalized = self._normalize_text(
            patient_text
        )

        explicit_stop = normalized in {
            "nothing",
            "nothing else",
            "nothing more",
            "nothing really",
            "none",
            "no more",
            "no",
            "not applicable",
            "not relevant",
            "i don't know",
            "i do not know",
            "नहीं",
            "कुछ नहीं",
            "और कुछ नहीं",
            "कोई नहीं",
            "पता नहीं",
        }

        completed_sections: list[str] = []

        if explicit_stop:
            facts.extend(
                self._negative_facts_for_question(
                    state.current_section,
                    state.question_history[-1]
                    if state.question_history
                    else None,
                )
            )

            if self._fallback_section_complete(
                state,
                facts,
            ):
                completed_sections.append(
                    state.current_section
                )

        if (
            state.current_section == "hpi"
            and self._hpi_sufficient(
                state,
                facts,
            )
            and (
                self._hpi_fallback_allows_completion(
                    state.question_history[-1]
                    if state.question_history
                    else None,
                )
                or explicit_stop
            )
        ):
            completed_sections.append(
                "hpi"
            )

        completed = (
            set(state.completed_sections)
            | set(completed_sections)
        )

        next_section = self._next_section(
            completed
        )

        section = (
            next_section
            or state.current_section
        )

        question = self._fallback_question(
            state=state,
            section=section,
            language=language,
        )

        completed = (
            completed
            | set(completed_sections)
        ) >= REQUIRED_SECTIONS

        if completed:
            question = None

        return InterviewPlan(
            topic=topic,
            section=section,
            completed_sections=completed_sections,
            facts=facts,
            next_question=question,
            completed=completed,
            ai_used=False,
        )

    def _deterministic_facts(
        self,
        patient_text: str,
        current_section: str,
        current_question: str | None,
    ) -> list[dict[str, Any]]:
        text = self._normalize_text(
            patient_text
        )

        facts: list[dict[str, Any]] = []

        def add(
            section: str,
            field: str,
            value: Any,
            negative: bool = False,
        ) -> None:
            facts.append(
                {
                    "section": section,
                    "field": field,
                    "value": value,
                    "negative": negative,
                }
            )

        topic = self._detect_topic(
            patient_text
        )

        if topic:
            add(
                "hpi",
                "chief_complaint",
                self._detect_complaint(
                    patient_text
                ) or topic.replace("_", " "),
            )

        onset_context = (
            current_section == "hpi"
            and (
                not current_question
                or any(
                    word in current_question.lower()
                    for word in (
                        "when",
                        "start",
                        "started",
                        "long",
                        "began",
                        "कब",
                        "शुरू",
                    )
                )
            )
        )

        if onset_context:
            onset = self._extract_onset(
                text
            )

            if onset:
                add(
                    "hpi",
                    "onset",
                    onset,
                )

        if current_section == "past_history":
            surgery = self._extract_surgery(
                patient_text
            )

            if surgery:
                add(
                    "past_history",
                    "past_surgical_history",
                    surgery,
                )

            medical = self._extract_medical_history(
                patient_text
            )

            if medical:
                add(
                    "past_history",
                    "past_medical_history",
                    medical,
                )

        family = self._extract_family_history(
            patient_text
        )

        if family:
            add(
                "family_history",
                "family_history",
                family,
            )

        if current_section == "drug_allergy":
            medications = self._extract_medications(
                patient_text
            )

            if medications:
                add(
                    "drug_allergy",
                    "medications",
                    medications,
                )

            allergies = self._extract_allergies(
                patient_text
            )

            if allergies:
                add(
                    "drug_allergy",
                    "allergies",
                    allergies,
                )

            if self._is_negative_answer(
                patient_text
            ):
                question = (
                    current_question or ""
                ).lower()

                if (
                    "medicine" in question
                    or "medication" in question
                    or "drug" in question
                    or "दवा" in question
                ):
                    add(
                        "drug_allergy",
                        "medications",
                        False,
                        True,
                    )

                if (
                    "allerg" in question
                    or "food" in question
                    or "एलर्जी" in question
                ):
                    add(
                        "drug_allergy",
                        "allergies",
                        False,
                        True,
                    )

        if (
            "severity" not in {
                fact["field"]
                for fact in facts
            }
        ):
            match = re.search(
                r"\b(10|[0-9])\s*(?:/|out of|में से)\s*10\b",
                text,
            )

            if match:
                add(
                    "hpi",
                    "severity",
                    int(match.group(1)),
                )

        if re.search(
            r"\b(constipation|constipated|hard stool|hard stools)\b|कब्ज",
            text,
        ):
            add(
                "hpi",
                "bowel_changes",
                "constipation",
            )

        if (
            current_section == "hpi"
            and current_question
            and (
                "bowel movement" in current_question.lower()
                or "bowel movements" in current_question.lower()
                or "मल त्याग" in current_question.lower()
                or "मल त्याग" in current_question
            )
        ):
            numeric_answer = re.search(
                r"\b([0-9]+(?:\.[0-9]+)?)\b",
                text,
            )

            if numeric_answer:
                raw_value = numeric_answer.group(1)

                value: Any = (
                    float(raw_value)
                    if "." in raw_value
                    else int(raw_value)
                )

                add(
                    "hpi",
                    "bowel_frequency",
                    value,
                )

        if re.search(
            r"\b(diarrhea|loose stools|loose motions)\b|दस्त",
            text,
        ):
            add(
                "hpi",
                "bowel_changes",
                "diarrhea",
            )

        if re.search(
            r"\b(hard stool|hard stools|hard bowel movement)\b",
            text,
        ):
            add(
                "hpi",
                "stool_consistency",
                "hard",
            )

        if re.search(
            r"\b(straining|strain to pass stool|straining to pass stool|"
            r"have to strain|need to strain)\b",
            text,
        ):
            add(
                "hpi",
                "straining",
                True,
            )

        if re.search(
            r"\b(bloating|bloated|abdominal distension|stomach bloating)\b",
            text,
        ):
            add(
                "hpi",
                "abdominal_distension",
                True,
            )

        if re.search(
            r"\b(blood in stool|blood in stools|blood while passing stool|"
            r"rectal bleeding)\b",
            text,
        ):
            add(
                "hpi",
                "blood_in_stool",
                True,
            )

        if re.search(
            r"\b(there is no blood|no blood|no blood in stool|"
            r"no blood in stools|i don't have blood in my stool)\b",
            text,
        ):
            add(
                "hpi",
                "blood_in_stool",
                False,
                True,
            )

        if (
            "very often" in text
            or "very frequently" in text
            or "frequently" in text
            or "often" in text
            or "rarely" in text
            or "seldom" in text
        ):
            match = re.search(
                r"\b(very often|very frequently|frequently|often|rarely|seldom)\b",
                text,
            )

            if match:
                add(
                    "hpi",
                    "bowel_frequency",
                    match.group(1),
                )

        numeric_frequency = re.search(
            r"\b\d+\s*(?:times?|bowel movements?)\s*"
            r"(?:a|per)\s*(?:day|week|month)\b",
            text,
        )

        if numeric_frequency:
            add(
                "hpi",
                "bowel_frequency",
                numeric_frequency.group(0),
            )

        if re.search(
            r"\b(burning|burning sensation)\b|जलन",
            text,
        ):
            add(
                "hpi",
                "character",
                "burning",
            )

        if re.search(
            r"\b(sharp|stabbing)\b|चुभता|चुभने",
            text,
        ):
            add(
                "hpi",
                "character",
                "sharp",
            )

        if re.search(
            r"\b(throbbing)\b|धड़कता",
            text,
        ):
            add(
                "hpi",
                "character",
                "throbbing",
            )

        if re.search(
            r"\b(constant|all the time|nonstop|continuous)\b",
            text,
        ):
            add(
                "hpi",
                "timing",
                "constant",
            )

        if re.search(
            r"\b(comes and goes|on and off|intermittent|sometimes)\b",
            text,
        ):
            add(
                "hpi",
                "timing",
                "comes and goes",
            )

        return self._dedupe_facts(
            facts
        )

    @staticmethod
    def _extract_surgery(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        surgery_words = (
            "surgery",
            "operation",
            "operated",
            "सर्जरी",
            "ऑपरेशन",
        )

        if not any(
            word in normalized
            for word in surgery_words
        ):
            return None

        return " ".join(
            text.strip().split()
        )

    @staticmethod
    def _extract_medical_history(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        if any(
            phrase in normalized
            for phrase in (
                "diabetes",
                "hypertension",
                "blood pressure",
                "asthma",
                "thyroid",
                "heart disease",
                "kidney disease",
                "liver disease",
                "epilepsy",
                "cancer",
                "मधुमेह",
                "ब्लड प्रेशर",
                "उच्च रक्तचाप",
                "अस्थमा",
                "थायरॉइड",
            )
        ):
            return " ".join(
                text.strip().split()
            )

        return None

    @staticmethod
    def _extract_family_history(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        family_words = (
            "my father",
            "my mother",
            "my brother",
            "my sister",
            "my uncle",
            "my aunt",
            "my grandfather",
            "my grandmother",
            "father has",
            "mother has",
            "family has",
            "runs in my family",
            "family history",
            "मेरे पिता",
            "मेरी माता",
            "मेरी मां",
            "मेरी माँ",
            "मेरे भाई",
            "मेरी बहन",
            "परिवार",
        )

        if any(
            phrase in normalized
            for phrase in family_words
        ):
            return " ".join(
                text.strip().split()
            )

        return None

    @staticmethod
    def _extract_medications(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        if normalized in {
            "no",
            "none",
            "nothing",
            "not taking anything",
            "i don't take anything",
            "i do not take anything",
        }:
            return None

        medication_words = (
            "mg",
            "tablet",
            "capsule",
            "medicine",
            "medication",
            "metformin",
            "insulin",
            "amlodipine",
            "paracetamol",
            "ibuprofen",
            "दवा",
            "दवाइ",
        )

        if any(
            word in normalized
            for word in medication_words
        ):
            return " ".join(
                text.strip().split()
            )

        return None

    @staticmethod
    def _extract_allergies(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        if (
            "no allergy" in normalized
            or "no allergies" in normalized
        ):
            return None

        if (
            "allergic to" in normalized
            or "allergy to" in normalized
            or "एलर्जी" in normalized
        ):
            return " ".join(
                text.strip().split()
            )

        return None

    @staticmethod
    def _is_negative_answer(
        text: str,
    ) -> bool:
        return (
            InterviewExtractor._normalize_text(
                text
            )
            in {
                "no",
                "none",
                "nothing",
                "nothing else",
                "no more",
                "not applicable",
                "नहीं",
                "कुछ नहीं",
                "और कुछ नहीं",
            }
        )

    @staticmethod
    def _hpi_sufficient(
        state: InterviewState,
        facts: list[dict[str, Any]],
    ) -> bool:
        fields = set(
            state.known_fields()
        )

        fields.update(
            fact["field"]
            for fact in facts
            if not fact.get("negative")
        )

        if "chief_complaint" not in fields:
            return False

        relevant = {
            "onset",
            "duration",
            "course",
            "site",
            "severity",
            "character",
            "timing",
            "frequency",
            "aggravating_factors",
            "relieving_factors",
            "radiation",
            "associated_symptoms",
            "bowel_changes",
            "bowel_frequency",
            "stool_consistency",
            "straining",
            "blood_in_stool",
            "abdominal_distension",
        }

        return len(
            fields & relevant
        ) >= 4

    @staticmethod
    def _negative_facts_for_question(
        section: str,
        question: str | None,
    ) -> list[dict[str, Any]]:
        lower = (
            question or ""
        ).lower()

        facts: list[dict[str, Any]] = []

        def add(field: str) -> None:
            facts.append(
                {
                    "section": section,
                    "field": field,
                    "value": False,
                    "negative": True,
                }
            )

        if section == "past_history":
            if (
                "medical condition" in lower
                or "long-term" in lower
                or "बीमारी" in lower
            ):
                add("past_medical_history")
            elif (
                "surgery" in lower
                or "operation" in lower
                or "सर्जरी" in lower
                or "ऑपरेशन" in lower
            ):
                add("past_surgical_history")
            elif (
                "hospital" in lower
                or "अस्पताल" in lower
            ):
                add("hospitalizations")

        elif section == "drug_allergy":
            if (
                "medicine" in lower
                or "medication" in lower
                or "drug" in lower
                or "supplement" in lower
                or "दवा" in lower
            ):
                add("medications")
            elif (
                "allerg" in lower
                or "एलर्जी" in lower
            ):
                add("allergies")

        elif section == "hpi":
            if (
                "blood" in lower
                or "खून" in lower
            ):
                add("blood_in_stool")
            elif (
                "straining" in lower
                or "जोर" in lower
            ):
                add("straining")
            elif (
                "other symptom" in lower
                or "other" in lower
            ):
                add("associated_symptoms")
            elif (
                "fever" in lower
                or "बुखार" in lower
            ):
                add("fever")

        return facts

    @staticmethod
    def _fallback_section_complete(
        state: InterviewState,
        new_facts: list[dict[str, Any]],
    ) -> bool:
        fields = state.known_fields()

        for fact in new_facts:
            fields[
                normalize_field_name(
                    fact.get("field")
                )
            ] = fact.get("value")

        if state.current_section == "past_history":
            return all(
                field in fields
                for field in (
                    "past_medical_history",
                    "past_surgical_history",
                    "hospitalizations",
                )
            )

        if state.current_section == "drug_allergy":
            return all(
                field in fields
                for field in (
                    "medications",
                    "allergies",
                )
            )

        return state.current_section in {
            "family_history",
            "personal_history",
            "review_of_systems",
        }

    @staticmethod
    def _hpi_fallback_allows_completion(
        question: str | None,
    ) -> bool:
        lower = (
            question or ""
        ).lower()

        return (
            "other" in lower
            or "anything else" in lower
            or "और" in lower
        )

    @staticmethod
    def _next_section(
        completed: set[str],
    ) -> str | None:
        for section in SECTION_ORDER:
            if section not in completed:
                return section

        return None

    @staticmethod
    def _detect_topic(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(
                keyword in normalized
                for keyword in keywords
            ):
                return topic

        return None

    @staticmethod
    def _detect_complaint(
        text: str,
    ) -> str | None:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        for complaint, phrases in COMPLAINT_PATTERNS:
            if any(
                phrase in normalized
                for phrase in phrases
            ):
                return complaint

        return None

    @staticmethod
    def _extract_onset(
        text: str,
    ) -> str | None:
        immediate = re.search(
            r"\b(?:started|began)\s+"
            r"(yesterday|today|this morning|this afternoon|"
            r"this evening|last night)\b",
            text,
        )

        if immediate:
            return immediate.group(1)

        duration = re.search(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
            r"a couple|a few)\s+"
            r"(day|days|hour|hours|week|weeks|month|months|year|years)\b",
            text,
        )

        if not duration:
            return None

        return (
            f"{duration.group(1)} "
            f"{duration.group(2)}"
        )

    @staticmethod
    def _fallback_question(
        state: InterviewState,
        section: str,
        language: str | None,
    ) -> str:
        lang = (
            "hi"
            if language == "hi"
            else "en"
        )

        known = state.known_fields()

        current_question = (
            state.question_history[-1]
            if state.question_history
            else ""
        ).lower()

        if section == "past_history":
            if "past_medical_history" not in known:
                return (
                    "Have you ever been diagnosed with any important medical condition?"
                    if lang == "en"
                    else "क्या आपको पहले कभी कोई महत्वपूर्ण बीमारी बताई गई है?"
                )

            if "past_surgical_history" not in known:
                return (
                    "Have you ever had any major surgery or operation?"
                    if lang == "en"
                    else "क्या आपकी कभी कोई बड़ी सर्जरी या ऑपरेशन हुआ है?"
                )

            if "hospitalizations" not in known:
                return (
                    "Have you ever been admitted to a hospital for any reason?"
                    if lang == "en"
                    else "क्या आपको कभी किसी कारण से अस्पताल में भर्ती होना पड़ा है?"
                )

        if section == "drug_allergy":
            if "medications" not in known:
                return (
                    "Are you taking any regular medicines or supplements?"
                    if lang == "en"
                    else "क्या आप कोई नियमित दवा या सप्लीमेंट लेते हैं?"
                )

            if "allergies" not in known:
                return (
                    "Do you have any medicine or food allergies?"
                    if lang == "en"
                    else "क्या आपको किसी दवा या खाने से एलर्जी है?"
                )

        if section == "hpi":
            if (
                "bowel_frequency" not in known
                and state.topic == "gastrointestinal"
            ):
                candidate = (
                    "Approximately how many bowel movements are you having in a day?"
                    if lang == "en"
                    else "लगभग एक दिन में आपको कितनी बार मल त्याग हो रहा है?"
                )

                if candidate.lower() != current_question:
                    return candidate

            if (
                "stool_consistency" not in known
                and state.topic == "gastrointestinal"
            ):
                candidate = (
                    "What are the stools like, for example hard, normal, loose, or watery?"
                    if lang == "en"
                    else "मल कैसा है, जैसे बहुत सख्त, सामान्य, ढीला या पानी जैसा?"
                )

                if candidate.lower() != current_question:
                    return candidate

            if (
                "straining" not in known
                and state.topic == "gastrointestinal"
            ):
                candidate = (
                    "Do you have to strain or push hard to pass stool?"
                    if lang == "en"
                    else "क्या मल त्याग करते समय आपको बहुत जोर लगाना पड़ता है?"
                )

                if candidate.lower() != current_question:
                    return candidate

            if (
                "blood_in_stool" not in known
                and state.topic == "gastrointestinal"
            ):
                candidate = (
                    "Have you noticed any blood in or on the stool?"
                    if lang == "en"
                    else "क्या आपने मल में या मल पर कोई खून देखा है?"
                )

                if candidate.lower() != current_question:
                    return candidate

            if (
                "abdominal_distension" not in known
                and state.topic == "gastrointestinal"
            ):
                candidate = (
                    "Have you noticed bloating or swelling of the abdomen?"
                    if lang == "en"
                    else "क्या पेट में फूलना या सूजन महसूस होती है?"
                )

                if candidate.lower() != current_question:
                    return candidate

            if "passing gas normally" not in current_question:
                return (
                    "Are you passing gas normally?"
                    if lang == "en"
                    else "क्या आप सामान्य रूप से गैस पास कर पा रहे हैं?"
                )

        if (
            section == "hpi"
            and current_question
            and "other symptoms" in current_question
        ):
            return FALLBACK_QUESTIONS[lang]["hpi"]

        return FALLBACK_QUESTIONS[lang].get(
            section,
            FALLBACK_QUESTIONS[lang]["hpi"],
        )

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are Aurora's conversational clinical history-taking engine. "
            "Collect a comprehensive history before a doctor consultation. "
            "Do not diagnose, prescribe, or recommend treatment. "
            "The conversation is adaptive and there is no question-count limit. "
            "Use the patient's complaint, complete conversation, known history, "
            "and remaining information gaps to decide the next question. "
            "Extract every explicit fact from the latest answer, including facts "
            "that belong to a different history section than the current focus. "
            "Never lose a fact because it is outside the current section. "
            "Never let an unrelated date, duration, or number overwrite another "
            "clinical fact. For example, surgery 8 months ago is not symptom "
            "onset unless the patient explicitly says the symptom started then. "
            "Preserve explicit negatives. Do not infer negatives from silence. "
            "Do not ask compound questions that mix unrelated domains. "
            "Ask one natural question at a time. Clarify vague answers when "
            "their precision matters. Do not repeat a question already answered. "
            "Cover HPI first, then past medical and surgical history, drug and "
            "allergy history, family history, personal history, and review of "
            "systems. AYUSH-specific history is conditional. "
            "A section may be considered complete when the patient has provided "
            "the relevant information or explicitly said there is none, it is "
            "not applicable, or they cannot provide it. "
            "The overall interview is complete only after the clinically relevant "
            "history structure has been sufficiently covered. "
            "Return only JSON. Use exactly these top-level keys: "
            '"topic", "section", "completed_sections", "facts", '
            '"next_question", "completed". '
            '"facts" must be an array of objects with "section", "field", '
            '"value", and optional "negative". '
            "The field name may be a known clinical field or a descriptive custom "
            "field; do not discard information merely because a field is not in "
            "a predefined list. Use the exact patient wording when useful. "
            "completed_sections contains all sections now adequately covered. "
            "section is the focus for the next question. "
            "next_question is null only when completed is true. "
            "completed is true only when the full interview is complete."
        )

    @staticmethod
    def _sanitize_plan(
        payload: dict[str, Any],
        current_section: str,
        language: str | None,
    ) -> InterviewPlan:
        raw_facts = payload.get(
            "facts"
        )

        if not isinstance(
            raw_facts,
            list,
        ):
            raw_facts = []

        if not raw_facts and isinstance(
            payload.get("fields"),
            dict,
        ):
            raw_facts = [
                {
                    "section": current_section,
                    "field": field,
                    "value": value,
                }
                for field, value in payload[
                    "fields"
                ].items()
            ]

        raw_negatives = payload.get(
            "negative_facts",
            payload.get("negatives"),
        )

        if isinstance(
            raw_negatives,
            dict,
        ):
            raw_negatives = [
                key
                for key, value in raw_negatives.items()
                if value is True
            ]

        if isinstance(
            raw_negatives,
            str,
        ):
            raw_negatives = [
                raw_negatives
            ]

        if isinstance(
            raw_negatives,
            list,
        ):
            raw_facts.extend(
                {
                    "section": (
                        field.get("section")
                        if isinstance(field, dict)
                        else current_section
                    ),
                    "field": (
                        field.get("field")
                        if isinstance(field, dict)
                        else field
                    ),
                    "value": False,
                    "negative": True,
                }
                for field in raw_negatives
            )

        facts: list[dict[str, Any]] = []

        for raw_fact in raw_facts:
            if not isinstance(
                raw_fact,
                dict,
            ):
                continue

            raw_field = (
                raw_fact.get("field")
                or raw_fact.get("name")
            )

            if not raw_field:
                continue

            field = normalize_field_name(
                str(raw_field)
            )

            value = raw_fact.get(
                "value"
            )

            if value is None:
                continue

            section = normalize_section(
                str(
                    raw_fact.get(
                        "section"
                    )
                    or current_section
                )
            )

            negative = (
                raw_fact.get(
                    "negative"
                )
                is True
            )

            facts.append(
                {
                    "section": section,
                    "field": field,
                    "value": value,
                    "negative": negative,
                }
            )

        raw_completed = payload.get(
            "completed_sections"
        )

        if isinstance(
            raw_completed,
            str,
        ):
            raw_completed = [
                raw_completed
            ]

        completed_sections = [
            normalize_section(
                str(section)
            )
            for section in (
                raw_completed
                if isinstance(
                    raw_completed,
                    list,
                )
                else []
            )
        ]

        completed_sections = list(
            dict.fromkeys(
                section
                for section in completed_sections
                if section
                in {
                    *SECTION_ORDER,
                    "ayush",
                }
            )
        )

        section = normalize_section(
            str(
                payload.get(
                    "section"
                )
                or current_section
            )
        )

        next_question = payload.get(
            "next_question"
        )

        if not isinstance(
            next_question,
            str,
        ):
            next_question = None
        else:
            next_question = " ".join(
                next_question.strip().split()
            )

        completed = (
            payload.get(
                "completed"
            )
            is True
        )

        if completed:
            next_question = None

        if next_question and next_question.count("?") > 1:
            next_question = (
                next_question.rsplit(
                    "?",
                    1,
                )[0].strip()
                + "?"
            )

        if (
            next_question
            and self_question_is_compound(
                next_question
            )
        ):
            next_question = None

        topic = payload.get(
            "topic"
        )

        if not isinstance(
            topic,
            str,
        ):
            topic = None

        return InterviewPlan(
            topic=topic,
            section=section,
            completed_sections=completed_sections,
            facts=facts,
            next_question=next_question,
            completed=completed,
            ai_used=True,
        )

    @staticmethod
    def _merge_fact_lists(
        first: list[dict[str, Any]] | None,
        second: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        for source in (
            first or [],
            second or [],
        ):
            for fact in source:
                key = (
                    fact.get("section"),
                    fact.get("field"),
                    json.dumps(
                        fact.get("value"),
                        ensure_ascii=False,
                        sort_keys=True,
                        default=str,
                    ),
                    fact.get("negative", False),
                )

                if key not in {
                    (
                        existing.get("section"),
                        existing.get("field"),
                        json.dumps(
                            existing.get("value"),
                            ensure_ascii=False,
                            sort_keys=True,
                            default=str,
                        ),
                        existing.get("negative", False),
                    )
                    for existing in result
                }:
                    result.append(
                        fact
                    )

        return result

    @staticmethod
    def _dedupe_facts(
        facts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return InterviewExtractor._merge_fact_lists(
            [],
            facts,
        )

    @staticmethod
    def _clean_json(
        content: str,
    ) -> str:
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

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start >= 0 and end > start:
            cleaned = cleaned[
                start:end + 1
            ]

        return cleaned.strip()

    @staticmethod
    def _repair_json(
        content: str,
    ) -> str:
        repaired = content

        repaired = re.sub(
            r",\s*([}\]])",
            r"\1",
            repaired,
        )

        repaired = re.sub(
            r'"\s*:\s*([}\],])',
            r'": null\1',
            repaired,
        )

        repaired = re.sub(
            r'"negatives"\s*:\s*\{\s*([^{}]+?)\s*\}',
            lambda match: (
                '"negatives": ['
                + ", ".join(
                    f'"{item.strip().strip(chr(34))}"'
                    for item in match.group(1).split(",")
                    if item.strip()
                )
                + "]"
            ),
            repaired,
        )

        repaired = re.sub(
            r'"completed"\s*([,}])',
            r'"completed": false\1',
            repaired,
        )

        return repaired

    @staticmethod
    def _pythonize(
        content: str,
    ) -> str:
        value = content

        value = re.sub(
            r"\btrue\b",
            "True",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\bfalse\b",
            "False",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\bnull\b",
            "None",
            value,
            flags=re.IGNORECASE,
        )

        return value

    @staticmethod
    def plan_dict(
        plan: InterviewPlan,
    ) -> dict[str, Any]:
        return {
            "topic": plan.topic,
            "section": plan.section,
            "completed_sections": plan.completed_sections,
            "facts": plan.facts,
            "next_question": plan.next_question,
            "completed": plan.completed,
            "ai_used": plan.ai_used,
        }

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        return re.sub(
            r"[,.!?।]+",
            "",
            text.strip().lower(),
        )

    @staticmethod
    def _debug(
        event: str,
        **data: Any,
    ) -> None:
        if not settings.interview_debug:
            return

        print(
            "[INTERVIEW] "
            + event
            + " "
            + json.dumps(
                data,
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )


def self_question_is_compound(
    question: str,
) -> bool:
    lower = question.lower()

    domain_groups = (
        (
            "medicine",
            "medication",
            "drug",
        ),
        (
            "allerg",
            "food",
        ),
        (
            "family",
            "work",
            "diet",
            "sleep",
        ),
        (
            "smoking",
            "tobacco",
            "alcohol",
        ),
    )

    matched_groups = 0

    for group in domain_groups:
        if any(
            term in lower
            for term in group
        ):
            matched_groups += 1

    return matched_groups > 1
