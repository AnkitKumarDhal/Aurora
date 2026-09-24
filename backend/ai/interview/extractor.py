from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from backend.ai.interview.state import InterviewState, normalize_field_name
from backend.config import settings

TOPIC_KEYWORDS = {
    "chest_pain": ("chest pain", "chest pressure", "chest discomfort", "सीने में दर्द", "सीने में दबाव"),
    "headache": ("headache", "head pain", "migraine", "सिरदर्द", "सिर में दर्द", "माइग्रेन"),
    "respiratory": ("cough", "coughing", "breathless", "shortness of breath", "difficulty breathing", "breathing problem", "खांसी", "खाँसी", "सांस फूलना", "साँस फूलना"),
    "gastrointestinal": ("constipation", "constipated", "hard stool", "hard stools", "diarrhea", "loose stools", "loose motions", "stomach pain", "abdominal pain", "vomiting", "nausea", "कब्ज", "दस्त", "पेट में दर्द", "उल्टी", "मतली"),
    "urinary": ("urine", "urination", "burning while urinating", "painful urination", "पेशाब", "मूत्र", "पेशाब में जलन"),
    "skin": ("rash", "itching", "skin problem", "दाने", "चकत्ते", "खुजली", "त्वचा"),
    "musculoskeletal": ("back pain", "joint pain", "muscle pain", "neck pain", "कमर दर्द", "जोड़ों का दर्द"),
    "neurological": ("numbness", "tingling", "weakness", "सुन्नपन", "झनझनाहट", "कमजोरी", "कमज़ोरी"),
}

NEGATIVE_ANSWERS = {"no", "none", "nothing", "nothing else", "no more", "not applicable", "not relevant",
                    "i don't know", "i do not know", "na", "n/a", "नहीं", "कुछ नहीं", "और कुछ नहीं", "कोई नहीं", "लागू नहीं", "पता नहीं"}

TARGET_FIELD = {
    "chief_complaint": "chief_complaint", "onset": "onset", "duration": "duration", "course": "course", "site": "site", "laterality": "laterality", "severity": "severity", "character": "character", "timing": "timing", "frequency": "frequency", "aggravating_factors": "aggravating_factors", "relieving_factors": "relieving_factors", "radiation": "radiation", "associated_symptoms": "associated_symptoms", "previous_episodes": "previous_episodes", "prior_treatment": "prior_treatment", "response_to_treatment": "response_to_treatment", "prior_investigations": "prior_investigations", "impact_on_daily_life": "impact_on_daily_life", "breathing_difficulty": "breathing_difficulty", "nausea_vomiting": "nausea_vomiting", "vision_or_neuro": "vision_or_neuro", "cough": "cough", "wheeze": "wheeze", "fever": "fever", "bowel_frequency": "bowel_frequency", "stool_consistency": "stool_consistency", "straining": "straining", "blood_in_stool": "blood_in_stool", "abdominal_distension": "abdominal_distension", "urinary_frequency": "urinary_frequency", "urinary_burning": "urinary_burning", "urinary_blood": "urinary_blood", "past_medical_history": "past_medical_history", "past_surgical_history": "past_surgical_history", "hospitalizations": "hospitalizations", "immunizations": "immunizations", "medications": "medications", "allergies": "allergies", "adverse_drug_reactions": "adverse_drug_reactions", "family_history": "family_history", "occupation": "occupation", "diet": "diet", "sleep": "sleep", "physical_activity": "physical_activity", "smoking": "smoking", "alcohol": "alcohol", "tobacco": "tobacco", "menstrual_history": "menstrual_history", "pregnancy_status": "pregnancy_status", "sexual_history": "sexual_history", "constitutional": "constitutional", "cardiovascular": "cardiovascular", "respiratory": "respiratory", "gastrointestinal": "gastrointestinal", "genitourinary": "genitourinary", "neurological": "neurological", "musculoskeletal": "musculoskeletal", "skin": "skin", "endocrine": "endocrine", "hematologic": "hematologic", "psychiatric": "psychiatric", "ayush_prakriti": "ayush_prakriti", "ayush_vikriti": "ayush_vikriti", "ayush_sara": "ayush_sara", "ayush_samhanana": "ayush_samhanana", "ayush_pramana": "ayush_pramana", "ayush_satmya": "ayush_satmya", "ayush_satva": "ayush_satva", "ayush_ahara_shakti": "ayush_ahara_shakti", "ayush_vyayama_shakti": "ayush_vyayama_shakti", "ayush_vaya": "ayush_vaya", "ayush_ahara_vihara": "ayush_ahara_vihara", "ayush_agni": "ayush_agni", "ayush_koshta": "ayush_koshta", "ayush_nidana": "ayush_nidana", "ayush_samprapti": "ayush_samprapti"
}

TARGET_TRANSLATIONS = {
    "section_closure": {"en": "anything else important to add", "hi": "और कोई महत्वपूर्ण बात"}
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

    async def generate_question(self, state: InterviewState, conversation: list[dict[str, Any]], language: str, session_id: str | None = None, forced_target: str | None = None) -> QuestionDecision:
        candidates = state.candidate_targets()
        if forced_target and forced_target in candidates:
            candidates = [forced_target]
        if not candidates:
            return QuestionDecision(self._emergency_question(state.current_section, language), None, False)
        if not self.enabled or self.provider != "lemonade":
            return QuestionDecision(self._emergency_question_for_target(candidates[0], language), candidates[0], False)
        prompt = self._build_question_prompt(
            state, conversation, language, candidates)
        try:
            content = await self._call_model(prompt, session_id)
            decision = self._parse_question(content, candidates)
            if decision.question and decision.target and decision.question.lower() not in {item.lower() for item in state.question_history}:
                return decision
            forced = candidates[0]
            content = await self._call_model(self._build_question_prompt(state, conversation, language, [forced], forced), session_id)
            decision = self._parse_question(content, [forced])
            if decision.question and decision.target and decision.question.lower() not in {item.lower() for item in state.question_history}:
                return decision
        except InterviewModelError as exc:
            self._debug("QUESTION_FAILURE", session_id=session_id,
                        error_type=type(exc).__name__, error=str(exc))
        return QuestionDecision(self._emergency_question_for_target(candidates[0], language), candidates[0], False)

    def extract_facts(self, text: str, state: InterviewState, turn_id: str | None = None) -> list[dict[str, Any]]:
        normalized = text.strip()
        if not normalized:
            return []
        facts: list[dict[str, Any]] = []
        target = state.pending_target
        section = state.current_section
        topic = self.detect_topic(normalized)
        if topic and state.known_fields().get("chief_complaint") is None:
            facts.append(self._fact("hpi", "chief_complaint",
                         self._complaint_from_topic(topic), normalized, turn_id))
        if target and target != "section_closure" and target in TARGET_FIELD:
            field = TARGET_FIELD[target]
            negative = self.is_negative_answer(
                normalized) or self._target_negative(target, normalized)
            value = self._target_value(target, normalized, negative)
            if value is not None:
                facts.append(self._fact(section, field, value,
                             normalized, turn_id, negative))
        facts.extend(self._cross_section_facts(normalized, state, turn_id))
        return self._dedupe(facts)

    @staticmethod
    def is_negative_answer(text: str) -> bool:
        value = InterviewExtractor._normalize_text(text)
        if value in NEGATIVE_ANSWERS or "nothing else" in value or "कुछ नहीं" in value or "और कुछ नहीं" in value:
            return True
        return bool(re.fullmatch(r"(?:no|none|n/?a|नहीं)(?:\s+(?:more|else|nothing))?", value))

    @staticmethod
    def detect_topic(text: str) -> str | None:
        normalized = text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return topic
        return None

    async def _call_model(self, prompt: str, session_id: str | None) -> str:
        payload = {"model": self.model, "messages": [{"role": "system", "content": self._system_prompt(
        )}, {"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 96, "stream": False, "chat_template_kwargs": {"enable_thinking": False}}
        urls = self._candidate_urls()
        last_error: Exception | None = None
        for url in urls:
            try:
                started = time.monotonic()
                timeout = httpx.Timeout(
                    connect=3.0, read=self.timeout, write=3.0, pool=3.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code in {400, 404, 422} and "chat_template_kwargs" in payload:
                        retry_payload = dict(payload)
                        retry_payload.pop("chat_template_kwargs", None)
                        response = await client.post(url, json=retry_payload)
                    response.raise_for_status()
                    body = response.json()
                elapsed = round((time.monotonic() - started) * 1000, 2)
                choices = body.get("choices") if isinstance(
                    body, dict) else None
                if not isinstance(choices, list) or not choices:
                    raise ValueError("Local model returned no choices")
                choice = choices[0]
                message = choice.get("message", {}) if isinstance(
                    choice, dict) else {}
                content = message.get("content") if isinstance(
                    message, dict) else None
                if isinstance(content, list):
                    content = "".join(item.get("text", "") if isinstance(
                        item, dict) else str(item) for item in content)
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Local model returned empty content")
                self._debug("QUESTION_MODEL_OK", session_id=session_id,
                            url=url, model=self.model, elapsed_ms=elapsed)
                return content
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                last_error = InterviewModelError(str(exc))
                self._debug("QUESTION_ENDPOINT_FAILURE", session_id=session_id,
                            url=url, error_type=type(exc).__name__, error=str(exc))
        raise last_error or InterviewModelError("Local model request failed")

    def _build_question_prompt(self, state: InterviewState, conversation: list[dict[str, Any]], language: str, candidates: list[str], forced: str | None = None) -> str:
        recent = conversation[-18:]
        known = state.known_fields()
        candidate_text = "\n".join(f"- {item}: {TARGET_TRANSLATIONS.get(item, {}).get(language, item.replace(
            '_', ' '))}" if item == "section_closure" else f"- {item}: {self._description(item, language)}" for item in candidates)
        force = f"You must use target: {forced}.\n" if forced else ""
        return f"Preferred language: {language}\nCurrent section: {state.current_section}\nClinical topic: {state.topic}\nKnown history: {json.dumps(known, ensure_ascii=False, default=str)}\nRecent questions: {json.dumps(state.question_history[-10:], ensure_ascii=False)}\nRecent target sequence: {json.dumps(state.target_history[-10:], ensure_ascii=False)}\nRecent conversation: {json.dumps(recent, ensure_ascii=False, default=str)}\nAllowed targets for the next question:\n{candidate_text}\n{force}Choose exactly one allowed target. Ask exactly one concise patient-facing question about that target. Do not combine separate history domains. Do not diagnose, explain, prescribe, reassure, or recommend treatment. Never repeat an already answered target unless the latest answer was vague or incomplete. For chest pain, prioritize the clinically relevant SOCRATES elements still missing. For other complaints, adapt to the symptom and prior answers. If target is section_closure, ask whether anything important remains to be added for the current section. Return exactly two lines and nothing else:\nTARGET: <target>\nQUESTION: <question>"

    @staticmethod
    def _system_prompt() -> str:
        return "You are Aurora's clinical history-taking interviewer. Your job is only to collect history before a clinician consultation. Follow the required order HPI, past medical and surgical history, drug and allergy history, family history, personal history, review of systems, then AYUSH-specific history only when AYUSH mode is enabled. Adapt HPI follow-up questions to the patient's complaint and answers. Use one question at a time. Every question must be answerable by speaking or tapping. Preserve the patient's meaning. Do not infer facts that were not stated. Do not diagnose or recommend treatment. Keep questions natural, short, respectful, and in the patient's selected language."

    def _parse_question(self, content: str, candidates: list[str]) -> QuestionDecision:
        cleaned = re.sub(r"<think>.*?</think>", "", content,
                         flags=re.IGNORECASE | re.DOTALL).strip()
        target_match = re.search(
            r"(?:^|\n)\s*TARGET\s*:\s*([^\n]+)", cleaned, flags=re.IGNORECASE)
        question_match = re.search(
            r"(?:^|\n)\s*QUESTION\s*:\s*(.+)", cleaned, flags=re.IGNORECASE | re.DOTALL)
        target = target_match.group(1).strip().strip(
            "`\"'").lower() if target_match else None
        if target and target not in candidates:
            target = None
        question = question_match.group(1).strip(
        ) if question_match else self._extract_question_line(cleaned)
        question = re.sub(r"^[-*\d.)\s]+", "", question).strip().strip('"')
        question = re.sub(r"\s+", " ", question)
        question = re.split(r"\n(?:TARGET|QUESTION)\s*:",
                            question, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if "?" in question:
            question = question.split("?", 1)[0].strip() + "?"
        elif question:
            question += "?"
        if not self._valid_question(question):
            return QuestionDecision("", target, True)
        if target is None and len(candidates) == 1:
            target = candidates[0]
        if target is None:
            return QuestionDecision("", None, True)
        return QuestionDecision(question, target, True)

    @staticmethod
    def _extract_question_line(content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in reversed(lines):
            if "?" in line:
                return line
        return lines[-1] if lines else ""

    @staticmethod
    def _valid_question(question: str) -> bool:
        if len(question) < 8 or len(question) > 320:
            return False
        lower = question.lower()
        if any(marker in lower for marker in ("target:", "question:", "```", "{", "}")):
            return False
        return True

    @staticmethod
    def _description(target: str, language: str) -> str:
        from backend.ai.interview.state import TARGET_DESCRIPTIONS
        description = TARGET_DESCRIPTIONS.get(target, {}).get(
            language) or TARGET_DESCRIPTIONS.get(target, {}).get("en") or target.replace("_", " ")
        return description

    @staticmethod
    def _target_negative(target: str, text: str) -> bool:
        normalized = text.lower()
        terms = {
            "straining": ("strain", "push hard", "जोर"),
            "blood_in_stool": ("blood", "bleeding", "खून"),
            "abdominal_distension": ("bloat", "swelling", "फूल", "सूजन"),
            "breathing_difficulty": ("breath", "breathing", "सांस", "साँस"),
            "wheeze": ("wheez", "घरघराहट"),
            "fever": ("fever", "temperature", "बुखार"),
            "urinary_burning": ("burning", "painful urination", "जलन"),
            "urinary_blood": ("blood", "खून"),
            "smoking": ("smoke", "smoking", "cigarette", "धूम्रपान"),
            "alcohol": ("alcohol", "drink", "शराब"),
            "tobacco": ("tobacco", "तंबाकू"),
            "medications": ("medicine", "medicines", "medication", "medications", "drug", "drugs", "दवा", "दवाइ"),
            "allergies": ("allergy", "allergies", "allergic", "एलर्जी"),
            "family_history": ("family", "परिवार"),
            "past_surgical_history": ("surgery", "operation", "operated", "सर्जरी", "ऑपरेशन"),
            "past_medical_history": ("disease", "diabetes", "hypertension", "asthma", "history", "बीमारी", "मधुमेह", "अस्थमा"),
            "hospitalizations": ("hospital", "admitted", "भर्ती"),
        }.get(target, ())
        if not any(term in normalized for term in terms):
            return False
        return bool(re.search(r"(?:^|\b)(?:no|not|never|don[’\']t|do not|without)\s+(?:\w+\s+){0,4}(?:" + "|".join(re.escape(term) for term in terms if re.match(r"[A-Za-z]", term)) + r")\b", normalized)) or "नहीं" in normalized

    @staticmethod
    def _target_value(target: str, text: str, negative: bool) -> Any:
        if negative:
            return False
        normalized = text.lower()
        binary = {"straining", "blood_in_stool", "abdominal_distension", "breathing_difficulty",
                  "wheeze", "fever", "urinary_burning", "urinary_blood", "smoking", "alcohol", "tobacco"}
        if target in binary:
            if target == "straining" and not any(word in normalized for word in ("strain", "push hard", "जोर")):
                return text
            if target == "blood_in_stool" and not any(word in normalized for word in ("blood", "bleeding", "खून")):
                return text
            if target == "abdominal_distension" and not any(word in normalized for word in ("bloat", "swelling", "सूजन", "फूल")):
                return text
            if target == "breathing_difficulty" and not any(word in normalized for word in ("breath", "breathing", "सांस", "साँस")):
                return text
            return True
        if target == "severity":
            match = re.search(
                r"\b(10|[0-9])\s*(?:/|out of|में से)?\s*10\b", normalized)
            if match:
                return int(match.group(1))
        if target in {"onset", "duration"}:
            match = re.search(
                r"\b(?:started|began|since|for)\s+([^,.!?;]+)", normalized)
            if match:
                return match.group(1).strip()
            duration = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple|a few)\s+(day|days|hour|hours|week|weeks|month|months|year|years)\b", normalized)
            if duration:
                return f"{duration.group(1)} {duration.group(2)}"
        if target == "bowel_frequency":
            match = re.search(
                r"\b\d+(?:\.\d+)?\s*(?:times?|bowel movements?)\s*(?:a|per)\s*(?:day|week|month)\b", normalized)
            if match:
                return match.group(0)
        if target == "stool_consistency":
            for value in ("watery", "loose", "hard", "normal", "सख्त", "ढीला", "पानी जैसा"):
                if value in normalized:
                    return value
        return text

    def _cross_section_facts(self, text: str, state: InterviewState, turn_id: str | None) -> list[dict[str, Any]]:
        normalized = text.lower()
        facts: list[dict[str, Any]] = []
        if state.current_section == "hpi":
            severity = re.search(
                r"\b(10|[0-9])\s*(?:/|out of|में से)?\s*10\b", normalized)
            if severity:
                facts.append(self._fact("hpi", "severity", int(
                    severity.group(1)), text, turn_id))
            duration = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple|a few)\s+(day|days|hour|hours|week|weeks|month|months|year|years)\b", normalized)
            if duration:
                facts.append(self._fact("hpi", "duration", f"{duration.group(1)} {
                             duration.group(2)}", text, turn_id))
            if any(term in normalized for term in ("constipation", "constipated", "कब्ज")):
                facts.append(self._fact("hpi", "bowel_changes",
                             "constipation", text, turn_id))
            if any(term in normalized for term in ("diarrhea", "loose stools", "loose motions", "दस्त")):
                facts.append(self._fact("hpi", "bowel_changes",
                             "diarrhea", text, turn_id))
            if any(term in normalized for term in ("hard stool", "hard stools", "hard bowel movement", "सख्त")):
                facts.append(self._fact(
                    "hpi", "stool_consistency", "hard", text, turn_id))
            if any(term in normalized for term in ("straining", "strain to pass stool", "have to strain", "जोर लगाना")):
                facts.append(self._fact(
                    "hpi", "straining", True, text, turn_id))
            if any(term in normalized for term in ("blood in stool", "blood in stools", "blood while passing stool", "rectal bleeding", "मल में खून")):
                facts.append(self._fact(
                    "hpi", "blood_in_stool", True, text, turn_id))
            if any(term in normalized for term in ("no blood", "there is no blood", "खून नहीं")):
                facts.append(self._fact("hpi", "blood_in_stool",
                             False, text, turn_id, True))
            if any(term in normalized for term in ("bloating", "bloated", "abdominal distension", "stomach bloating", "पेट फूल")):
                facts.append(self._fact(
                    "hpi", "abdominal_distension", True, text, turn_id))
        if any(term in normalized for term in ("allergic to", "allergy to", "allergy", "allergies", "एलर्जी")):
            facts.append(self._fact("drug_allergy", "allergies", False if self._target_negative(
                "allergies", normalized) else text, text, turn_id, self._target_negative("allergies", normalized)))
        if re.search(r"\b(?:take|taking|takes|on)\b.{0,60}\b\d+\s*(?:mg|mcg|ml)\b", normalized) or any(term in normalized for term in ("metformin", "insulin", "amlodipine", "paracetamol", "ibuprofen", "medicine", "medicines", "medication", "medications", "drugs", "दवा", "दवाइ")):
            negative = self._target_negative(
                "medications", normalized) or self.is_negative_answer(text)
            facts.append(self._fact("drug_allergy", "medications",
                         False if negative else text, text, turn_id, negative))
        if any(term in normalized for term in ("surgery", "operation", "operated", "सर्जरी", "ऑपरेशन")):
            negative = self._target_negative(
                "past_surgical_history", normalized)
            facts.append(self._fact("past_history", "past_surgical_history",
                         False if negative else text, text, turn_id, negative))
        if any(term in normalized for term in ("diabetes", "hypertension", "blood pressure", "asthma", "thyroid", "heart disease", "kidney disease", "liver disease", "epilepsy", "cancer", "मधुमेह", "ब्लड प्रेशर", "अस्थमा", "थायरॉइड")):
            negative = self._target_negative(
                "past_medical_history", normalized)
            facts.append(self._fact("past_history", "past_medical_history",
                         False if negative else text, text, turn_id, negative))
        if any(term in normalized for term in ("my father", "my mother", "my brother", "my sister", "family history", "runs in my family", "मेरे पिता", "मेरी मां", "मेरी माँ", "मेरे भाई", "मेरी बहन", "परिवार")):
            negative = self._target_negative("family_history", normalized)
            facts.append(self._fact("family_history", "family_history",
                         False if negative else text, text, turn_id, negative))
        for field, terms in (("smoking", ("smoke", "smoking", "cigarette", "धूम्रपान")), ("alcohol", ("alcohol", "drink alcohol", "शराब")), ("tobacco", ("tobacco", "तंबाकू"))):
            if any(term in normalized for term in terms):
                negative = self._target_negative(field, normalized)
                facts.append(self._fact("personal_history", field,
                             False if negative else text, text, turn_id, negative))
        return facts

    @staticmethod
    def _fact(section: str, field: str, value: Any, evidence: str, turn_id: str | None, negative: bool = False) -> dict[str, Any]:
        return {"section": section, "field": normalize_field_name(field), "value": value, "negative": negative, "evidence": evidence, "turn_id": turn_id}

    @staticmethod
    def _dedupe(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen = set()
        for fact in facts:
            key = (fact.get("section"), fact.get("field"), json.dumps(fact.get(
                "value"), ensure_ascii=False, sort_keys=True, default=str), bool(fact.get("negative")))
            if key not in seen:
                seen.add(key)
                result.append(fact)
        return result

    @staticmethod
    def _complaint_from_topic(topic: str) -> str:
        return topic.replace("_", " ")

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"[,.!?।]+", "", text.strip().lower())

    def _candidate_urls(self) -> list[str]:
        configured = self.url.rstrip("/")
        urls = [configured]
        replacements = (("/api/v1/", "/v1/"), ("/v1/", "/api/v1/"))
        for old, new in replacements:
            if old in configured:
                alt = configured.replace(old, new, 1)
                if alt not in urls:
                    urls.append(alt)
        return urls

    @staticmethod
    def _emergency_question(section: str, language: str) -> str:
        if language == "hi":
            return "कृपया अपनी स्वास्थ्य समस्या के बारे में थोड़ा और बताइए?"
        return "Could you tell me a little more about your health problem?"

    @staticmethod
    def _emergency_question_for_target(target: str, language: str) -> str:
        if target == "section_closure":
            return "क्या इस हिस्से के बारे में कोई और महत्वपूर्ण बात बतानी है?" if language == "hi" else "Is there anything else important you would like to add about this part of your history?"
        from backend.ai.interview.state import TARGET_DESCRIPTIONS
        description = TARGET_DESCRIPTIONS.get(target, {}).get(
            language) or TARGET_DESCRIPTIONS.get(target, {}).get("en") or target.replace("_", " ")
        return f"कृपया बताइए {description} के बारे में क्या जानकारी है?" if language == "hi" else f"Could you tell me about {description}?"
