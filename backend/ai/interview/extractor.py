from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from backend.ai.interview.state import FIELD_PRIMARY_SECTION, TARGET_DESCRIPTIONS, TARGET_FIELDS, InterviewState, normalize_field_name
from backend.config import settings

TOPIC_KEYWORDS = {
    "chest_pain": (
        "chest pain",
        "chest pressure",
        "chest discomfort",
        "सीने में दर्द",
        "सीने में दबाव",
    ),
    "headache": (
        "headache",
        "head pain",
        "migraine",
        "सिरदर्द",
        "सिर में दर्द",
        "माइग्रेन",
    ),
    "respiratory": (
        "cough",
        "coughing",
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
        "vomiting",
        "nausea",
        "कब्ज",
        "दस्त",
        "पेट में दर्द",
        "उल्टी",
        "मतली",
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
    "skin": (
        "rash",
        "itching",
        "skin problem",
        "दाने",
        "चकत्ते",
        "खुजली",
        "त्वचा",
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

NEGATIVE_ANSWERS = {
    "no",
    "none",
    "nothing",
    "nothing else",
    "no more",
    "not applicable",
    "not relevant",
    "i don't know",
    "i do not know",
    "na",
    "n/a",
    "नहीं",
    "कुछ नहीं",
    "और कुछ नहीं",
    "कोई नहीं",
    "लागू नहीं",
    "पता नहीं",
}

QUESTION_BUNDLES = (
    (
        "onset",
        "duration",
        "course",
    ),
    (
        "site",
        "laterality",
    ),
    (
        "severity",
        "character",
        "impact_on_daily_life",
    ),
    (
        "timing",
        "frequency",
        "associated_symptoms",
    ),
    (
        "aggravating_factors",
        "relieving_factors",
    ),
    (
        "previous_episodes",
        "prior_treatment",
        "response_to_treatment",
        "prior_investigations",
    ),
    (
        "bowel_frequency",
        "stool_consistency",
        "straining",
        "blood_in_stool",
    ),
    (
        "abdominal_distension",
        "nausea_vomiting",
        "fever",
    ),
    (
        "breathing_difficulty",
        "cough",
        "wheeze",
        "fever",
    ),
    (
        "urinary_frequency",
        "urinary_burning",
        "urinary_blood",
        "fever",
    ),
    (
        "past_medical_history",
        "past_surgical_history",
        "hospitalizations",
        "immunizations",
    ),
    (
        "medications",
        "allergies",
        "adverse_drug_reactions",
    ),
    (
        "occupation",
        "diet",
        "sleep",
        "physical_activity",
        "smoking",
        "alcohol",
        "tobacco",
    ),
    (
        "menstrual_history",
        "pregnancy_status",
        "sexual_history",
    ),
    (
        "constitutional",
        "cardiovascular",
        "respiratory",
        "gastrointestinal",
        "genitourinary",
        "neurological",
    ),
)

TARGET_TERM_HINTS = {
    "site": (
        "chest",
        "stomach",
        "abdomen",
        "head",
        "back",
        "neck",
        "throat",
        "arm",
        "leg",
        "below stomach",
        "upper abdomen",
        "lower abdomen",
    ),
    "laterality": (
        "left",
        "right",
        "both sides",
        "both",
    ),
    "character": (
        "burning",
        "pressure",
        "squeezing",
        "stabbing",
        "throbbing",
        "sharp",
        "dull",
        "aching",
        "twisting",
        "turning",
        "churning",
        "cramping",
    ),
    "timing": (
        "constant",
        "all the time",
        "nonstop",
        "continuous",
        "comes and goes",
        "on and off",
        "intermittent",
        "morning",
        "afternoon",
        "evening",
        "night",
    ),
    "aggravating_factors": (
        "worse",
        "worsens",
        "worse when",
        "worse with",
        "makes it worse",
        "make it worse",
    ),
    "relieving_factors": (
        "better",
        "helps",
        "relief",
        "improves",
        "eases",
        "makes it better",
    ),
    "radiation": (
        "radiate",
        "spreads to",
        "spread to",
        "goes to",
        "moves to",
        "arm",
        "shoulder",
        "jaw",
        "neck",
        "back",
    ),
    "associated_symptoms": (
        "nausea",
        "vomit",
        "fever",
        "dizziness",
        "headache",
        "cough",
        "weakness",
        "pain",
        "bloating",
    ),
    "previous_episodes": (
        "before",
        "previously",
        "ever had",
        "happened before",
        "first time",
        "पहले",
    ),
    "prior_treatment": (
        "medicine",
        "medication",
        "drug",
        "remedy",
        "pharmacist",
        "treated",
        "treatment",
        "दवा",
    ),
    "response_to_treatment": (
        "helped",
        "better",
        "relief",
        "improved",
        "same",
        "unchanged",
        "no effect",
        "for about",
        "for 2 hours",
    ),
    "prior_investigations": (
        "test",
        "tests",
        "scan",
        "x-ray",
        "xray",
        "ultrasound",
        "blood work",
        "investigation",
    ),
    "impact_on_daily_life": (
        "work",
        "sleep",
        "daily",
        "activities",
        "walking",
        "eating",
        "working",
        "cannot",
        "unable",
    ),
    "nausea_vomiting": (
        "nausea",
        "nauseous",
        "vomit",
        "vomiting",
        "मतली",
        "उल्टी",
    ),
    "vision_or_neuro": (
        "vision",
        "blurred",
        "numbness",
        "weakness",
        "tingling",
        "dizziness",
        "fainting",
    ),
    "cough": (
        "cough",
        "coughing",
        "खांसी",
        "खाँसी",
    ),
    "wheeze": (
        "wheez",
        "घरघराहट",
    ),
    "fever": (
        "fever",
        "temperature",
        "chills",
        "बुखार",
    ),
    "bowel_frequency": (
        "times a day",
        "times per day",
        "bowel movement",
        "bowel movements",
        "motions",
        "stools",
    ),
    "stool_consistency": (
        "hard",
        "soft",
        "loose",
        "watery",
        "normal",
        "stools are",
        "stool is",
        "very hard",
        "सख्त",
        "ढीला",
        "पानी जैसा",
    ),
    "straining": (
        "strain",
        "straining",
        "push hard",
        "जोर",
    ),
    "blood_in_stool": (
        "blood",
        "bleeding",
        "खून",
    ),
    "abdominal_distension": (
        "bloat",
        "bloated",
        "distension",
        "swelling",
        "पेट फूल",
        "सूजन",
    ),
    "breathing_difficulty": (
        "shortness of breath",
        "difficulty breathing",
        "trouble breathing",
        "cannot breathe",
        "breathless",
        "breathing",
        "सांस",
        "साँस",
    ),
    "urinary_frequency": (
        "urine",
        "urination",
        "urinary frequency",
        "frequency of urination",
        "पेशाब",
    ),
    "urinary_burning": (
        "burning while urinating",
        "painful urination",
        "burning",
        "जलन",
    ),
    "urinary_blood": (
        "blood in urine",
        "blood in my urine",
        "पेशाब में खून",
    ),
    "past_medical_history": (
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
        "medical condition",
        "disease",
        "बीमारी",
        "मधुमेह",
        "अस्थमा",
        "थायरॉइड",
    ),
    "past_surgical_history": (
        "surgery",
        "surgeries",
        "operation",
        "operations",
        "operated",
        "सर्जरी",
        "ऑपरेशन",
    ),
    "hospitalizations": (
        "hospital",
        "admitted",
        "hospitalized",
        "भर्ती",
    ),
    "immunizations": (
        "vaccine",
        "vaccination",
        "immunization",
        "covid vaccine",
        "टीका",
    ),
    "medications": (
        "medicine",
        "medicines",
        "medication",
        "medications",
        "drug",
        "drugs",
        "tablet",
        "tablets",
        "दवा",
    ),
    "allergies": (
        "allergy",
        "allergies",
        "allergic",
        "एलर्जी",
    ),
    "adverse_drug_reactions": (
        "reaction to",
        "reactions to",
        "side effect",
        "side effects",
        "adverse reaction",
        "bad reaction",
    ),
    "family_history": (
        "family",
        "mother",
        "father",
        "brother",
        "sister",
        "runs in my family",
        "परिवार",
    ),
    "occupation": (
        "job",
        "work",
        "occupation",
        "desk job",
        "profession",
        "काम",
        "नौकरी",
    ),
    "diet": (
        "diet",
        "eat",
        "eating",
        "meals",
        "meal",
        "food",
        "roti",
        "rice",
        "potato",
        "vegetable",
        "भोजन",
    ),
    "sleep": (
        "sleep",
        "sleeping",
        "sleep pattern",
        "hours of sleep",
        "नींद",
    ),
    "physical_activity": (
        "exercise",
        "physical activity",
        "activity",
        "walking",
        "gym",
        "active",
        "व्यायाम",
    ),
    "smoking": (
        "smoke",
        "smoking",
        "cigarette",
        "सिगरेट",
        "धूम्रपान",
    ),
    "alcohol": (
        "alcohol",
        "drink alcohol",
        "drinking",
        "शराब",
    ),
    "tobacco": (
        "tobacco",
        "gutkha",
        "paan",
        "तंबाकू",
    ),
    "menstrual_history": (
        "period",
        "periods",
        "menstrual",
        "menstruation",
        "मासिक",
    ),
    "pregnancy_status": (
        "pregnant",
        "pregnancy",
        "गर्भावस्था",
    ),
    "sexual_history": (
        "sexual",
        "sex",
        "sexual health",
        "यौन",
    ),
    "constitutional": (
        "fever",
        "chills",
        "fatigue",
        "weight loss",
        "weight gain",
        "appetite",
    ),
    "cardiovascular": (
        "chest pain",
        "palpitation",
        "palpitations",
        "heart",
    ),
    "respiratory": (
        "cough",
        "breath",
        "breathing",
        "wheeze",
    ),
    "gastrointestinal": (
        "nausea",
        "vomit",
        "abdominal",
        "stomach",
        "diarrhea",
        "constipation",
        "bloating",
    ),
    "genitourinary": (
        "urine",
        "urination",
        "urinary",
        "painful urination",
    ),
    "neurological": (
        "dizziness",
        "fainting",
        "numbness",
        "weakness",
        "tingling",
    ),
    "musculoskeletal": (
        "joint",
        "muscle",
        "back pain",
        "neck pain",
    ),
    "skin": (
        "rash",
        "itch",
        "skin",
    ),
    "endocrine": (
        "thyroid",
        "heat intolerance",
        "cold intolerance",
    ),
    "hematologic": (
        "easy bruising",
        "bleeding",
        "anemia",
    ),
    "psychiatric": (
        "anxiety",
        "depression",
        "stress",
        "panic",
    ),
}

BINARY_TARGETS = {
    "straining",
    "blood_in_stool",
    "abdominal_distension",
    "breathing_difficulty",
    "wheeze",
    "fever",
    "urinary_burning",
    "urinary_blood",
    "smoking",
    "alcohol",
    "tobacco",
}

NEGATABLE_TARGETS = BINARY_TARGETS | {
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "previous_episodes",
}


@dataclass
class QuestionDecision:
    question: str
    target: str | None
    ai_used: bool


class InterviewModelError(RuntimeError):
    pass


class InterviewExtractor:
    def __init__(self) -> None:
        self.url = settings.lemonade_url
        self.model = settings.lemonade_model
        self.timeout = settings.lemonade_timeout
        self.enabled = settings.interview_ai_enabled
        self.provider = settings.interview_ai_provider

    async def generate_question(
        self,
        state: InterviewState,
        conversation: list[dict[str, Any]],
        language: str,
        session_id: str | None = None,
        forced_target: str | None = None,
    ) -> QuestionDecision:
        candidates = state.candidate_targets()

        if forced_target and forced_target in candidates:
            candidates = [forced_target]

        if not candidates:
            return QuestionDecision(
                self._emergency_question(
                    state.current_section,
                    language,
                ),
                None,
                False,
            )

        if not self.enabled or self.provider != "lemonade":
            return QuestionDecision(
                self._emergency_question_for_target(
                    candidates[0],
                    language,
                ),
                candidates[0],
                False,
            )

        prompt = self._build_question_prompt(
            state,
            conversation,
            language,
            candidates,
            forced_target,
        )

        try:
            content = await self._call_model(
                prompt,
                session_id,
            )

            decision = self._parse_question(
                content,
                candidates,
            )

            if (
                decision.question
                and decision.target
                and decision.question.lower()
                not in {
                    item.lower()
                    for item in state.question_history
                }
            ):
                return decision

        except InterviewModelError as exc:
            self._debug(
                "QUESTION_FAILURE",
                session_id=session_id,
                error_type=type(exc).__name__,
                error=str(exc),
            )

        return QuestionDecision(
            self._emergency_question_for_target(
                candidates[0],
                language,
            ),
            candidates[0],
            False,
        )

    def extract_facts(
        self,
        text: str,
        state: InterviewState,
        turn_id: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized = text.strip()

        if not normalized:
            return []

        facts: list[dict[str, Any]] = []
        topic = self.detect_topic(normalized)

        pending_targets = self._pending_targets(
            state.pending_target
        )

        if (
            topic
            and state.known_fields().get(
                "chief_complaint"
            ) is None
            and not pending_targets
        ):
            facts.append(
                self._fact(
                    "hpi",
                    "chief_complaint",
                    self._complaint_from_topic(topic),
                    normalized,
                    turn_id,
                )
            )

        if "chief_complaint" in pending_targets:
            facts.append(
                self._fact(
                    "hpi",
                    "chief_complaint",
                    normalized,
                    normalized,
                    turn_id,
                )
            )

        whole_answer_negative = self.is_negative_answer(
            normalized
        )

        for target in pending_targets:
            if (
                target not in TARGET_FIELDS
                or target == "section_closure"
                or target == "chief_complaint"
            ):
                continue

            negative = (
                whole_answer_negative
                or (
                    target in NEGATABLE_TARGETS
                    and self._target_negative(
                        target,
                        normalized,
                    )
                )
            )

            value = self._bundle_target_value(
                target,
                normalized,
                negative,
            )

            if value is not None:
                section = FIELD_PRIMARY_SECTION.get(
                    target,
                    state.current_section,
                )

                facts.append(
                    self._fact(
                        section,
                        target,
                        value,
                        normalized,
                        turn_id,
                        negative,
                    )
                )

        facts.extend(
            self._cross_section_facts(
                normalized,
                state,
                turn_id,
            )
        )

        return self._dedupe(facts)

    @staticmethod
    def is_negative_answer(text: str) -> bool:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        if (
            normalized in NEGATIVE_ANSWERS
            or "nothing else" in normalized
            or "कुछ नहीं" in normalized
            or "और कुछ नहीं" in normalized
        ):
            return True

        return bool(
            re.fullmatch(
                r"(?:no|none|n/?a|नहीं)(?:\s+(?:more|else|nothing))?",
                normalized,
            )
        )

    @staticmethod
    def detect_topic(text: str) -> str | None:
        normalized = text.lower()

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(
                keyword in normalized
                for keyword in keywords
            ):
                return topic

        return None

    async def _call_model(
        self,
        prompt: str,
        session_id: str | None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 96,
            "stream": False,
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
        }

        last_error: Exception | None = None

        for url in self._candidate_urls():
            try:
                started = time.monotonic()

                timeout = httpx.Timeout(
                    connect=3.0,
                    read=self.timeout,
                    write=3.0,
                    pool=3.0,
                )

                async with httpx.AsyncClient(
                    timeout=timeout
                ) as client:
                    response = await client.post(
                        url,
                        json=payload,
                    )

                    if (
                        response.status_code
                        in {400, 404, 422}
                        and "chat_template_kwargs"
                        in payload
                    ):
                        retry_payload = dict(
                            payload
                        )

                        retry_payload.pop(
                            "chat_template_kwargs",
                            None,
                        )

                        response = await client.post(
                            url,
                            json=retry_payload,
                        )

                    response.raise_for_status()
                    body = response.json()

                elapsed = round(
                    (time.monotonic() - started)
                    * 1000,
                    2,
                )

                choices = (
                    body.get("choices")
                    if isinstance(body, dict)
                    else None
                )

                if (
                    not isinstance(choices, list)
                    or not choices
                ):
                    raise ValueError(
                        "Local model returned no choices"
                    )

                choice = (
                    choices[0]
                    if isinstance(
                        choices[0],
                        dict,
                    )
                    else {}
                )

                message = (
                    choice.get(
                        "message",
                        {},
                    )
                    if isinstance(
                        choice.get(
                            "message",
                            {},
                        ),
                        dict,
                    )
                    else {}
                )

                content = message.get(
                    "content"
                )

                if isinstance(content, list):
                    content = "".join(
                        item.get(
                            "text",
                            "",
                        )
                        if isinstance(
                            item,
                            dict,
                        )
                        else str(item)
                        for item in content
                    )

                if (
                    not isinstance(
                        content,
                        str,
                    )
                    or not content.strip()
                ):
                    raise ValueError(
                        "Local model returned empty content"
                    )

                self._debug(
                    "QUESTION_MODEL_OK",
                    session_id=session_id,
                    url=url,
                    model=self.model,
                    elapsed_ms=elapsed,
                )

                return content

            except (
                httpx.HTTPError,
                ValueError,
                KeyError,
                TypeError,
            ) as exc:
                last_error = InterviewModelError(
                    str(exc)
                )

                self._debug(
                    "QUESTION_ENDPOINT_FAILURE",
                    session_id=session_id,
                    url=url,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )

        raise last_error or InterviewModelError(
            "Local model request failed"
        )

    def _build_question_prompt(
        self,
        state: InterviewState,
        conversation: list[dict[str, Any]],
        language: str,
        candidates: list[str],
        forced: str | None = None,
    ) -> str:
        recent = conversation[-8:]
        known = state.known_fields()

        candidate_text = "\n".join(
            f"- {item}: "
            f"{TARGET_DESCRIPTIONS.get(item, {}).get(
                language, item.replace('_', ' '))}"
            for item in candidates
        )

        candidate_set = set(candidates)
        valid_bundles: list[str] = []

        for bundle in QUESTION_BUNDLES:
            usable = tuple(
                item
                for item in bundle
                if item in candidate_set
            )

            if len(usable) >= 2:
                valid_bundles.append(
                    ",".join(usable)
                )

        bundle_text = "\n".join(
            f"- {item}"
            for item in valid_bundles
        )

        force = (
            f"You must use target: {forced}.\n"
            if forced
            else ""
        )

        return (
            f"Preferred language: {language}\n"
            f"Current section: {state.current_section}\n"
            f"Clinical topic: {state.topic}\n"
            f"Known history: "
            f"{json.dumps(known, ensure_ascii=False, default=str)}\n"
            f"Recent questions: "
            f"{json.dumps(state.question_history[-6:], ensure_ascii=False)}\n"
            f"Recent target sequence: "
            f"{json.dumps(state.target_history[-6:], ensure_ascii=False)}\n"
            f"Recent conversation: "
            f"{json.dumps(recent, ensure_ascii=False, default=str)}\n"
            f"Allowed targets:\n{candidate_text}\n"
            f"Preferred related target bundles:\n{bundle_text}\n"
            f"{force}"
            "Choose the most useful allowed target or closely related allowed targets from one section. "
            "Ask exactly one concise patient-facing question that the patient can answer in one response. "
            "When a valid bundle is available, prefer bundling closely related targets to reduce interview time. "
            "For past history, combine medical conditions, surgeries, hospitalizations, and immunizations when possible. "
            "For drug and allergy history, combine medicines, allergies, and adverse reactions when possible. "
            "For personal history, combine occupation, diet, sleep, physical activity, smoking, alcohol, and tobacco when possible. "
            "For review of systems, screen several relevant systems together rather than one system at a time. "
            "Never ask a section closure question. "
            "Do not diagnose, explain, prescribe, reassure, or recommend treatment. "
            "Never repeat an already answered target unless its answer is genuinely incomplete. "
            "Return exactly two lines and nothing else:\n"
            "TARGET: <target> or <target1,target2,...>\n"
            "QUESTION: <question>"
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

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are Aurora's clinical history-taking interviewer. "
            "Your job is only to collect history before a clinician consultation. "
            "Follow the required order HPI, past medical and surgical history, drug and allergy history, family history, personal history, review of systems, then AYUSH-specific history only when AYUSH mode is enabled. "
            "Adapt questions to the patient's complaint and answers. "
            "You may ask about closely related details together when that reduces the number of turns. "
            "Preserve the patient's meaning and do not infer facts that were not stated. "
            "Do not diagnose or recommend treatment. "
            "Keep questions natural, short, respectful, and in the patient's selected language."
        )

    def _parse_question(
        self,
        content: str,
        candidates: list[str],
    ) -> QuestionDecision:
        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        target_match = re.search(
            r"(?:^|\n)\s*TARGET\s*:\s*([^\n]+)",
            cleaned,
            flags=re.IGNORECASE,
        )

        question_match = re.search(
            r"(?:^|\n)\s*QUESTION\s*:\s*(.+)",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )

        raw_target = (
            target_match.group(1)
            .strip()
            .strip("`\"'")
            if target_match
            else ""
        )

        raw_target = re.sub(
            r"^bundle\s*:\s*",
            "",
            raw_target,
            flags=re.IGNORECASE,
        )

        targets = list(
            dict.fromkeys(
                item.strip().lower()
                for item in re.split(
                    r"[,|;/]+|\band\b",
                    raw_target,
                )
                if item.strip()
            )
        )

        target = None

        if (
            targets
            and 1 <= len(targets) <= 7
            and all(
                item in candidates
                for item in targets
            )
        ):
            if len(targets) == 1:
                target = targets[0]
            elif any(
                set(targets).issubset(
                    set(bundle)
                )
                for bundle in QUESTION_BUNDLES
            ):
                target = (
                    "bundle:"
                    + ",".join(targets)
                )

        question = (
            question_match.group(1).strip()
            if question_match
            else self._extract_question_line(
                cleaned
            )
        )

        question = re.sub(
            r"^[-*\d.)\s]+",
            "",
            question,
        ).strip().strip('"')

        question = re.sub(
            r"\s+",
            " ",
            question,
        )

        question = re.split(
            r"\n(?:TARGET|QUESTION)\s*:",
            question,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if "?" in question:
            question = (
                question.split(
                    "?",
                    1,
                )[0].strip()
                + "?"
            )
        elif question:
            question += "?"

        if (
            not self._valid_question(
                question
            )
            or target is None
        ):
            return QuestionDecision(
                "",
                target,
                True,
            )

        return QuestionDecision(
            question,
            target,
            True,
        )

    @staticmethod
    def _extract_question_line(
        content: str,
    ) -> str:
        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        for line in reversed(lines):
            if "?" in line:
                return line

        return lines[-1] if lines else ""

    @staticmethod
    def _valid_question(
        question: str,
    ) -> bool:
        if len(question) < 8 or len(question) > 320:
            return False

        lower = question.lower()

        return not any(
            marker in lower
            for marker in (
                "target:",
                "question:",
                "```",
                "{",
                "}",
            )
        )

    @staticmethod
    def _pending_targets(
        target: str | None,
    ) -> list[str]:
        if not target:
            return []

        raw = (
            target[7:]
            if target.startswith("bundle:")
            else target
        )

        return [
            item.strip().lower()
            for item in re.split(
                r"[,|;/]+|\band\b",
                raw,
            )
            if item.strip()
        ]

    @staticmethod
    def _target_negative(
        target: str,
        text: str,
    ) -> bool:
        normalized = text.lower()
        terms = TARGET_TERM_HINTS.get(
            target,
            (),
        )

        if not terms:
            return False

        positive = False
        negative = False

        for term in terms:
            for match in re.finditer(
                re.escape(term),
                normalized,
            ):
                prefix = normalized[
                    max(
                        0,
                        match.start() - 35,
                    ):match.start()
                ]

                if (
                    re.search(
                        r"\b(?:no|not|never|without|don't|do not|denies)\b",
                        prefix,
                    )
                    or "नहीं" in prefix
                ):
                    negative = True
                else:
                    positive = True

        return negative and not positive

    @staticmethod
    def _bundle_target_value(
        target: str,
        text: str,
        negative: bool,
    ) -> Any:
        if negative:
            return False

        normalized = text.lower()

        if target == "chief_complaint":
            return text

        if target == "severity":
            match = re.search(
                r"^\s*(10|[0-9])"
                r"(?:\s*(?:/|out of|में से)\s*10)?"
                r"(?:\s|,|;|$)",
                normalized,
            )

            if match:
                return int(
                    match.group(1)
                )

            match = re.search(
                r"\b(10|[0-9])\s*"
                r"(?:/|out of|में से)\s*10\b",
                normalized,
            )

            if match:
                return int(
                    match.group(1)
                )

            return None

        if target in {
            "onset",
            "duration",
        }:
            match = re.search(
                r"\b(?:started|began|since|for)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return match.group(1).strip()

            match = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple|a few)\s+"
                r"(day|days|hour|hours|week|weeks|month|months|year|years)\b",
                normalized,
            )

            return (
                f"{match.group(1)} {match.group(2)}"
                if match
                else None
            )

        if target == "course":
            if re.search(
                r"\b(?:same|unchanged|no change|stable)\b",
                normalized,
            ):
                return "unchanged"

            if re.search(
                r"\b(?:worse|worsening|getting worse)\b",
                normalized,
            ):
                return "worsening"

            if re.search(
                r"\b(?:better|improving|getting better)\b",
                normalized,
            ):
                return "improving"

            return None

        if target == "site":
            match = re.search(
                r"\b(?:in|at|around|below|above|near)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return match.group(1).strip()

            for term in TARGET_TERM_HINTS["site"]:
                if term in normalized:
                    return term

            return None

        if target == "laterality":
            if (
                "both sides" in normalized
                or re.search(
                    r"\bboth\b",
                    normalized,
                )
            ):
                return "both"

            if "left" in normalized:
                return "left"

            if "right" in normalized:
                return "right"

            return None

        if target == "character":
            for value in (
                "burning",
                "pressure",
                "squeezing",
                "stabbing",
                "throbbing",
                "sharp",
                "dull",
                "aching",
                "twisting",
                "turning",
                "churning",
                "cramping",
            ):
                if value in normalized:
                    return value

            match = re.search(
                r"\b(?:feels like|feel like|feels as if|like)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            return (
                match.group(1).strip()
                if match
                else None
            )

        if target in {
            "timing",
            "frequency",
            "bowel_frequency",
            "urinary_frequency",
        }:
            if target == "timing":
                if any(
                    item in normalized
                    for item in (
                        "constant",
                        "all the time",
                        "nonstop",
                        "continuous",
                    )
                ):
                    return "constant"

                if any(
                    item in normalized
                    for item in (
                        "comes and goes",
                        "on and off",
                        "intermittent",
                    )
                ):
                    return "intermittent"

                if any(
                    item in normalized
                    for item in (
                        "morning",
                        "afternoon",
                        "evening",
                        "night",
                    )
                ):
                    return text

                return None

            if (
                target == "urinary_frequency"
                and not any(
                    item in normalized
                    for item in TARGET_TERM_HINTS[
                        "urinary_frequency"
                    ]
                )
            ):
                return None

            match = re.search(
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:times?|bowel movements?|motions?)\s*"
                r"(?:a|per)\s*"
                r"(?:day|week|month)\b",
                normalized,
            )

            return (
                match.group(0)
                if match
                else None
            )

        if target == "stool_consistency":
            match = re.search(
                r"\b(?:stools?|bowel movements?|stool)\b"
                r"[^,.!?;]{0,25}\b"
                r"(?:very\s+)?"
                r"(hard|soft|loose|watery|normal)\b",
                normalized,
            )

            return (
                match.group(1)
                if match
                else None
            )

        if target in BINARY_TARGETS:
            return (
                True
                if any(
                    term in normalized
                    for term in TARGET_TERM_HINTS.get(
                        target,
                        (),
                    )
                )
                else None
            )

        if target == "occupation":
            match = re.search(
                r"(?:^|[,;])\s*"
                r"((?:desk|office|field|home)\s+job|"
                r"(?:my\s+)?job\s+(?:is|as)\s+[^,;]+|"
                r"(?:i\s+)?work(?:\s+as)?\s+[^,;]+|"
                r"occupation\s+is\s+[^,;]+)",
                normalized,
            )

            if match:
                value = match.group(1).strip()

                value = re.sub(
                    r"^(?:my\s+job\s+is|job\s+is|job\s+as|"
                    r"i\s+work\s+as|i\s+work|occupation\s+is)\s+",
                    "",
                    value,
                ).strip()

                return value

            if "desk job" in normalized:
                return "desk job"

        if target == "diet":
            match = re.search(
                r"(?:i\s+eat|my\s+diet\s+is|my\s+usual\s+diet\s+is|"
                r"meals?\s+(?:are|include))\s+([^,;]+)",
                normalized,
            )

            if match:
                return match.group(1).strip()

            if any(
                term in normalized
                for term in TARGET_TERM_HINTS["diet"]
            ):
                for marker in (
                    "roti",
                    "rice",
                    "potato",
                    "vegetable",
                    "food",
                ):
                    if marker in normalized:
                        start = normalized.find(
                            marker
                        )

                        positions = [
                            position
                            for position in (
                                normalized.find(
                                    ",",
                                    start,
                                ),
                                normalized.find(
                                    ";",
                                    start,
                                ),
                            )
                            if position >= 0
                        ]

                        end = min(
                            positions
                            or [len(normalized)]
                        )

                        return normalized[
                            start:end
                        ].strip()

        if target == "sleep":
            match = re.search(
                r"\b(?:very good|good|poor|bad|normal|disturbed)"
                r"\s+sleep(?:[^,;]*)",
                normalized,
            )

            if match:
                return match.group(0).strip()

            match = re.search(
                r"\bsleep(?:\s+pattern)?\s+(?:is|of)?\s*"
                r"([^,;]+)",
                normalized,
            )

            if match:
                return match.group(1).strip()

        if target == "physical_activity":
            match = re.search(
                r"\b(?:not much|very little|little|no|high|low|regular|daily)\s+"
                r"(?:physical\s+activity|exercise)(?:[^,;]*)",
                normalized,
            )

            if match:
                return match.group(0).strip()

            match = re.search(
                r"\b(?:physical\s+activity|exercise|activity)\s+"
                r"(?:is|includes|involves)?\s*"
                r"([^,;]+)",
                normalized,
            )

            if match:
                return match.group(1).strip()

        terms = TARGET_TERM_HINTS.get(
            target,
            (),
        )

        if any(
            term in normalized
            for term in terms
        ):
            return text

        return None

    def _cross_section_facts(
        self,
        text: str,
        state: InterviewState,
        turn_id: str | None,
    ) -> list[dict[str, Any]]:
        normalized = text.lower()
        facts: list[dict[str, Any]] = []

        if state.current_section == "hpi":
            severity = re.search(
                r"\b(10|[0-9])\s*"
                r"(?:/|out of|में से)\s*10\b",
                normalized,
            )

            if severity:
                facts.append(
                    self._fact(
                        "hpi",
                        "severity",
                        int(
                            severity.group(1)
                        ),
                        text,
                        turn_id,
                    )
                )

            duration = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple|a few)\s+"
                r"(day|days|hour|hours|week|weeks|month|months|year|years)\b",
                normalized,
            )

            if duration:
                facts.append(
                    self._fact(
                        "hpi",
                        "duration",
                        (
                            f"{duration.group(1)} "
                            f"{duration.group(2)}"
                        ),
                        text,
                        turn_id,
                    )
                )

            topic = self.detect_topic(
                text
            )

            if topic in {
                "gastrointestinal",
                "constipation",
                "diarrhea",
            }:
                bowel_value = (
                    "constipation"
                    if (
                        "constip" in normalized
                        or "कब्ज" in normalized
                    )
                    else (
                        "diarrhea"
                        if (
                            "diarr" in normalized
                            or "loose stool" in normalized
                            or "दस्त" in normalized
                        )
                        else "gastrointestinal"
                    )
                )

                facts.append(
                    self._fact(
                        "hpi",
                        "bowel_changes",
                        bowel_value,
                        text,
                        turn_id,
                    )
                )

            for field in (
                "stool_consistency",
                "straining",
                "blood_in_stool",
                "abdominal_distension",
                "nausea_vomiting",
                "breathing_difficulty",
                "cough",
                "wheeze",
                "fever",
                "urinary_frequency",
                "urinary_burning",
                "urinary_blood",
            ):
                negative = self._target_negative(
                    field,
                    normalized,
                )

                value = self._bundle_target_value(
                    field,
                    normalized,
                    negative,
                )

                if value is not None:
                    facts.append(
                        self._fact(
                            "hpi",
                            field,
                            value,
                            text,
                            turn_id,
                            value is False
                            and negative,
                        )
                    )

            for field in (
                "course",
                "site",
                "laterality",
                "character",
                "timing",
                "frequency",
                "aggravating_factors",
                "relieving_factors",
                "radiation",
                "associated_symptoms",
                "previous_episodes",
                "prior_treatment",
                "response_to_treatment",
                "prior_investigations",
                "impact_on_daily_life",
            ):
                negative = self._target_negative(
                    field,
                    normalized,
                )

                value = self._bundle_target_value(
                    field,
                    normalized,
                    negative,
                )

                if value is not None:
                    facts.append(
                        self._fact(
                            "hpi",
                            field,
                            value,
                            text,
                            turn_id,
                            value is False
                            and negative,
                        )
                    )

        for field in (
            "past_medical_history",
            "past_surgical_history",
            "hospitalizations",
            "immunizations",
            "medications",
            "allergies",
            "adverse_drug_reactions",
            "family_history",
        ):
            negative = self._target_negative(
                field,
                normalized,
            )

            value = self._bundle_target_value(
                field,
                normalized,
                negative,
            )

            if value is not None:
                facts.append(
                    self._fact(
                        FIELD_PRIMARY_SECTION.get(
                            field,
                            "past_history",
                        ),
                        field,
                        value,
                        text,
                        turn_id,
                        value is False
                        and negative,
                    )
                )

        if state.current_section == "personal_history":
            for field in (
                "occupation",
                "diet",
                "sleep",
                "physical_activity",
                "smoking",
                "alcohol",
                "tobacco",
                "menstrual_history",
                "pregnancy_status",
                "sexual_history",
            ):
                negative = self._target_negative(
                    field,
                    normalized,
                )

                value = self._bundle_target_value(
                    field,
                    normalized,
                    negative,
                )

                if value is not None:
                    facts.append(
                        self._fact(
                            "personal_history",
                            field,
                            value,
                            text,
                            turn_id,
                            value is False
                            and negative,
                        )
                    )

        if state.current_section == "review_of_systems":
            for field in (
                "constitutional",
                "cardiovascular",
                "respiratory",
                "gastrointestinal",
                "genitourinary",
                "neurological",
                "musculoskeletal",
                "skin",
                "endocrine",
                "hematologic",
                "psychiatric",
            ):
                negative = self._target_negative(
                    field,
                    normalized,
                )

                value = self._bundle_target_value(
                    field,
                    normalized,
                    negative,
                )

                if value is not None:
                    facts.append(
                        self._fact(
                            "review_of_systems",
                            field,
                            value,
                            text,
                            turn_id,
                            value is False
                            and negative,
                        )
                    )

        return facts

    @staticmethod
    def _fact(
        section: str,
        field: str,
        value: Any,
        evidence: str,
        turn_id: str | None,
        negative: bool = False,
    ) -> dict[str, Any]:
        return {
            "section": section,
            "field": normalize_field_name(field),
            "value": value,
            "negative": negative,
            "evidence": evidence,
            "turn_id": turn_id,
        }

    @staticmethod
    def _dedupe(
        facts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen = set()

        for fact in facts:
            key = (
                fact.get("section"),
                fact.get("field"),
                json.dumps(
                    fact.get("value"),
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),
                bool(fact.get("negative")),
            )

            if key not in seen:
                seen.add(key)
                result.append(fact)

        return result

    @staticmethod
    def _complaint_from_topic(
        topic: str,
    ) -> str:
        return topic.replace(
            "_",
            " ",
        )

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        return re.sub(
            r"[,.!?।]+",
            "",
            text.strip().lower(),
        )

    def _candidate_urls(self) -> list[str]:
        configured = self.url.rstrip("/")
        urls = [configured]

        for old, new in (
            (
                "/api/v1/",
                "/v1/",
            ),
            (
                "/v1/",
                "/api/v1/",
            ),
        ):
            if old in configured:
                alt = configured.replace(
                    old,
                    new,
                    1,
                )

                if alt not in urls:
                    urls.append(alt)

        return urls

    @staticmethod
    def _emergency_question(
        section: str,
        language: str,
    ) -> str:
        return (
            "कृपया अपनी स्वास्थ्य समस्या के बारे में थोड़ा और बताइए?"
            if language == "hi"
            else "Could you tell me a little more about your health problem?"
        )

    @staticmethod
    def _emergency_question_for_target(
        target: str,
        language: str,
    ) -> str:
        raw_target = (
            target[7:]
            if target.startswith("bundle:")
            else target
        )

        first = (
            raw_target.split(
                ",",
                1,
            )[0].strip()
        )

        description = (
            TARGET_DESCRIPTIONS.get(
                first,
                {},
            ).get(language)
            or TARGET_DESCRIPTIONS.get(
                first,
                {},
            ).get("en")
            or first.replace(
                "_",
                " ",
            )
        )

        return (
            f"कृपया {description} के बारे में बताइए?"
            if language == "hi"
            else f"Could you tell me about {description}?"
        )
