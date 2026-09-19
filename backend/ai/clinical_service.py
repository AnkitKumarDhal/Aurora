from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .ai_engine import (
    extract_contextual_fields,
    extract_explicit_onset,
    extract_history,
)
from .complaint_router import classify_complaint
from .clinical_schema import QUESTION_GROUPS
from .red_flag_engine import detect_red_flags
from .clinical_evidence import ClinicalEvidenceStore


class ClinicalSession:
    """
    Patient-facing clinical history collection engine.

    Design principles:
    - Preserve every patient statement exactly as provided.
    - Derive structured fields without silently deleting raw information.
    - Use deterministic extraction first and optional AI only when appropriate.
    - Never silently overwrite conflicting clinical assertions.
    - Flag clinically concerning combinations for physician review/triage.
    """

    # Open-ended fields should not turn "no" into a literal clinical value.
    # The raw patient response remains fully preserved in raw_responses.
    OPEN_ENDED_FIELDS = {
        "diet",
        "sleep",
        "activity",
        "general",
        "general_complaint",
        "prakriti",
        "vikriti",
        "sara",
        "samhanana",
        "pramana",
        "satmya",
        "sattva",
        "ahara_shakti",
        "vyayama_shakti",
        "vaya",
        "ahara_vihara",
        "dashavidha",
    }

    SIMPLE_NEGATIVE_VALUES = {
        "no",
        "nope",
        "nah",
        "none",
        "nothing",
        "nothing else",
        "not really",
        "not applicable",
        "na",
        "n/a",
        "nil",
    }

    SIMPLE_POSITIVE_VALUES = {
        "yes",
        "yeah",
        "yep",
        "y",
    }

    def __init__(self) -> None:
        self.patient_history: Dict[str, Any] = {
            "chief_complaint": None,
            "history_of_present_illness": {},
            "respiratory_history": {},
            "gastrointestinal_history": {},
            "neurological_history": {},
            "skin_history": {},
            "urinary_history": {},
            "past_history": {},
            "medication_history": {},
            "family_history": {},
            "personal_history": {},
            "review_of_systems": {},
            "ayush": {},
        }

        self.raw_responses: List[Dict[str, Any]] = []
        self.field_history: Dict[str, List[Dict[str, Any]]] = {}
        self.contradictions: List[Dict[str, Any]] = []
        self.adaptive_extractions: List[Dict[str, Any]] = []
        self.evidence_store = ClinicalEvidenceStore()

        self.red_flags: List[str] = []
        self.triage_required: bool = False
        self.review_required: bool = False
        self.completed: bool = False

        self.complaint_categories: List[str] = []
        self.question_queue: List[Dict[str, str]] = []
        self.question_index: int = 0

    # ------------------------------------------------------------------
    # Question helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_question(item: Any) -> Optional[Dict[str, str]]:
        """
        Accept common schema representations:
          {"field": "...", "question": "..."}
          {"name": "...", "question": "..."}
          {"id": "...", "text": "..."}
        """
        if isinstance(item, dict):
            field = (
                item.get("field")
                or item.get("name")
                or item.get("id")
                or item.get("key")
            )
            question = (
                item.get("question")
                or item.get("text")
                or item.get("prompt")
            )
            if field and question:
                return {"field": str(field), "question": str(question)}

        # Defensive support for tuples/lists like ("field", "question").
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            return {"field": str(item[0]), "question": str(item[1])}

        return None

    def _questions_for_category(self, category: str) -> List[Dict[str, str]]:
        group = QUESTION_GROUPS.get(category, [])
        result: List[Dict[str, str]] = []
        for item in group:
            question = self._normalise_question(item)
            if question:
                result.append(question)
        return result

    def _build_question_queue(self) -> None:
        """
        Build an adaptive but deterministic queue.

        Complaint-specific questions are followed by the full general
        medical history, review of systems, and AYUSH assessment.

        The queue is always schema-driven. AI may extract an explicitly
        stated fact early, but it never changes question order or invents
        fields outside this queue.
        """
        ordered_categories: List[str] = []

        for category in self.complaint_categories:
            if category not in ordered_categories:
                ordered_categories.append(category)

        if "general" not in ordered_categories:
            ordered_categories.append("general")

        queue: List[Dict[str, str]] = []
        seen_fields = set()

        # Core history is always available. The chief-complaint handler may
        # already extract onset; _current_question() will then skip it. If
        # onset was not stated, the deterministic queue will ask for it.
        for question in self._questions_for_category("core"):
            field = question["field"]
            if field not in seen_fields:
                queue.append(question)
                seen_fields.add(field)

        for category in ordered_categories:
            for question in self._questions_for_category(category):
                field = question["field"]
                if field not in seen_fields:
                    queue.append(question)
                    seen_fields.add(field)

        # AYUSH is a separate assessment block rather than a complaint
        # category. Prefer the canonical schema definition. A small fallback
        # list is retained so isolated tests that stub clinical_schema keep
        # working without the full schema module.
        ayush_questions = self._questions_for_category("ayush")

        if not ayush_questions:
            ayush_questions = [
                {
                    "field": "prakriti",
                    "question": "If applicable, please describe your known Prakriti.",
                },
                {
                    "field": "vikriti",
                    "question": "If applicable, please describe your known Vikriti or current imbalance assessment.",
                },
                {
                    "field": "sara",
                    "question": "If known, please provide your Sara assessment.",
                },
                {
                    "field": "samhanana",
                    "question": "If known, please provide your Samhanana assessment.",
                },
                {
                    "field": "pramana",
                    "question": "If known, please provide your Pramana or body-measurement assessment.",
                },
                {
                    "field": "satmya",
                    "question": "If known, please describe your Satmya or habituation assessment.",
                },
                {
                    "field": "sattva",
                    "question": "If known, please provide your Sattva assessment.",
                },
                {
                    "field": "ahara_shakti",
                    "question": "If known, please provide your Ahara Shakti assessment.",
                },
                {
                    "field": "vyayama_shakti",
                    "question": "If known, please provide your Vyayama Shakti assessment.",
                },
                {
                    "field": "vaya",
                    "question": "If known, please provide your Vaya assessment.",
                },
                {
                    "field": "ahara_vihara",
                    "question": "Please describe any relevant Ahara-Vihara (diet and lifestyle) information.",
                },
                {
                    "field": "dashavidha",
                    "question": "If applicable, please provide any other known Dashavidha Pariksha information.",
                },
            ]

        for question in ayush_questions:
            field = question["field"]
            if field not in seen_fields:
                queue.append(question)
                seen_fields.add(field)

        self.question_queue = queue
        self.question_index = 0

    def _current_question(self) -> Optional[Dict[str, str]]:
        while self.question_index < len(self.question_queue):
            question = self.question_queue[self.question_index]
            field = question["field"]

            # If a field has already been populated, don't ask it again.
            if self._field_has_value(field):
                self.question_index += 1
                continue

            return question

        return None

    def _field_has_value(self, field: str) -> bool:
        if field == "chief_complaint":
            return bool(self.patient_history.get("chief_complaint"))

        section = self._get_section_for_field(field)
        return bool(
            isinstance(self.patient_history.get(section), dict)
            and field in self.patient_history[section]
            and self.patient_history[section].get(field) not in (None, "")
        )

    def get_next_question(self) -> str:
        if self.completed:
            return "Clinical history collection is complete."

        # A newly-created session has no queue until the chief complaint is
        # received. Expose the real patient-facing starting prompt instead of
        # incorrectly reporting the interview as complete.
        if self.patient_history.get("chief_complaint") is None:
            return (
                "What is the main problem or symptom that brought you here?"
            )

        current = self._current_question()
        if current is None:
            self.completed = True
            self._refresh_triage()
            return "Clinical history collection is complete."

        return current["question"]

    # ------------------------------------------------------------------
    # Section / storage helpers
    # ------------------------------------------------------------------

    def _get_section_for_field(self, field: str) -> str:
        direct_sections = {
            "chief_complaint": None,
            "onset": "history_of_present_illness",
            "site": "history_of_present_illness",
            "character": "history_of_present_illness",
            "radiation": "history_of_present_illness",
            "associated_symptoms": "history_of_present_illness",
            "timing": "history_of_present_illness",
            "aggravating_factors": "history_of_present_illness",
            "relieving_factors": "history_of_present_illness",
            "severity": "history_of_present_illness",
            "general_complaint": "history_of_present_illness",

            "respiratory_triggers": "respiratory_history",
            "cough": "respiratory_history",
            "sputum": "respiratory_history",
            "wheezing": "respiratory_history",
            "breathing_difficulty": "respiratory_history",

            "gi_location": "gastrointestinal_history",
            "nausea_vomiting": "gastrointestinal_history",
            "bowel_changes": "gastrointestinal_history",
            "appetite": "gastrointestinal_history",
            "food_relation": "gastrointestinal_history",

            "neuro_location": "neurological_history",
            "dizziness": "neurological_history",
            "weakness": "neurological_history",
            "numbness": "neurological_history",
            "vision": "neurological_history",
            "headache_features": "neurological_history",

            "skin_location": "skin_history",
            "skin_pain": "skin_history",
            "itching": "skin_history",
            "changes": "skin_history",

            "urinary_associated_symptoms": "urinary_history",
            "urination_changes": "urinary_history",
            "blood": "urinary_history",
            "burning": "urinary_history",

            "medical_history": "past_history",
            "surgical_history": "past_history",

            "current_medications": "medication_history",
            "allergies": "medication_history",

            "family_history": "family_history",

            "diet": "personal_history",
            "sleep": "personal_history",
            "smoking": "personal_history",
            "alcohol": "personal_history",
            "activity": "personal_history",

            "general": "review_of_systems",
            "respiratory": "review_of_systems",
            "cardiovascular": "review_of_systems",
            "gastrointestinal": "review_of_systems",
            "neurological": "review_of_systems",

            "prakriti": "ayush",
            "vikriti": "ayush",
            "sara": "ayush",
            "samhanana": "ayush",
            "pramana": "ayush",
            "satmya": "ayush",
            "sattva": "ayush",
            "ahara_shakti": "ayush",
            "vyayama_shakti": "ayush",
            "vaya": "ayush",
            "ahara_vihara": "ayush",
            "dashavidha": "ayush",
        }

        if field in direct_sections:
            return direct_sections[field]

        # Safe fallbacks for future schema additions.
        for section, values in {
            "respiratory_history": {"respiratory"},
            "gastrointestinal_history": {"gastrointestinal"},
            "neurological_history": {"neurological"},
            "skin_history": {"skin"},
            "urinary_history": {"urinary"},
        }.items():
            if field in values:
                return section

        return "history_of_present_illness"

    def process_audio_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe a patient voice response and feed the transcript through
        the same clinical engine used for typed/touch responses.

        Voice recognition is an input modality; it does not change clinical
        question ordering or extraction rules. If ASR fails, the clinical
        session is left unchanged and the failure is returned for the caller
        to handle.
        """
        try:
            from voice_asr import transcribe_audio
        except ImportError as exc:
            return {
                "status": "failed",
                "stage": "dependency",
                "error": str(exc),
                "completed": self.completed,
                "next_question": self.get_next_question(),
            }

        transcription = transcribe_audio(
            audio_path=audio_path,
            language=language,
        )

        if not isinstance(transcription, dict):
            return {
                "status": "failed",
                "stage": "transcription",
                "error": "ASR returned an invalid response.",
                "completed": self.completed,
                "next_question": self.get_next_question(),
            }

        if transcription.get("status") != "success":
            return {
                "status": "failed",
                "stage": transcription.get(
                    "stage",
                    "transcription",
                ),
                "error": transcription.get(
                    "error",
                    "Voice transcription failed.",
                ),
                "voice": transcription,
                "completed": self.completed,
                "next_question": self.get_next_question(),
            }

        transcript = str(
            transcription.get("text")
            or ""
        ).strip()

        if not transcript:
            return {
                "status": "failed",
                "stage": "transcription",
                "error": "Voice transcription returned no text.",
                "voice": transcription,
                "completed": self.completed,
                "next_question": self.get_next_question(),
            }

        result = self.process_response(
            transcript
        )

        result["status"] = "success"
        result["input_modality"] = "voice"
        result["voice"] = transcription
        result["transcript"] = transcript

        return result

    # ------------------------------------------------------------------
    # Input processing
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(value: Any) -> str:
        return str(value or "").strip()

    @classmethod
    def _simple_answer(cls, response: str) -> Optional[str]:
        cleaned = response.strip().lower()
        cleaned = cleaned.rstrip(".!?").strip()

        if cleaned in cls.SIMPLE_NEGATIVE_VALUES:
            return "None reported"

        if cleaned in cls.SIMPLE_POSITIVE_VALUES:
            return "Yes"

        return None

    def _fallback_value(self, field: str, response: str) -> str:
        """
        Convert only truly simple yes/no responses into a meaningful
        structured value.

        For open-ended fields, a bare 'no' means the patient did not
        provide useful information rather than 'No' being the clinical
        value.
        """
        simple = self._simple_answer(response)

        if field in self.OPEN_ENDED_FIELDS:
            if simple == "None reported":
                return "Not provided / patient did not provide information"
            if simple == "Yes":
                return "Patient affirmed but did not provide details"

        if simple is not None:
            return simple

        return response.strip()

    def _extract_current_field(
        self,
        field: str,
        response: str,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Run the existing selective-AI extraction pipeline.

        Returns:
            structured_data, extraction_method
        """
        try:
            extracted = extract_history(
                patient_response=response,
                field=field,
            )
        except TypeError:
            # Compatibility fallback for an older function signature.
            try:
                extracted = extract_history(response, field)
            except Exception:
                extracted = {}
        except Exception:
            extracted = {}

        if not isinstance(extracted, dict):
            return {}, "raw_field_fallback"

        method = extracted.pop("__extraction_method__", None)

        # AI may return metadata that belongs to the session rather than
        # the field. Keep contradiction metadata separate.
        ai_contradiction = bool(extracted.pop("contradiction_detected", False))
        ai_details = extracted.pop("contradiction_details", None)

        if ai_contradiction:
            extracted["__contradiction_detected__"] = True
        if ai_details:
            extracted["__contradiction_details__"] = ai_details

        # Never allow extraction for another field to overwrite the current
        # field. Keep only the requested field.
        if field in extracted:
            value = extracted.get(field)
            clean = {
                field: value,
            }
            if "__contradiction_detected__" in extracted:
                clean["__contradiction_detected__"] = extracted[
                    "__contradiction_detected__"
                ]
            if "__contradiction_details__" in extracted:
                clean["__contradiction_details__"] = extracted[
                    "__contradiction_details__"
                ]
            return clean, method or "ai"

        return {}, method or "raw_field_fallback"

    def _ai_candidate_fields(
        self,
        exclude_field: Optional[str] = None,
        limit: int = 12,
    ) -> List[str]:
        """Return only queued, still-missing fields that AI may opportunistically extract."""
        candidates: List[str] = []
        for question in self.question_queue:
            field = question["field"]
            if field == exclude_field:
                continue
            if field in candidates:
                continue
            if self._field_has_value(field):
                continue
            candidates.append(field)
            if len(candidates) >= limit:
                break
        return candidates

    def _extract_adaptive_fields(
        self,
        response: str,
        exclude_field: Optional[str] = None,
        limit: int = 12,
    ) -> Tuple[Dict[str, Any], str]:
        """Let AI capture other explicit facts already present in the same answer.

        AI receives an allow-list taken from the existing deterministic queue. It
        cannot invent a new question or change question order.
        """
        candidates = self._ai_candidate_fields(exclude_field, limit=limit)
        if not candidates:
            return {}, "none"

        try:
            extracted = extract_contextual_fields(
                patient_response=response,
                candidate_fields=candidates,
            )
        except Exception:
            return {}, "none"

        if not isinstance(extracted, dict):
            return {}, "none"

        provider = extracted.pop("__ai_provider__", None)
        method = extracted.pop("__extraction_method__", None) or "none"
        extracted.pop("__ai_fields__", None)

        clean: Dict[str, Any] = {}
        for field, value in extracted.items():
            if field in candidates and value not in (None, "", [], {}):
                clean[field] = value

        if provider:
            return clean, f"{method}:{provider}"
        return clean, method

    def _store_adaptive_extractions(
        self,
        extracted: Dict[str, Any],
        patient_response: str,
        source_field: str,
        extraction_method: str,
    ) -> None:
        """Persist opportunistically extracted facts without replacing patient text."""
        if not extracted:
            return

        current_raw_index = len(self.raw_responses) - 1

        for field, value in extracted.items():
            if value in (None, "", [], {}):
                continue

            # Only fill a field that is actually in this session's queue.
            queued_fields = {item["field"] for item in self.question_queue}
            if field not in queued_fields:
                continue

            before = self.patient_history.get(
                self._get_section_for_field(field)
            )
            before_value = (
                before.get(field)
                if isinstance(before, dict)
                else None
            )

            adaptive_confidence = None
            if extraction_method.startswith("ai_contextual"):
                # Contextual extractor currently does not expose per-field
                # confidence, so leave this unset rather than inventing one.
                adaptive_confidence = None

            self.store_extracted_data(
                {field: value},
                field,
                patient_response,
                extraction_method=extraction_method,
                confidence=adaptive_confidence,
                source_field=source_field,
            )

            after = self.patient_history.get(
                self._get_section_for_field(field)
            )
            after_value = (
                after.get(field)
                if isinstance(after, dict)
                else None
            )

            self.adaptive_extractions.append(
                {
                    "raw_response_index": current_raw_index,
                    "source_field": source_field,
                    "field": field,
                    "value": value,
                    "stored": self._normalise_compare(after_value)
                    == self._normalise_compare(value),
                    "overwrote_existing": before_value not in (None, ""),
                    "extraction_method": extraction_method,
                }
            )

    def process_response(self, response: str) -> Dict[str, Any]:
        if self.completed:
            return {
                "message": "Clinical history collection is already complete.",
                "completed": True,
                "history": self.patient_history,
                "next_question": None,
            }

        response = self._clean_text(response)
        if not response:
            return {
                "message": "Please provide a response.",
                "completed": False,
                "history": self.patient_history,
                "next_question": self.get_next_question(),
            }

        # First response is always the chief complaint.
        if self.patient_history.get("chief_complaint") is None:
            self._store_chief_complaint(response)

            adaptive_fields, adaptive_method = self._extract_adaptive_fields(
                response,
                exclude_field="chief_complaint",
                limit=12,
            )
            if adaptive_fields:
                self._store_adaptive_extractions(
                    adaptive_fields,
                    response,
                    source_field="chief_complaint",
                    extraction_method=adaptive_method,
                )
                self.raw_responses[-1]["adaptive_structured"] = dict(
                    adaptive_fields
                )
                self.raw_responses[-1]["structured"].update(
                    adaptive_fields
                )
                self.raw_responses[-1]["adaptive_extraction_method"] = (
                    adaptive_method
                )

            self._refresh_triage()

            next_question = self.get_next_question()
            return {
                "field": "chief_complaint",
                "question": next_question,
                "history": self.patient_history,
                "completed": self.completed,
                "raw_response": response,
                "extraction_method": "direct",
                "adaptive_fields": adaptive_fields,
                "next_question": next_question,
                "red_flags": self.red_flags,
                "triage_required": self.triage_required,
            }

        current = self._current_question()
        if current is None:
            self.completed = True
            self._refresh_triage()
            return self._result_payload()

        field = current["field"]

        extracted, extraction_method = self._extract_current_field(
            field,
            response,
        )

        contradiction_detected = bool(
            extracted.pop("__contradiction_detected__", False)
        )
        contradiction_details = extracted.pop("__contradiction_details__", None)

        if field not in extracted or extracted.get(field) in (None, ""):
            extracted = {field: self._fallback_value(field, response)}
            extraction_method = "raw_field_fallback"

        value = extracted[field]

        self.raw_responses.append(
            {
                "index": len(self.raw_responses),
                "field": field,
                "question": current["question"],
                "response": response,
                "patient_response": response,
                "structured": {field: value},
                "extraction_method": extraction_method,
                "adaptive_structured": {},
            }
        )

        confidence = None
        if isinstance(extracted, dict):
            try:
                confidence = float(extracted.get("__ai_confidence__"))
            except (TypeError, ValueError):
                confidence = None

        self.store_extracted_data(
            extracted,
            field,
            response,
            contradiction_detected=contradiction_detected,
            contradiction_details=contradiction_details,
            extraction_method=extraction_method,
            confidence=confidence,
        )

        # Adaptive pass: the same natural-language answer may already contain
        # information for later queued fields. Capture it without changing the
        # deterministic question order.
        adaptive_fields, adaptive_method = self._extract_adaptive_fields(
            response,
            exclude_field=field,
            limit=12,
        )
        if adaptive_fields:
            self._store_adaptive_extractions(
                adaptive_fields,
                response,
                source_field=field,
                extraction_method=adaptive_method,
            )
            self.raw_responses[-1]["adaptive_structured"] = dict(
                adaptive_fields
            )
            self.raw_responses[-1]["structured"].update(adaptive_fields)
            self.raw_responses[-1]["adaptive_extraction_method"] = (
                adaptive_method
            )

        self.question_index += 1
        self._refresh_triage()

        if self._current_question() is None:
            self.completed = True
            self._refresh_triage()

        result = self._result_payload()
        result.update(
            {
                "field": field,
                "question": current["question"],
                "patient_response": response,
                "structured": {
                    field: self.patient_history[
                        self._get_section_for_field(field)
                    ].get(field)
                },
                "extraction_method": extraction_method,
                "next_question": None
                if self.completed
                else self.get_next_question(),
            }
        )
        return result

    def _store_chief_complaint(self, response: str) -> None:
        self.patient_history["chief_complaint"] = response
        self.raw_responses.append(
            {
                "index": len(self.raw_responses),
                "field": "chief_complaint",
                "question": "What is the main problem or symptom that brought you here?",
                "response": response,
                "patient_response": response,
                "structured": {"chief_complaint": response},
                "extraction_method": "direct",
            }
        )

        self.evidence_store.add_patient_fact(
            field="chief_complaint",
            value=response,
            patient_response=response,
            extraction_method="direct",
            raw_response_index=len(self.raw_responses) - 1,
            status="reported",
        )

        try:
            self.complaint_categories = classify_complaint(response)
        except Exception:
            self.complaint_categories = ["general"]

        if not self.complaint_categories:
            self.complaint_categories = ["general"]

        self._build_question_queue()

        # The chief complaint itself can contain explicit onset information.
        try:
            onset = extract_explicit_onset(response)
        except Exception:
            onset = None

        if onset:
            self.patient_history["history_of_present_illness"]["onset"] = onset
            self._record_field_assertion(
                field="onset",
                value=onset,
                patient_response=response,
            )

    # ------------------------------------------------------------------
    # Structured storage + contradiction detection
    # ------------------------------------------------------------------

    def _record_field_assertion(
        self,
        field: str,
        value: Any,
        patient_response: str,
    ) -> None:
        history = self.field_history.setdefault(field, [])

        history.append(
            {
                "value": value,
                "patient_response": patient_response,
                "raw_response_index": self._find_raw_response_index(
                    patient_response,
                    field,
                ),
            }
        )

    def _find_raw_response_index(
        self,
        response: str,
        field: str,
    ) -> Optional[int]:
        for item in reversed(self.raw_responses):
            if (
                item.get("field") == field
                and item.get("response") == response
            ):
                return item.get("index")
        return len(self.raw_responses) - 1 if self.raw_responses else 0

    @staticmethod
    def _normalise_compare(value: Any) -> str:
        return " ".join(str(value).strip().lower().split())

    def _add_contradiction(
        self,
        field: str,
        previous_value: Any,
        current_value: Any,
        previous_statement: str,
        current_statement: str,
        details: Optional[str] = None,
    ) -> None:
        contradiction = {
            "field": field,
            "previous_value": previous_value,
            "current_value": current_value,
            "previous_patient_statement": previous_statement,
            "current_patient_statement": current_statement,
            "details": details
            or "Different patient assertions were recorded for the same clinical field. Physician review is required.",
            "status": "requires_physician_review",
        }

        self.contradictions.append(contradiction)
        self.evidence_store.add_contradiction(
            field=field,
            previous_value=previous_value,
            current_value=current_value,
            previous_statement=previous_statement,
            current_statement=current_statement,
            details=contradiction["details"],
        )
        self.review_required = True

    def store_extracted_data(
        self,
        data: Dict[str, Any],
        field: str,
        patient_response: str,
        contradiction_detected: bool = False,
        contradiction_details: Optional[str] = None,
        extraction_method: str = "direct",
        confidence: Optional[float] = None,
        source_field: Optional[str] = None,
    ) -> None:
        if not isinstance(data, dict) or field not in data:
            return

        current_value = data[field]
        section = self._get_section_for_field(field)

        if field == "chief_complaint":
            return

        if section not in self.patient_history:
            self.patient_history[section] = {}

        current_store = self.patient_history[section]
        existing_value = current_store.get(field)

        # Record every assertion first.
        self._record_field_assertion(
            field=field,
            value=current_value,
            patient_response=patient_response,
        )

        evidence_status = "reported"
        if contradiction_detected:
            evidence_status = "requires_physician_review"

        self.evidence_store.add_patient_fact(
            field=field,
            value=current_value,
            patient_response=patient_response,
            extraction_method=extraction_method,
            confidence=confidence,
            raw_response_index=self._find_raw_response_index(
                patient_response,
                field,
            ),
            source_field=source_field,
            status=evidence_status,
        )

        if existing_value in (None, ""):
            current_store[field] = current_value
            if contradiction_detected:
                self._add_contradiction(
                    field=field,
                    previous_value=None,
                    current_value=current_value,
                    previous_statement="",
                    current_statement=patient_response,
                    details=contradiction_details,
                )
            return

        # AI explicitly detected a contradiction.
        if contradiction_detected:
            previous_statement = self._previous_statement_for_field(
                field,
                existing_value,
                exclude_response=patient_response,
            )
            self._add_contradiction(
                field=field,
                previous_value=existing_value,
                current_value=current_value,
                previous_statement=previous_statement,
                current_statement=patient_response,
                details=contradiction_details,
            )
            return

        # Deterministic/raw conflict detection.
        if self._normalise_compare(existing_value) != self._normalise_compare(
            current_value
        ):
            previous_statement = self._previous_statement_for_field(
                field,
                existing_value,
                exclude_response=patient_response,
            )
            self._add_contradiction(
                field=field,
                previous_value=existing_value,
                current_value=current_value,
                previous_statement=previous_statement,
                current_statement=patient_response,
            )

            # Do NOT overwrite the first structured assertion.
            return

        # Same normalized value: no contradiction and no change needed.

    def _previous_statement_for_field(
        self,
        field: str,
        value: Any,
        exclude_response: Optional[str] = None,
    ) -> str:
        assertions = self.field_history.get(field, [])
        for assertion in reversed(assertions):
            if self._normalise_compare(
                assertion.get("value")
            ) == self._normalise_compare(value):
                statement = assertion.get("patient_response", "")
                if statement != exclude_response:
                    return statement
        return ""

    # ------------------------------------------------------------------
    # Triage
    # ------------------------------------------------------------------

    def _refresh_triage(self) -> None:
        result = detect_red_flags(
            self.patient_history,
            self.raw_responses,
        )

        self.red_flags = result.get("red_flags", [])
        self.triage_required = bool(result.get("triage_required", False))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _result_payload(self) -> Dict[str, Any]:
        return {
            "history": self.patient_history,
            "completed": self.completed,
            "red_flags": self.red_flags,
            "triage_required": self.triage_required,
            "contradictions": self.contradictions,
            "physician_review_required": self.review_required,
            "raw_responses": self.raw_responses,
            "adaptive_extractions": self.adaptive_extractions,
            "clinical_evidence": self.evidence_store.to_dict(),
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "status": "completed" if self.completed else "in_progress",
            "chief_complaint": self.patient_history.get("chief_complaint"),
            "clinical_history": self.patient_history,
            "history": self.patient_history,
            "red_flags": self.red_flags,
            "triage_required": self.triage_required,
            "physician_review_required": self.review_required,
            "contradictions": self.contradictions,
            "patient_statements": self.raw_responses,
            "field_history": self.field_history,
            "adaptive_extractions": self.adaptive_extractions,
            "clinical_evidence": self.evidence_store.to_dict(),
        }