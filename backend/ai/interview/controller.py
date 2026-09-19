from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from backend.ai.clinical_schema import InterviewExtraction
from backend.ai.interview.extractor import InterviewExtractor
from backend.ai.interview.objectives import missing_objectives, normalize_topic
from backend.ai.interview.questions import question_for
from backend.ai.red_flag_engine import detect_red_flags
from backend.config import settings
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import ClinicalSignalType, SessionStatus, Speaker, SummaryStatus
from backend.domain.triage import TriageResult
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_signal import ClinicalSignalService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.conversation import ConversationService
from backend.services.triage import TriageService


class InterviewController:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        conversation_service: ConversationService,
        signal_service: ClinicalSignalService,
        summary_service: ClinicalSummaryService,
        triage_service: TriageService,
        extractor: InterviewExtractor,
    ) -> None:
        self.session_service = session_service
        self.conversation_service = conversation_service
        self.signal_service = signal_service
        self.summary_service = summary_service
        self.triage_service = triage_service
        self.extractor = extractor

    async def get_state(self, session_id: str) -> dict[str, Any]:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        turns = await self.conversation_service.get_session_turns(session_id)

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        signals = await self.signal_service.get_session_signals(session_id)
        known_fields = self._build_known_fields(signals)

        topic = normalize_topic(
            self._value_as_string(
                known_fields.get("symptom_topic"),
            ),
        )

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            known_fields,
        )

        if red_flag_result["triage_required"]:
            next_question = None
            completed = True
        else:
            missing = missing_objectives(topic, known_fields)
            next_question = question_for(missing[0]) if missing else None
            completed = (
                not missing
                or len(patient_turns) >= settings.interview_max_turns
            )

        return {
            "session_id": session_id,
            "topic": topic,
            "known_fields": self._public_fields(known_fields),
            "patient_turns": len(patient_turns),
            "next_question": next_question,
            "completed": completed,
            "red_flags": red_flag_result["red_flags"],
            "ai_enabled": self.extractor.enabled,
        }

    async def process_turn(
        self,
        session_id: str,
        content: str,
        input_type: Any,
        language: str | None,
        turn_id: str,
    ) -> dict[str, Any]:
        text = content.strip()

        if not text:
            raise ValueError("Conversation content is required")

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status not in {
            SessionStatus.CONSENTED,
            SessionStatus.HISTORY_IN_PROGRESS,
        }:
            raise ValueError(
                "Session must be consented or have history in progress")

        if session.status == SessionStatus.CONSENTED:
            updated_session = await self.session_service.transition_session(
                session_id,
                SessionStatus.HISTORY_IN_PROGRESS,
            )

            if updated_session is None:
                raise ValueError(
                    "Clinical session could not enter history state")

            session = updated_session

        existing_turn = await self.conversation_service.get_turn(turn_id)

        if existing_turn is None:
            turn = ConversationTurn(
                turn_id=turn_id,
                session_id=session_id,
                speaker=Speaker.PATIENT,
                input_type=input_type,
                content=text,
                language=language,
                media_reference=None,
            )

            stored_turn = await self.conversation_service.submit_turn(turn)
        else:
            if existing_turn.content != text:
                raise ValueError(
                    "Conversation turn already exists with different content",
                )

            stored_turn = existing_turn

        previous_turns = await self.conversation_service.get_session_turns(
            session_id,
        )

        previous_patient_turns = [
            item
            for item in previous_turns
            if item.speaker == Speaker.PATIENT
            and item.turn_id != stored_turn.turn_id
        ]

        existing_signals = await self.signal_service.get_session_signals(
            session_id,
        )

        known_fields = self._build_known_fields(existing_signals)

        current_topic = normalize_topic(
            self._value_as_string(
                known_fields.get("symptom_topic"),
            ),
        )

        extraction = await self.extractor.extract(
            patient_text=text,
            known_fields=self._public_fields(known_fields),
            topic=current_topic,
        )

        await self._persist_extraction(
            session_id=session_id,
            extraction=extraction,
        )

        signals = await self.signal_service.get_session_signals(session_id)
        known_fields = self._build_known_fields(signals)

        topic = normalize_topic(
            extraction.topic
            or self._value_as_string(
                known_fields.get("symptom_topic"),
            ),
        )

        await self._upsert_signal(
            session_id=session_id,
            name="symptom_topic",
            value=topic,
            signal_type=ClinicalSignalType.SYMPTOM,
            confidence=0.95 if extraction.topic else 0.70,
        )

        signals = await self.signal_service.get_session_signals(session_id)
        known_fields = self._build_known_fields(signals)

        red_flag_result = self._run_red_flag_screen(
            previous_patient_turns + [stored_turn],
            known_fields,
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        if red_flag_result["triage_required"]:
            next_question = None
            completed = True
        else:
            patient_turn_count = len(
                [
                    item
                    for item in previous_turns
                    if item.speaker == Speaker.PATIENT
                ],
            )

            missing = missing_objectives(topic, known_fields)

            completed = (
                not missing
                or patient_turn_count >= settings.interview_max_turns
            )

            next_question = None if completed else question_for(missing[0])

        assistant_response = next_question

        if assistant_response:
            system_turn_id = (
                "ai_"
                + sha256(
                    f"{stored_turn.turn_id}:{assistant_response}".encode(
                        "utf-8",
                    ),
                ).hexdigest()[:24]
            )

            if await self.conversation_service.get_turn(system_turn_id) is None:
                system_turn = ConversationTurn(
                    turn_id=system_turn_id,
                    session_id=session_id,
                    speaker=Speaker.SYSTEM,
                    input_type=input_type,
                    content=assistant_response,
                    language=language,
                    media_reference=None,
                )

                await self.conversation_service.add_turn(system_turn)

        return {
            "turn": stored_turn,
            "assistant_response": assistant_response,
            "next_question": next_question,
            "completed": completed,
            "topic": topic,
            "known_fields": self._public_fields(known_fields),
            "extracted_fields": extraction.fields,
            "negative_fields": extraction.negatives,
            "red_flags": red_flag_result["red_flags"],
            "ai_used": self.extractor.enabled
            and self.extractor.provider == "lemonade",
        }

    async def finalize(self, session_id: str) -> dict[str, Any]:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status not in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError(
                "Clinical session is not ready for interview finalization",
            )

        turns = await self.conversation_service.get_session_turns(session_id)

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        signals = await self.signal_service.get_session_signals(session_id)
        known_fields = self._build_known_fields(signals)

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            known_fields,
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        signals = await self.signal_service.get_session_signals(session_id)
        known_fields = self._build_known_fields(signals)

        summary = await self._upsert_summary(
            session_id=session_id,
            known_fields=known_fields,
        )

        triage = await self.triage_service.get_session_result(session_id)

        if triage is None:
            triage = TriageResult(
                triage_id=f"triage_{uuid4().hex}",
                session_id=session_id,
            )

            triage = await self.triage_service.create_result(triage)

        signals = await self.signal_service.get_session_signals(session_id)

        assessed = await self.triage_service.assess_from_signals(
            triage.triage_id,
            signals,
        )

        if assessed is None:
            raise ValueError(
                "Clinical triage assessment could not be completed",
            )

        final_session = await self.session_service.transition_session(
            session_id,
            SessionStatus.SUMMARY_READY,
        )

        if final_session is None:
            raise ValueError(
                "Clinical session could not enter summary-ready state",
            )

        return {
            "session": final_session,
            "summary": summary,
            "triage": assessed,
        }

    async def _persist_extraction(
        self,
        session_id: str,
        extraction: InterviewExtraction,
    ) -> None:
        if extraction.topic:
            await self._upsert_signal(
                session_id=session_id,
                name="symptom_topic",
                value=normalize_topic(extraction.topic),
                signal_type=ClinicalSignalType.SYMPTOM,
                confidence=0.95,
            )

        for field, value in extraction.fields.items():
            await self._upsert_signal(
                session_id=session_id,
                name=field,
                value=", ".join(map(str, value)) if isinstance(
                    value, list) else value,
                signal_type=self._signal_type_for(field),
                confidence=0.90,
            )

        for field in extraction.negatives:
            await self._upsert_signal(
                session_id=session_id,
                name=field,
                value=False,
                signal_type=self._signal_type_for(field),
                confidence=0.95,
            )

    async def _upsert_signal(
        self,
        session_id: str,
        name: str,
        value: Any,
        signal_type: ClinicalSignalType,
        confidence: float,
    ) -> None:
        signal_id = (
            "sig_"
            + sha256(
                f"{session_id}:{name}".encode("utf-8"),
            ).hexdigest()[:24]
        )

        existing = await self.signal_service.get_signal(signal_id)

        if existing is None:
            signal = ClinicalSignal(
                signal_id=signal_id,
                session_id=session_id,
                signal_type=signal_type,
                name=name,
                value=value,
                confidence=confidence,
                source="interview_ai",
            )

            await self.signal_service.create_signal(signal)
            return

        await self.signal_service.update_signal(
            signal_id,
            {
                "signal_type": signal_type,
                "value": value,
                "confidence": confidence,
                "source": "interview_ai",
                "updated_at": datetime.now(timezone.utc),
            },
        )

    async def _persist_critical_red_flags(
        self,
        session_id: str,
        result: dict[str, Any],
    ) -> None:
        critical_signals = result.get("critical_signals", {})

        for name, value in critical_signals.items():
            if value is True:
                await self._upsert_signal(
                    session_id=session_id,
                    name=name,
                    value=True,
                    signal_type=ClinicalSignalType.RED_FLAG,
                    confidence=1.0,
                )

        signals = await self.signal_service.get_session_signals(session_id)

        severity = next(
            (
                signal.value
                for signal in signals
                if signal.name == "severity"
            ),
            None,
        )

        try:
            numeric_severity = float(severity)
        except (TypeError, ValueError):
            numeric_severity = 0

        if numeric_severity >= 7:
            await self._upsert_signal(
                session_id=session_id,
                name="severe_pain",
                value=True,
                signal_type=ClinicalSignalType.RED_FLAG,
                confidence=1.0,
            )
        elif numeric_severity >= 4:
            await self._upsert_signal(
                session_id=session_id,
                name="moderate_pain",
                value=True,
                signal_type=ClinicalSignalType.SYMPTOM,
                confidence=1.0,
            )

    @staticmethod
    def _signal_type_for(field: str) -> ClinicalSignalType:
        if field == "medications":
            return ClinicalSignalType.MEDICATION

        if field == "allergies":
            return ClinicalSignalType.ALLERGY

        if field == "past_medical_history":
            return ClinicalSignalType.HISTORY

        return ClinicalSignalType.SYMPTOM

    async def _upsert_summary(
        self,
        session_id: str,
        known_fields: dict[str, Any],
    ) -> ClinicalSummary:
        existing = await self.summary_service.get_session_summary(session_id)

        complaint = self._value_as_string(
            known_fields.get("chief_complaint"),
        )

        ordered_hpi_fields = (
            "onset",
            "site",
            "location",
            "severity",
            "character",
            "timing",
            "aggravating_factors",
            "relieving_factors",
            "radiation",
            "associated_symptoms",
            "breathing_difficulty",
            "nausea_vomiting",
            "vision_or_neuro",
            "cough",
            "wheeze",
            "bowel_changes",
            "appearance",
            "itch_or_pain",
            "spread",
            "urinary_frequency",
            "urinary_burning",
            "urinary_blood",
            "fever",
            "fatigue",
            "weight_change",
        )

        hpi_parts: list[str] = []

        for field in ordered_hpi_fields:
            if field not in known_fields:
                continue

            value = known_fields[field]

            if value is None:
                continue

            if isinstance(value, bool):
                text = "yes" if value else "no"
            else:
                text = str(value)

            hpi_parts.append(f"{field.replace('_', ' ')}: {text}")

        history = "; ".join(hpi_parts) if hpi_parts else None

        clinical_signal_names = sorted(
            {
                field
                for field in known_fields
                if field != "symptom_topic"
            }
        )

        values = {
            "status": SummaryStatus.READY,
            "chief_complaint": complaint,
            "history_of_present_illness": history,
            "past_medical_history": self._as_list(
                known_fields.get("past_medical_history"),
            ),
            "medications": self._as_list(
                known_fields.get("medications"),
            ),
            "allergies": self._as_list(
                known_fields.get("allergies"),
            ),
            "clinical_signals": clinical_signal_names,
            "generated_at": datetime.now(timezone.utc),
        }

        if existing is None:
            summary = ClinicalSummary(
                summary_id=f"summary_{uuid4().hex}",
                session_id=session_id,
                **values,
            )

            return await self.summary_service.create_summary(summary)

        updated = await self.summary_service.update_summary(
            existing.summary_id,
            values,
        )

        if updated is None:
            raise ValueError("Clinical summary could not be updated")

        return updated

    @staticmethod
    def _build_known_fields(
        signals: list[ClinicalSignal],
    ) -> dict[str, Any]:
        return {
            signal.name: signal.value
            for signal in signals
        }

    @staticmethod
    def _public_fields(
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            key: value
            for key, value in fields.items()
            if key != "symptom_topic"
        }

    @staticmethod
    def _value_as_string(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        return text or None

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [
                str(item)
                for item in value
                if str(item).strip()
            ]

        text = str(value).strip()

        return [text] if text else []

    @staticmethod
    def _run_red_flag_screen(
        patient_turns: list[ConversationTurn],
        known_fields: dict[str, Any],
    ) -> dict[str, Any]:
        combined_text = " ".join(
            turn.content or ""
            for turn in patient_turns
        )

        return detect_red_flags(
            combined_text,
            known_fields,
        )
