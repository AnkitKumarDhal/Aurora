from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from backend.ai.interview.state import (
    FIELD_PRIMARY_SECTION,
    TARGET_DESCRIPTIONS,
    TARGET_FIELDS,
    InterviewState,
    normalize_field_name,
)
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
        "bloating",
        "bloated",
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
        "dizziness",
        "fainting",
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

UNKNOWN_ANSWERS = {
    "i don't know",
    "i do not know",
    "don't know",
    "do not know",
    "not sure",
    "not certain",
    "unknown",
    "not known",
    "not available",
    "pata nahi",
    "pata nahin",
    "पता नहीं",
    "मुझे नहीं पता",
    "मालूम नहीं",
    "नहीं पता",
    "i haven't been assessed",
    "i have not been assessed",
    "never had an ayush assessment",
    "never had an ayurvedic assessment",
    "कोई आयुष जांच नहीं हुई",
    "कोई आयुष मूल्यांकन नहीं हुआ",
    "आयुर्वेदिक जांच नहीं हुई",
    "आयुर्वेदिक मूल्यांकन नहीं हुआ",
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
        "radiation",
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
        "family_history",
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
    ),
    (
        "ayush_prakriti",
        "ayush_vikriti",
        "ayush_sara",
        "ayush_samhanana",
    ),
    (
        "ayush_pramana",
        "ayush_satmya",
        "ayush_satva",
    ),
    (
        "ayush_ahara_shakti",
        "ayush_vyayama_shakti",
        "ayush_vaya",
    ),
    (
        "ayush_ahara_vihara",
        "ayush_agni",
        "ayush_koshta",
    ),
    (
        "ayush_nidana",
        "ayush_samprapti",
    ),
)

BOOLEAN_TARGETS = {
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

NEGATABLE_TARGETS = BOOLEAN_TARGETS | {
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
    "nausea_vomiting",
    "previous_episodes",
    "prior_investigations",
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
}

BOOLEAN_TERMS = {
    "straining": (
        "strain",
        "straining",
        "push hard",
        "जोर लगाना",
        "जोर",
    ),
    "blood_in_stool": (
        "blood in stool",
        "blood in stools",
        "blood while passing stool",
        "rectal bleeding",
        "blood",
        "bleeding",
        "मल में खून",
    ),
    "abdominal_distension": (
        "bloating",
        "bloated",
        "abdominal distension",
        "abdominal swelling",
        "stomach bloating",
        "पेट फूल",
        "सूजन",
    ),
    "breathing_difficulty": (
        "shortness of breath",
        "difficulty breathing",
        "trouble breathing",
        "cannot breathe",
        "can't breathe",
        "breathless",
        "breathing problem",
        "सांस लेने में दिक्कत",
        "साँस लेने में दिक्कत",
    ),
    "wheeze": (
        "wheeze",
        "wheezing",
        "घरघराहट",
    ),
    "fever": (
        "fever",
        "temperature",
        "chills",
        "बुखार",
    ),
    "urinary_burning": (
        "burning while urinating",
        "burning during urination",
        "painful urination",
        "burning urine",
        "पेशाब में जलन",
    ),
    "urinary_blood": (
        "blood in urine",
        "blood in my urine",
        "पेशाब में खून",
    ),
    "smoking": (
        "smoke",
        "smoking",
        "cigarette",
        "cigarettes",
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
        "paan masala",
        "तंबाकू",
    ),
}

AYUSH_TARGET_TERMS = {
    "ayush_prakriti": (
        "prakriti",
        "constitution",
        "vata",
        "pitta",
        "kapha",
        "वात",
        "पित्त",
        "कफ",
        "प्रकृति",
    ),
    "ayush_vikriti": (
        "vikriti",
        "imbalance",
        "dosha imbalance",
        "विकृति",
        "असंतुलन",
        "दोष असंतुलन",
    ),
    "ayush_sara": ("sara", "सार"),
    "ayush_samhanana": ("samhanana", "संहनन"),
    "ayush_pramana": ("pramana", "प्रमाण"),
    "ayush_satmya": ("satmya", "सात्म्य"),
    "ayush_satva": ("satva", "sattva", "सत्त्व"),
    "ayush_ahara_shakti": ("ahara shakti", "आहार शक्ति"),
    "ayush_vyayama_shakti": ("vyayama shakti", "व्यायाम शक्ति"),
    "ayush_vaya": ("vaya", "age", "वय", "उम्र"),
    "ayush_ahara_vihara": (
        "ahara-vihara",
        "ahara vihara",
        "daily routine",
        "आहार",
        "विहार",
        "दैनिक दिनचर्या",
    ),
    "ayush_agni": ("agni", "digestion", "अग्नि", "पाचन"),
    "ayush_koshta": ("koshta", "koshtha", "bowel pattern", "कोष्ठ"),
    "ayush_nidana": ("nidana", "cause", "causes", "निदान", "कारण"),
    "ayush_samprapti": (
        "samprapti",
        "how the problem developed",
        "सम्प्राप्ति",
        "समप्राप्ति",
    ),
}

TEXT_TARGET_TERMS = {
    "nausea_vomiting": (
        "nausea",
        "nauseous",
        "vomit",
        "vomiting",
        "मतली",
        "उल्टी",
    ),
    "previous_episodes": (
        "before",
        "previously",
        "ever had this",
        "happened before",
        "first time",
        "पहले",
    ),
    "prior_treatment": (
        "medicine",
        "medication",
        "medicine from",
        "pharmacist",
        "treatment",
        "remedy",
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
        "worked for",
    ),
    "prior_investigations": (
        "test",
        "tests",
        "scan",
        "x-ray",
        "xray",
        "ultrasound",
        "investigation",
        "investigations",
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
        "मधुमेह",
        "ब्लड प्रेशर",
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
        "supplement",
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
        "family history",
        "runs in my family",
        "my father",
        "my mother",
        "my brother",
        "my sister",
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
        "meal",
        "meals",
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
        "walking",
        "gym",
        "active",
        "व्यायाम",
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
}

ROS_TERMS = {
    "constitutional": (
        "fever",
        "chills",
        "fatigue",
        "tired",
        "weight loss",
        "weight gain",
        "appetite",
    ),
    "cardiovascular": (
        "chest pain",
        "palpitation",
        "palpitations",
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
    ) -> QuestionDecision:
        candidates = state.candidate_targets()

        if not candidates:
            return QuestionDecision(
                self._emergency_question(
                    state.current_section,
                    language,
                ),
                None,
                False,
            )

        if (
            not self.enabled
            or self.provider != "lemonade"
        ):
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
                and self._question_key(
                    decision.question
                )
                not in {
                    self._question_key(item)
                    for item in state.question_history
                }
                and all(
                    not state.target_answered(item)
                    for item in state._split_targets(
                        decision.target
                    )
                    if item
                )
            ):
                return decision

        except InterviewModelError as exc:
            self._debug(
                "QUESTION_FAILURE",
                session_id=session_id,
                error_type=type(exc).__name__,
                error=str(exc),
            )

        seen_questions = {
            self._question_key(item)
            for item in state.question_history
        }

        for bundle in QUESTION_BUNDLES:
            available = [
                target
                for target in bundle
                if target in candidates
            ]

            if len(available) < 2:
                continue

            # Keep fallback questions clinically narrow and voice-friendly.
            fallback_question = (
                self._emergency_question_for_bundle(
                    available[:4],
                    language,
                )
            )

            if (
                fallback_question
                and self._question_key(
                    fallback_question
                ) not in seen_questions
            ):
                return QuestionDecision(
                    fallback_question,
                    "bundle:" + ",".join(available[:4]),
                    False,
                )

        for target in candidates:
            fallback_question = (
                self._emergency_question_for_target(
                    target,
                    language,
                )
            )

            if self._question_key(
                fallback_question
            ) not in seen_questions:
                return QuestionDecision(
                    fallback_question,
                    target,
                    False,
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
        topic = self.detect_topic(
            normalized
        )

        known = state.known_fields()

        if (
            "chief_complaint" not in known
            and normalized
        ):
            facts.append(
                self._fact(
                    "hpi",
                    "chief_complaint",
                    normalized,
                    normalized,
                    turn_id,
                )
            )

        if topic:
            facts.append(
                self._fact(
                    "hpi",
                    "chief_complaint",
                    normalized,
                    normalized,
                    turn_id,
                )
            )

        if (
            topic
            and (
                not state.topic
                or state.topic == "general"
            )
        ):
            state.topic = topic

        pending_targets = (
            state._split_targets(
                state.pending_target
            )
        )

        if self.is_unknown_answer(
            normalized
        ):
            for target in pending_targets:
                facts.append(
                    self._fact(
                        FIELD_PRIMARY_SECTION.get(
                            target,
                            state.current_section,
                        ),
                        target,
                        "unknown",
                        normalized,
                        turn_id,
                    )
                )

        elif self.is_negative_answer(
            normalized
        ):
            for target in pending_targets:
                if target in NEGATABLE_TARGETS:
                    facts.append(
                        self._fact(
                            FIELD_PRIMARY_SECTION.get(
                                target,
                                state.current_section,
                            ),
                            target,
                            False,
                            normalized,
                            turn_id,
                            True,
                        )
                    )

        for target in TARGET_FIELDS:
            if target == "chief_complaint":
                continue

            value, negative = self._extract_target(
                target,
                normalized,
            )

            if value is None:
                continue

            facts.append(
                self._fact(
                    FIELD_PRIMARY_SECTION.get(
                        target,
                        state.current_section,
                    ),
                    target,
                    value,
                    normalized,
                    turn_id,
                    negative,
                )
            )

        extracted_targets = {
            str(fact.get("field") or "")
            for fact in facts
        }

        # Preserve natural, context-rich answers when one target is pending.
        # This catches answers such as "teacher", "six hours", "Vata", or
        # "since last night" even when no keyword extractor has a rule for it.
        if (
            len(pending_targets) == 1
            and pending_targets[0] not in extracted_targets
            and self._can_context_capture(
                pending_targets[0],
                normalized,
            )
        ):
            target = pending_targets[0]
            facts.append(
                self._fact(
                    FIELD_PRIMARY_SECTION.get(
                        target,
                        state.current_section,
                    ),
                    target,
                    normalized,
                    normalized,
                    turn_id,
                )
            )

        facts.extend(
            self._cross_section_facts(
                normalized,
                state,
                turn_id,
            )
        )

        return self._dedupe(
            facts
        )

    @staticmethod
    def is_unknown_answer(
        text: str,
    ) -> bool:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        return normalized in UNKNOWN_ANSWERS

    @staticmethod
    def is_negative_answer(
        text: str,
        text: str,
    ) -> bool:
        normalized = InterviewExtractor._normalize_text(
            text
        )

        if (
            normalized in NEGATIVE_ANSWERS
            or "nothing else" in normalized
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
    def detect_topic(
        text: str,
    ) -> str | None:
        normalized = text.lower()

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(
                keyword in normalized
                for keyword in keywords
            ):
                return topic

        return None

    def _extract_target(
        self,
        target: str,
        text: str,
    ) -> tuple[Any, bool]:
        normalized = text.lower()

        if target in AYUSH_TARGET_TERMS:
            terms = AYUSH_TARGET_TERMS[target]

            if any(
                term in normalized
                for term in terms
            ):
                return (
                    text.strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "severity":
            patterns = (
                r"\b(10|[0-9])\s*(?:/|out of|में से)?\s*10\b",
                r"^\s*(10|[0-9])\s*$",
                r"\b(?:pain|severity|discomfort)\s*(?:is|of|at)?\s*(10|[0-9])\b",
                r"\b(?:तीव्रता|दर्द|तकलीफ|तकलीफ़)\s*(?:\S+\s*){0,3}(10|[0-9])\b",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    return (
                        int(
                            match.group(1)
                        ),
                        False,
                    )

            return (
                None,
                False,
            )

        if target in {
            "onset",
            "duration",
        }:
            temporal = self._extract_temporal_answer(
                normalized
            )

            if temporal:
                return (
                    temporal,
                    False,
                )

            match = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple|a few)\s+"
                r"(day|days|hour|hours|week|weeks|month|months|year|years)\b",
                normalized,
            )

            if match:
                return (
                    f"{match.group(1)} {match.group(2)}",
                    False,
                )

            match = re.search(
                r"\b(?:started|began|since|for)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return (
                    match.group(1).strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "course":
            if re.search(
                r"\b(?:same|unchanged|no change|stable)\b",
                normalized,
            ):
                return (
                    "unchanged",
                    False,
                )

            if re.search(
                r"\b(?:worse|worsening|getting worse)\b",
                normalized,
            ):
                return (
                    "worsening",
                    False,
                )

            if re.search(
                r"\b(?:better|improving|getting better)\b",
                normalized,
            ):
                return (
                    "improving",
                    False,
                )

            return (
                None,
                False,
            )

        if target == "site":
            patterns = (
                r"\b(?:in|at|around|below|above|near)\s+"
                r"([^,.!?;]+)",
                r"\b(lower abdomen|upper abdomen|abdomen|stomach|chest|head|back|neck|throat|arm|leg)\b",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    return (
                        match.group(1).strip(),
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "laterality":
            if (
                "both sides" in normalized
                or "दोनों तरफ" in normalized
                or "दोनों तरफ़" in normalized
            ):
                return (
                    "both",
                    False,
                )

            if re.search(
                r"\bleft\b|\bबायां\b|\bबायाँ\b",
                normalized,
            ):
                return (
                    "left",
                    False,
                )

            if re.search(
                r"\bright\b|\bदायां\b|\bदायाँ\b",
                normalized,
            ):
                return (
                    "right",
                    False,
                )

            return (
                None,
                False,
            )

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
                "जलन",
                "दबाव",
                "जकड़न",
                "चुभने",
                "चुभता",
                "धड़कता",
                "तेज",
                "तेज़",
                "भारी",
                "ऐंठन",
                "मरोड़",
            ):
                if value in normalized:
                    return (
                        value,
                        False,
                    )

            match = re.search(
                r"\b(?:feels like|feel like|feels as if|like)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return (
                    match.group(1).strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "timing":
            if any(
                value in normalized
                for value in (
                    "constant",
                    "all the time",
                    "nonstop",
                    "continuous",
                    "throughout the day",
                    "throughout",
                    "लगातार",
                    "हर समय",
                    "पूरे दिन",
                )
            ):
                return (
                    "constant",
                    False,
                )

            if any(
                value in normalized
                for value in (
                    "comes and goes",
                    "on and off",
                    "intermittent",
                    "आता जाता",
                    "आता-जाता",
                    "बीच-बीच में",
                    "कभी-कभी",
                )
            ):
                return (
                    "intermittent",
                    False,
                )

            if any(
                value in normalized
                for value in (
                    "morning",
                    "afternoon",
                    "evening",
                    "night",
                    "सुबह",
                    "दोपहर",
                    "शाम",
                    "रात",
                )
            ):
                return (
                    normalized,
                    False,
                )

            return (
                None,
                False,
            )

        if target in {
            "frequency",
            "bowel_frequency",
            "urinary_frequency",
        }:
            match = re.search(
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:times?|bowel movements?|motions?)"
                r"(?:\s*(?:a|per)\s*)?"
                r"(?:day|week|month)?\b",
                normalized,
            )

            if not match:
                match = re.search(
                    r"\b(?:दिन में|हर दिन|रोज़|रोज)\s*\d+\s*(?:बार|बारी)\b",
                    normalized,
                )

            if match:
                return (
                    match.group(0).strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "stool_consistency":
            for value in (
                "very hard",
                "hard",
                "loose",
                "watery",
                "soft",
                "normal",
                "सख्त",
                "ढीला",
                "पानी जैसा",
            ):
                if value in normalized:
                    return (
                        value,
                        False,
                    )

            return (
                None,
                False,
            )

        if target in BOOLEAN_TARGETS:
            terms = BOOLEAN_TERMS.get(
                target,
                (),
            )

            for term in terms:
                position = normalized.find(
                    term
                )

                if position < 0:
                    continue

                prefix = normalized[
                    max(
                        0,
                        position - 45,
                    ):position
                ]

                negative = bool(
                    re.search(
                        r"\b(?:no|not|never|without|don't|do not|denies|none)\b",
                        prefix,
                    )
                ) or "नहीं" in prefix

                return (
                    False if negative else True,
                    negative,
                )

            return (
                None,
                False,
            )

        if target == "nausea_vomiting":
            terms = TEXT_TARGET_TERMS[
                "nausea_vomiting"
            ]

            if any(
                term in normalized
                for term in terms
            ):
                negative = (
                    "no nausea" in normalized
                    or "no vomiting" in normalized
                    or "no vomit" in normalized
                    or "not nauseous" in normalized
                    or "no nausea or vomiting"
                    in normalized
                    or "मतली नहीं" in normalized
                    or "उल्टी नहीं" in normalized
                )

                return (
                    False if negative else text,
                    negative,
                )

            return (
                None,
                False,
            )

        if target == "bowel_changes":
            if any(
                term in normalized
                for term in (
                    "constipation",
                    "constipated",
                    "कब्ज",
                )
            ):
                return (
                    "constipation",
                    False,
                )

            if any(
                term in normalized
                for term in (
                    "diarrhea",
                    "loose stools",
                    "loose motions",
                    "दस्त",
                )
            ):
                return (
                    "diarrhea",
                    False,
                )

            return (
                None,
                False,
            )

        if target == "aggravating_factors":
            patterns = (
                r"\b(?:makes|make|made|makes it)\s+worse\b",
                r"\bworse when\b([^,.!?;]+)",
                r"\bworse with\b([^,.!?;]+)",
                r"\bgets worse when\b([^,.!?;]+)",
                r"\bgets worse with\b([^,.!?;]+)",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    value = (
                        match.group(1).strip()
                        if match.lastindex
                        else "reported"
                    )

                    return (
                        value,
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "relieving_factors":
            patterns = (
                r"\b(?:makes|make|made|makes it)\s+better\b",
                r"\bbetter when\b([^,.!?;]+)",
                r"\bbetter with\b([^,.!?;]+)",
                r"\bgets better when\b([^,.!?;]+)",
                r"\bgets better with\b([^,.!?;]+)",
                r"\bhelps\b([^,.!?;]*)",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    value = (
                        match.group(1).strip()
                        if match.lastindex
                        else "reported"
                    )

                    return (
                        value,
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "occupation":
            match = re.search(
                r"\b(?:desk job|office job|works? as|work as|job is|occupation is)\s*"
                r"([^,.!?;]*)",
                normalized,
            )

            if match:
                value = match.group(0).strip()
                return (
                    value,
                    False,
                )

            return (
                None,
                False,
            )

        if target == "diet":
            match = re.search(
                r"\b(?:i eat|my diet is|my usual diet is|diet consists of)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return (
                    match.group(1).strip(),
                    False,
                )

            if any(
                term in normalized
                for term in (
                    "roti",
                    "rice",
                    "potato",
                    "vegetable",
                    "meals",
                )
            ):
                return (
                    normalized,
                    False,
                )

            return (
                None,
                False,
            )

        if target == "sleep":
            if re.search(
                r"\b(?:very good|good|poor|bad|normal|disturbed)\s+sleep\b",
                normalized,
            ):
                return (
                    normalized,
                    False,
                )

            return (
                None,
                False,
            )

        if target == "physical_activity":
            if any(
                term in normalized
                for term in (
                    "not much",
                    "very little",
                    "little exercise",
                    "no exercise",
                    "physical activity",
                    "exercise",
                    "walking",
                    "gym",
                    "active",
                    "व्यायाम",
                )
            ):
                return (
                    normalized,
                    False,
                )

            return (
                None,
                False,
            )

        if target in TEXT_TARGET_TERMS:
            terms = TEXT_TARGET_TERMS[
                target
            ]

            if any(
                term in normalized
                for term in terms
            ):
                negative = False

                if target == "previous_episodes":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "never had this before",
                            "never experienced this before",
                            "first time",
                            "no previous episodes",
                            "has never happened before",
                        )
                    )

                elif target == "prior_investigations":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "no tests",
                            "no test",
                            "no investigations",
                            "no scans",
                            "have not had any tests",
                            "never had any tests",
                        )
                    )

                elif target == "past_medical_history":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "no medical conditions",
                            "no medical condition",
                            "no major medical conditions",
                            "no past medical history",
                            "no history of",
                        )
                    )

                elif target == "past_surgical_history":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "never had surgery",
                            "never had any surgery",
                            "no surgery",
                            "no surgeries",
                            "no operations",
                        )
                    )

                elif target == "hospitalizations":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "never been admitted",
                            "never admitted",
                            "never hospitalized",
                            "no hospital admissions",
                            "never stayed in a hospital",
                        )
                    )

                elif target == "medications":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "not taking any",
                            "no regular medicines",
                            "no regular medications",
                            "not on any medication",
                        )
                    )

                elif target == "allergies":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "no allergies",
                            "no known allergies",
                            "no known allergy",
                            "not allergic",
                        )
                    )

                elif target == "family_history":
                    negative = any(
                        phrase in normalized
                        for phrase in (
                            "no family history",
                            "no known family history",
                            "nothing runs in my family",
                            "no family history of",
                        )
                    )

                return (
                    False if negative else text,
                    negative,
                )

            return (
                None,
                False,
            )

        return (
            None,
            False,
        )

    @staticmethod
    def _extract_temporal_answer(
        text: str,
    ) -> str | None:
        normalized = text.strip().lower()

        patterns = (
            r"\b(?:the\s+)?day\s+before\s+yesterday\b",
            r"\b(?:yesterday|today|tonight|last\s+night|this\s+morning|this\s+afternoon|this\s+evening|yesterday\s+morning|yesterday\s+afternoon|yesterday\s+evening|last\s+week|this\s+week|last\s+month|this\s+month|last\s+year|this\s+year)\b",
            r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+couple(?:\s+of)?|a\s+few)\s+(?:second|seconds|minute|minutes|hour|hours|day|days|night|nights|week|weeks|month|months|year|years)\s+ago\b",
            r"\b(?:since|from|starting\s+from)\s+(?:the\s+)?(?:day\s+before\s+yesterday|yesterday|today|tonight|last\s+night|this\s+morning|last\s+week|last\s+month|last\s+year)\b",
            r"\b(?:since|from|starting\s+from)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+couple(?:\s+of)?|a\s+few)\s+(?:second|seconds|minute|minutes|hour|hours|day|days|night|nights|week|weeks|month|months|year|years)\s+(?:ago|back)\b",
            r"(?:आज\s+(?:सुबह|दोपहर|शाम)|आज|कल\s+(?:सुबह|दोपहर|शाम|रात)|कल|परसों|पिछले\s+(?:हफ्ते|सप्ताह|महीने|साल)|इस\s+(?:हफ्ते|सप्ताह|महीने|साल))",
            r"(?:\d+|एक|दो|तीन|चार|पाँच|पांच|छह|छः|सात|आठ|नौ|दस|कुछ)\s+(?:से\s+)?(?:दिन|दिनों|हफ्ते|सप्ताह|महीने|साल)\s+(?:पहले|पूर्व)",
            r"(?:एक|दो|तीन|चार|पाँच|पांच|छह|छः|सात|आठ|नौ|दस|कुछ)\s+(?:दिन|दिनों|हफ्ते|सप्ताह|महीने|साल)\s+से",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0).strip()

        return None

    @staticmethod
    def _can_context_capture(
        target: str,
        text: str,
    ) -> bool:
        if (
            not target
            or target == "chief_complaint"
            or target in BOOLEAN_TARGETS
        ):
            return False

        normalized = InterviewExtractor._normalize_text(
            text
        )

        if normalized in {
            "yes",
            "y",
            "yeah",
            "yep",
            "haan",
            "हाँ",
            "हां",
            "no",
            "n",
            "nope",
            "none",
            "नहीं",
            "कोई नहीं",
        }:
            return False

        if (
            not normalized
            or "?" in normalized
            or len(normalized) < 2
        ):
            return False

        return True

    def _cross_section_facts(
        self,
        text: str,
        state: InterviewState,
        turn_id: str | None,
    ) -> list[dict[str, Any]]:
        normalized = text.lower()
        facts: list[
            dict[str, Any]
        ] = []

        for field, terms in ROS_TERMS.items():
            matched = False
            negative = False

            for term in terms:
                position = normalized.find(
                    term
                )

                if position < 0:
                    continue

                matched = True

                prefix = normalized[
                    max(
                        0,
                        position - 40,
                    ):position
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
                    negative = False

                break

            if not matched:
                continue

            facts.append(
                self._fact(
                    "review_of_systems",
                    field,
                    False
                    if negative
                    else text,
                    text,
                    turn_id,
                    negative,
                )
            )

        return facts

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
            "max_tokens": 128,
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
                        in {
                            400,
                            404,
                            422,
                        }
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
                    (
                        time.monotonic()
                        - started
                    )
                    * 1000,
                    2,
                )

                choices = (
                    body.get(
                        "choices"
                    )
                    if isinstance(
                        body,
                        dict,
                    )
                    else None
                )

                if (
                    not isinstance(
                        choices,
                        list,
                    )
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

                if isinstance(
                    content,
                    list,
                ):
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
    ) -> str:
        recent = conversation[-6:]
        known = state.known_fields()

        candidate_text = "\n".join(
            f"- {item}: "
            f"{TARGET_DESCRIPTIONS.get(item, {}).get(
                language, item.replace('_', ' '))}"
            for item in candidates
        )

        bundle_text = "\n".join(
            f"- {','.join(bundle)}"
            for bundle in QUESTION_BUNDLES
            if len(
                set(bundle)
                & set(candidates)
            )
            >= 2
        )

        return (
            f"Language: {language}\n"
            f"Current section: {state.current_section}\n"
            f"Clinical topic: {state.topic}\n"
            f"Known facts: "
            f"{json.dumps(known, ensure_ascii=False, default=str)}\n"
            f"Recent questions: "
            f"{json.dumps(state.question_history[-5:], ensure_ascii=False)}\n"
            f"Recent conversation: "
            f"{json.dumps(recent, ensure_ascii=False, default=str)}\n"
            f"Allowed targets:\n{candidate_text}\n"
            f"Useful same-section bundles:\n{bundle_text}\n"
            "Ask only for information that is still missing from the known facts. "
            "Never repeat information already stated by the patient. "
            "Ask one natural question that can collect multiple closely related targets in one patient response. "
            "Prefer high-yield clinical information over exhaustive checklist completion. "
            "For HPI, prioritize severity, location, timing, associated symptoms, and treatment history when still missing. "
            "For past history, combine medical conditions, surgery, hospitalizations, and immunization history. "
            "For drug history, combine medicines, allergies, and adverse reactions. "
            "For personal history, combine occupation, diet, sleep, activity, smoking, alcohol, and tobacco where appropriate. "
            "For review of systems, use a broad symptom screen rather than one symptom at a time. "
            "For AYUSH, ask only for patient-reported or previously documented information. "
            "Never infer Prakriti, Vikriti, or any other AYUSH assessment. "
            "If the patient does not know an AYUSH term or has never had such an assessment, accept that answer and continue. "
            "Do not ask a section-closure question. "
            "Do not diagnose. "
            "Do not recommend treatment. "
            "Do not explain results. "
            "Return exactly two lines and nothing else:\n"
            "TARGETS: <target1,target2,...>\n"
            "QUESTION: <question>"
        )

    @staticmethod
    def _parse_question(
        content: str,
        candidates: list[str],
    ) -> QuestionDecision:
        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.IGNORECASE
            | re.DOTALL,
        ).strip()

        target_match = re.search(
            r"(?:^|\n)\s*TARGETS?\s*:\s*([^\n]+)",
            cleaned,
            flags=re.IGNORECASE,
        )

        question_match = re.search(
            r"(?:^|\n)\s*QUESTION\s*:\s*(.+)",
            cleaned,
            flags=re.IGNORECASE
            | re.DOTALL,
        )

        raw_targets = (
            target_match.group(1)
            .strip()
            .strip("`\"'")
            if target_match
            else ""
        )

        raw_targets = re.sub(
            r"^bundle\s*:\s*",
            "",
            raw_targets,
            flags=re.IGNORECASE,
        )

        targets = list(
            dict.fromkeys(
                item.strip().lower()
                for item in re.split(
                    r"[,|;/]+|\band\b",
                    raw_targets,
                    flags=re.IGNORECASE,
                )
                if item.strip()
            )
        )

        if not targets and len(
            candidates
        ) == 1:
            targets = [
                candidates[0]
            ]

        if (
            not targets
            or len(targets) > 4
            or any(
                item not in candidates
                for item in targets
            )
        ):
            return QuestionDecision(
                "",
                None,
                True,
            )

        if len(targets) > 1:
            if not any(
                set(targets).issubset(
                    set(bundle)
                )
                for bundle in QUESTION_BUNDLES
            ):
                return QuestionDecision(
                    "",
                    None,
                    True,
                )

            target = (
                "bundle:"
                + ",".join(targets)
            )
        else:
            target = targets[0]

        question = (
            question_match.group(1).strip()
            if question_match
            else InterviewExtractor._extract_question_line(
                cleaned
            )
        )

        question = re.sub(
            r"^[-*\d.)\s]+",
            "",
            question,
        ).strip().strip(
            '"'
        )

        question = re.sub(
            r"\s+",
            " ",
            question,
        )

        question = re.split(
            r"\n(?:TARGETS?|QUESTION)\s*:",
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

        if not InterviewExtractor._valid_question(
            question
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

        return (
            lines[-1]
            if lines
            else ""
        )

    @staticmethod
    def _question_key(
        question: str,
    ) -> str:
        value = question.strip().lower()
        value = re.sub(
            r"[^a-z0-9\u0900-\u097f]+",
            " ",
            value,
            flags=re.IGNORECASE,
        )
        return " ".join(
            value.split()
        )

    @staticmethod
    def _valid_question(
        question: str,
    ) -> bool:
        if (
            len(question) < 8
            or len(question) > 320
        ):
            return False

        lower = question.lower()

        return not any(
            marker in lower
            for marker in (
                "target:",
                "targets:",
                "question:",
                "```",
                "{",
                "}",
            )
        )

    def _candidate_urls(
        self,
    ) -> list[str]:
        configured = (
            self.url.rstrip("/")
        )

        urls = [
            configured
        ]

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
                    urls.append(
                        alt
                    )

        return urls

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are Aurora's clinical history-taking interviewer. "
            "Your job is to collect concise, clinically useful history before a clinician consultation. "
            "Follow the required order HPI, past medical and surgical history, drug and allergy history, "
            "family history, personal history, review of systems, and AYUSH history only when enabled. "
            "The patient's previous answers are already recorded. "
            "Never ask again for facts that are already explicitly present. "
            "Prefer one broad high-yield question over several narrow questions. "
            "Questions must be natural, short, respectful, and answerable by voice or text. "
            "Do not diagnose, reassure, prescribe, or recommend treatment."
        )

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
            "field": normalize_field_name(
                field
            ),
            "value": value,
            "negative": negative,
            "evidence": evidence,
            "turn_id": turn_id,
        }

    @staticmethod
    def _dedupe(
        facts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result: list[
            dict[str, Any]
        ] = []

        seen = set()

        for fact in facts:
            key = (
                fact.get(
                    "section"
                ),
                fact.get(
                    "field"
                ),
                json.dumps(
                    fact.get(
                        "value"
                    ),
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),
                bool(
                    fact.get(
                        "negative"
                    )
                ),
            )

            if key not in seen:
                seen.add(
                    key
                )
                result.append(
                    fact
                )

        return result

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        return re.sub(
            r"[,.!?;।]+",
            "",
            text.strip().lower(),
        )

    @staticmethod
    def _complaint_from_topic(
        topic: str,
    ) -> str:
        return topic.replace(
            "_",
            " ",
        )

    @staticmethod
    def _emergency_question(
        section: str,
        language: str,
    ) -> str:
        if language == "hi":
            return "कृपया अपनी स्वास्थ्य समस्या के बारे में थोड़ा और बताइए?"

        return "Could you tell me a little more about your health problem?"

    @staticmethod
    def _emergency_question_for_bundle(
        targets: list[str],
        language: str,
    ) -> str:
        labels = [
            TARGET_DESCRIPTIONS.get(
                target,
                {},
            ).get(language)
            or TARGET_DESCRIPTIONS.get(
                target,
                {},
            ).get("en")
            or target.replace(
                "_",
                " ",
            )
            for target in targets
        ]

        if not labels:
            return ""

        if language == "hi":
            if len(labels) == 2:
                return (
                    f"कृपया {labels[0]} और {labels[1]} के बारे में बताइए?"
                )

            if len(labels) == 3:
                return (
                    f"कृपया {labels[0]}, {labels[1]} और {labels[2]} के बारे में बताइए?"
                )

            return (
                f"कृपया {', '.join(labels[:-1])} और {labels[-1]} के बारे में बताइए?"
            )

        if len(labels) == 2:
            return (
                f"Could you tell me about {labels[0]} and {labels[1]}?"
            )

        if len(labels) == 3:
            return (
                f"Could you tell me about {labels[0]}, {labels[1]}, and {labels[2]}?"
            )

        return (
            f"Could you tell me about {', '.join(labels[:-1])}, and {labels[-1]}?"
        )

    @staticmethod
    def _emergency_question_for_target(
        target: str,
        language: str,
    ) -> str:
        raw = (
            target[7:]
            if target.startswith(
                "bundle:"
            )
            else target
        )

        first = (
            raw.split(
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

        if language == "hi":
            return (
                f"कृपया {description} के बारे में बताइए?"
            )

        return (
            f"Could you tell me about {description}?"
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