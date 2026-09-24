from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from backend.ai.interview.extractor import InterviewExtractor
from backend.ai.interview.state import (
    AYUSH_SECTION,
    FIELD_PRIMARY_SECTION,
    InterviewState,
    normalize_field_name,
    normalize_section,
)
from backend.ai.red_flag_engine import detect_red_flags
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import (
    ClinicalSignalType,
    ConversationInputType,
    SessionStatus,
    Speaker,
    SummaryStatus,
    UrgencyLevel,
)
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

    async def get_state(
        self,
        session_id: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        session = await self.session_service.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                "Clinical session not found"
            )

        signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        state = self._load_state(
            signals,
            self._is_ayush_department(
                session.department_id
            ),
        )

        turns = (
            await self.conversation_service.get_session_turns(
                session_id
            )
        )

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        response_language = self._normalise_language(
            language
            or next(
                (
                    turn.language
                    for turn in reversed(
                        patient_turns
                    )
                    if turn.language
                ),
                "en",
            )
        )

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            state.known_fields(),
        )

        limit_reached = state.question_limit_reached()
        if limit_reached and not state.is_complete():
            state.complete_remaining_sections()
            await self._persist_state_bundle(
                session_id,
                state,
            )

        completed = bool(
            red_flag_result[
                "triage_required"
            ]
            or state.is_complete()
            or limit_reached
        )

        if (
            not completed
            and state.current_section
            in state.completed_sections
        ):
            state.current_section = (
                state.next_section()
                or state.current_section
            )

        if (
            not completed
            and not state.question_history
        ):
            decision = (
                await self.extractor.generate_question(
                    state,
                    self._conversation_for_ai(
                        turns
                    ),
                    response_language,
                    session_id,
                )
            )

            state.add_question(
                decision.question,
                decision.target,
            )

            await self._persist_state_bundle(
                session_id,
                state,
            )

            await self._store_assistant_question(
                session_id,
                decision.question,
                response_language,
            )

        latest_question = (
            state.question_history[-1]
            if state.question_history
            else None
        )

        return {
            "session_id": session_id,
            "topic": state.topic,
            "known_fields": state.known_fields(),
            "patient_turns": len(
                patient_turns
            ),
            "next_question": (
                None
                if completed
                else latest_question
            ),
            "completed": completed,
            "red_flags": red_flag_result[
                "red_flags"
            ],
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
            raise ValueError(
                "Conversation content is required"
            )

        session = await self.session_service.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                "Clinical session not found"
            )

        if session.status not in {
            SessionStatus.CONSENTED,
            SessionStatus.HISTORY_IN_PROGRESS,
        }:
            raise ValueError(
                "Session must be consented or have history in progress"
            )

        if session.status == SessionStatus.CONSENTED:
            transitioned = (
                await self.session_service.transition_session(
                    session_id,
                    SessionStatus.HISTORY_IN_PROGRESS,
                )
            )

            if transitioned is None:
                raise ValueError(
                    "Clinical session could not enter history-in-progress state"
                )

        existing_turn = (
            await self.conversation_service.get_turn(
                turn_id
            )
        )

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

            stored_turn = (
                await self.conversation_service.submit_turn(
                    turn
                )
            )
        else:
            if existing_turn.content != text:
                raise ValueError(
                    "Conversation turn already exists with different content"
                )

            stored_turn = existing_turn

        signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        state = self._load_state(
            signals,
            self._is_ayush_department(
                session.department_id
            ),
        )

        state.turn_count += 1

        turns = (
            await self.conversation_service.get_session_turns(
                session_id
            )
        )

        response_language = self._normalise_language(
            language
            or next(
                (
                    item.language
                    for item in reversed(
                        turns
                    )
                    if item.language
                ),
                "en",
            )
        )

        pending_before = state._split_targets(state.pending_target)

        facts = self.extractor.extract_facts(
            text,
            state,
            turn_id,
        )

        if facts:
            state.add_facts(
                facts,
                text,
                turn_id,
            )

        pending_answered = any(
            state.target_answered(target)
            for target in pending_before
        )

        if pending_before and pending_answered:
            state.unproductive_turns = 0
        else:
            state.unproductive_turns += 1
            if state.unproductive_turns >= 1:
                state.skip_pending_targets()
                state.unproductive_turns = 0

        topic = self.extractor.detect_topic(
            text
        )

        if (
            topic
            and (
                not state.topic
                or state.topic == "general"
            )
        ):
            state.topic = topic

        await self._persist_triage_signals(
            session_id,
            state,
        )

        turns = (
            await self.conversation_service.get_session_turns(
                session_id
            )
        )

        patient_turns = [
            item
            for item in turns
            if item.speaker == Speaker.PATIENT
        ]

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            state.known_fields(),
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        completed = False
        assistant_response: str | None = None
        next_question: str | None = None
        ai_used = False

        if red_flag_result["triage_required"]:
            completed = True
            assistant_response = self._red_flag_message(
                response_language
            )
            state.pending_target = None

        else:
            # Hard upper bound: adaptive questioning must never turn into an
            # open-ended checklist.
            if state.question_limit_reached():
                state.complete_remaining_sections()
                completed = True
                assistant_response = self._completion_message(
                    response_language
                )
            else:
                # Never close a section solely because its question budget
                # was reached. Budgets help keep the interview efficient, while
                # readiness is determined by the information actually collected.
                should_advance = state.section_naturally_ready()

                if should_advance:
                    state.complete_current_section()

                if (
                    not should_advance
                    and not state.candidate_targets()
                ):
                    state.complete_current_section()

                if not state.is_complete():
                    decision = (
                        await self.extractor.generate_question(
                            state,
                            self._conversation_for_ai(
                                turns
                            ),
                            response_language,
                            session_id,
                        )
                    )

                    if decision.question:
                        next_question = (
                            decision.question
                        )
                        assistant_response = (
                            decision.question
                        )
                        ai_used = (
                            decision.ai_used
                        )

                        state.add_question(
                            decision.question,
                            decision.target,
                        )

            if state.is_complete():
                completed = True
                next_question = None
                assistant_response = (
                    self._completion_message(
                        response_language
                    )
                )

        await self._persist_clinical_facts(
            session_id,
            state,
            turn_id,
        )

        await self._persist_state_bundle(
            session_id,
            state,
        )

        if completed:
            await self._upsert_signal(
                session_id=session_id,
                name="_interview_completed",
                value=True,
                signal_type=ClinicalSignalType.OTHER,
                confidence=1.0,
            )

        if assistant_response:
            await self._store_assistant_question(
                session_id,
                assistant_response,
                response_language,
            )

        extracted = {
            fact["field"]: fact["value"]
            for fact in facts
            if not fact.get(
                "negative"
            )
        }

        negatives = [
            fact["field"]
            for fact in facts
            if fact.get(
                "negative"
            )
        ]

        return {
            "turn": stored_turn,
            "assistant_response": assistant_response,
            "next_question": next_question,
            "completed": completed,
            "topic": state.topic,
            "known_fields": state.known_fields(),
            "extracted_fields": extracted,
            "negative_fields": negatives,
            "red_flags": red_flag_result[
                "red_flags"
            ],
            "ai_used": ai_used,
        }

    async def finalize(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        session = await self.session_service.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                "Clinical session not found"
            )

        if session.status not in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError(
                "Clinical session is not ready for interview finalization"
            )

        signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        state = self._load_state(
            signals,
            self._is_ayush_department(
                session.department_id
            ),
        )

        turns = (
            await self.conversation_service.get_session_turns(
                session_id
            )
        )

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            state.known_fields(),
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        if (
            not state.is_complete()
            and not red_flag_result[
                "triage_required"
            ]
        ):
            raise ValueError(
                "Interview is not complete"
            )

        await self._persist_triage_signals(
            session_id,
            state,
        )

        signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        state = self._load_state(
            signals,
            self._is_ayush_department(
                session.department_id
            ),
        )

        known_fields = state.known_fields()

        summary = await self._upsert_summary(
            session_id,
            state,
            known_fields,
        )

        triage = (
            await self.triage_service.get_session_result(
                session_id
            )
        )

        if triage is None:
            triage = TriageResult(
                triage_id=f"triage_{uuid4().hex}",
                session_id=session_id,
                urgency_level=UrgencyLevel.LEVEL_1,
                priority_score=20,
                red_flags_present=bool(
                    red_flag_result[
                        "red_flags"
                    ]
                ),
            )

            triage = (
                await self.triage_service.create_result(
                    triage
                )
            )

        signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        assessed = (
            await self.triage_service.assess_from_signals(
                triage.triage_id,
                signals,
            )
        )

        if assessed is None:
            raise ValueError(
                "Clinical triage assessment could not be completed"
            )

        final_session = (
            await self.session_service.transition_session(
                session_id,
                SessionStatus.SUMMARY_READY,
            )
        )

        if final_session is None:
            raise ValueError(
                "Clinical session could not enter summary-ready state"
            )

        return {
            "session": final_session,
            "summary": summary,
            "triage": assessed,
        }

    @staticmethod
    def _normalise_language(
        language: str | None,
    ) -> str:
        value = str(
            language or "en"
        ).strip().lower()

        if value.startswith("hi") or value.startswith("hin"):
            return "hi"

        if value.startswith("en") or value.startswith("eng"):
            return "en"

        return "en"

    @staticmethod
    def _is_ayush_department(
        department_id: str | None,
    ) -> bool:
        value = str(
            department_id or ""
        ).lower()

        return any(
            term in value
            for term in (
                "ayush",
                "ayur",
                "ayurveda",
            )
        )

    @staticmethod
    def _load_state(
        signals: list[ClinicalSignal],
        ayush_enabled: bool,
    ) -> InterviewState:
        values = {
            signal.name: signal.value
            for signal in signals
        }

        return InterviewState.from_value(
            values.get(
                "_interview_state"
            ),
            legacy_fields=values,
            ayush_enabled=ayush_enabled,
        )

    async def _persist_triage_signals(
        self,
        session_id: str,
        state: InterviewState,
    ) -> None:
        known = state.known_fields()

        try:
            severity = float(
                known.get(
                    "severity",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            severity = 0

        if severity >= 7:
            await self._upsert_signal(
                session_id,
                "severe_pain",
                True,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )
            await self._upsert_signal(
                session_id,
                "moderate_pain",
                False,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )

        elif severity >= 4:
            await self._upsert_signal(
                session_id,
                "severe_pain",
                False,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )
            await self._upsert_signal(
                session_id,
                "moderate_pain",
                True,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )

        elif severity > 0:
            await self._upsert_signal(
                session_id,
                "severe_pain",
                False,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )
            await self._upsert_signal(
                session_id,
                "moderate_pain",
                False,
                ClinicalSignalType.SYMPTOM,
                1.0,
            )

        duration = str(
            known.get(
                "duration"
            )
            or ""
        ).lower()

        course = str(
            known.get(
                "course"
            )
            or ""
        ).lower()

        persistent = bool(
            duration
            and (
                "week" in duration
                or "month" in duration
                or "year" in duration
                or course in {
                    "unchanged",
                    "worsening",
                    "persistent",
                }
            )
        )

        await self._upsert_signal(
            session_id,
            "persistent_symptoms",
            persistent,
            ClinicalSignalType.SYMPTOM,
            1.0,
        )

    async def _persist_clinical_facts(
        self,
        session_id: str,
        state: InterviewState,
        turn_id: str,
    ) -> None:
        existing_values = {
            signal.name: signal.value
            for signal in (
                await self.signal_service.get_session_signals(
                    session_id
                )
            )
        }

        for fact in state.facts:
            if fact.get(
                "turn_id"
            ) != turn_id:
                continue

            field = normalize_field_name(
                fact.get("field")
            )

            if field.startswith(
                "custom_"
            ):
                continue

            value = (
                False
                if fact.get(
                    "negative"
                )
                else fact.get(
                    "value"
                )
            )

            if value is None:
                continue

            existing = existing_values.get(
                field
            )

            final_value = self._merge_signal_value(
                field,
                existing,
                value,
            )

            section = (
                FIELD_PRIMARY_SECTION.get(
                    field,
                    normalize_section(
                        fact.get(
                            "section"
                        )
                    ),
                )
            )

            if (
                field == "onset"
                and section != "hpi"
            ):
                continue

            await self._upsert_signal(
                session_id,
                field,
                final_value,
                self._signal_type_for(
                    field
                ),
                0.95
                if fact.get(
                    "negative"
                )
                else 0.9,
            )

            existing_values[field] = final_value

    @staticmethod
    def _merge_signal_value(
        field: str,
        existing: Any,
        new_value: Any,
    ) -> Any:
        if new_value is None:
            return existing

        if (
            existing is None
            or existing is False
            or existing is True
        ):
            return new_value

        if field not in {
            "past_medical_history",
            "past_surgical_history",
            "hospitalizations",
            "immunizations",
            "medications",
            "allergies",
            "adverse_drug_reactions",
            "family_history",
            "personal_history",
            "associated_symptoms",
            "prior_treatment",
            "prior_investigations",
            "review_of_systems",
            "aggravating_factors",
            "relieving_factors",
            "radiation",
        }:
            return new_value

        values: list[str] = []

        for source in (
            existing,
            new_value,
        ):
            for item in (
                source
                if isinstance(
                    source,
                    list,
                )
                else [source]
            ):
                value = str(
                    item
                ).strip()

                if (
                    value
                    and value not in values
                ):
                    values.append(
                        value
                    )

        return (
            values[0]
            if len(values) == 1
            else ", ".join(values)
        )

    async def _persist_state_bundle(
        self,
        session_id: str,
        state: InterviewState,
    ) -> None:
        await self._upsert_signal(
            session_id,
            "_interview_state",
            state.to_value(),
            ClinicalSignalType.OTHER,
            1.0,
        )

        await self._upsert_signal(
            session_id,
            "_interview_section",
            state.current_section,
            ClinicalSignalType.OTHER,
            1.0,
        )

        await self._upsert_signal(
            session_id,
            "_interview_completed_sections",
            json.dumps(
                sorted(
                    state.completed_sections
                ),
                ensure_ascii=False,
            ),
            ClinicalSignalType.OTHER,
            1.0,
        )

    async def _store_assistant_question(
        self,
        session_id: str,
        question: str,
        language: str,
    ) -> None:
        turn_id = (
            "ai_"
            + sha256(
                f"{session_id}:{question}".encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        if (
            await self.conversation_service.get_turn(
                turn_id
            )
            is not None
        ):
            return

        await self.conversation_service.add_turn(
            ConversationTurn(
                turn_id=turn_id,
                session_id=session_id,
                speaker=Speaker.SYSTEM,
                input_type=ConversationInputType.TEXT,
                content=question,
                language=language,
                media_reference=None,
            )
        )

    async def _persist_critical_red_flags(
        self,
        session_id: str,
        result: dict[str, Any],
    ) -> None:
        for name, value in result.get(
            "critical_signals",
            {},
        ).items():
            if value is True:
                await self._upsert_signal(
                    session_id,
                    name,
                    True,
                    ClinicalSignalType.RED_FLAG,
                    1.0,
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
                f"{session_id}:{name}".encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        existing = (
            await self.signal_service.get_signal(
                signal_id
            )
        )

        signal_value = self._signal_value(
            value
        )

        if existing is None:
            await self.signal_service.create_signal(
                ClinicalSignal(
                    signal_id=signal_id,
                    session_id=session_id,
                    signal_type=signal_type,
                    name=name,
                    value=signal_value,
                    confidence=confidence,
                    source="interview_ai",
                )
            )
            return

        await self.signal_service.update_signal(
            signal_id,
            {
                "signal_type": signal_type,
                "value": signal_value,
                "confidence": confidence,
                "source": "interview_ai",
                "updated_at": datetime.now(
                    timezone.utc
                ),
            },
        )

    @staticmethod
    def _signal_value(
        value: Any,
    ) -> str | bool | int | float | None:
        if (
            isinstance(
                value,
                (
                    bool,
                    int,
                    float,
                ),
            )
            or value is None
        ):
            return value

        if isinstance(
            value,
            list,
        ):
            return ", ".join(
                str(item)
                for item in value
                if str(item).strip()
            )

        if isinstance(
            value,
            dict,
        ):
            return json.dumps(
                value,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            )

        return (
            str(value).strip()
            or None
        )

    @staticmethod
    def _signal_type_for(
        field: str,
    ) -> ClinicalSignalType:
        if field.startswith("ayush_"):
            return ClinicalSignalType.HISTORY

        if field == "medications":
            return ClinicalSignalType.MEDICATION

        if field in {
            "allergies",
            "adverse_drug_reactions",
        }:
            return ClinicalSignalType.ALLERGY

        if field in {
            "past_medical_history",
            "past_surgical_history",
            "hospitalizations",
            "immunizations",
        }:
            return ClinicalSignalType.HISTORY

        if field in {
            "onset",
            "duration",
        }:
            return ClinicalSignalType.DURATION

        return ClinicalSignalType.SYMPTOM

    @staticmethod
    def _conversation_for_ai(
        turns: list[ConversationTurn],
    ) -> list[dict[str, Any]]:
        return [
            {
                "role": (
                    "patient"
                    if turn.speaker
                    == Speaker.PATIENT
                    else "assistant"
                ),
                "content": (
                    turn.content or ""
                ),
                "language": turn.language,
            }
            for turn in turns
            if turn.speaker
            in {
                Speaker.PATIENT,
                Speaker.SYSTEM,
            }
        ][-6:]

    @staticmethod
    def _run_red_flag_screen(
        patient_turns: list[ConversationTurn],
        known_fields: dict[str, Any],
    ) -> dict[str, Any]:
        return detect_red_flags(
            " ".join(
                turn.content or ""
                for turn in patient_turns
            ),
            known_fields,
        )

    async def _upsert_summary(
        self,
        session_id: str,
        state: InterviewState,
        known_fields: dict[str, Any],
    ) -> ClinicalSummary:
        existing = (
            await self.summary_service.get_session_summary(
                session_id
            )
        )

        complaint = self._value_as_string(
            known_fields.get(
                "chief_complaint"
            )
        )

        section_values = (
            (
                "HPI",
                state.render_section(
                    "hpi"
                ),
            ),
            (
                "Past history",
                state.render_section(
                    "past_history"
                ),
            ),
            (
                "Drug and allergy history",
                state.render_section(
                    "drug_allergy"
                ),
            ),
            (
                "Family history",
                state.render_section(
                    "family_history"
                ),
            ),
            (
                "Personal history",
                state.render_section(
                    "personal_history"
                ),
            ),
            (
                "Review of systems",
                state.render_section(
                    "review_of_systems"
                ),
            ),
            (
                "AYUSH history",
                state.render_section(
                    "ayush"
                ),
            ),
        )

        history = (
            "\n".join(
                f"{label}: {value}"
                for label, value
                in section_values
                if value
            )
            or None
        )

        past_medical_history = (
            self._as_list(
                known_fields.get(
                    "past_medical_history"
                )
            )
            + self._as_list(
                known_fields.get(
                    "past_surgical_history"
                )
            )
        )

        if (
            not past_medical_history
            and state.render_section(
                "past_history"
            )
        ):
            past_medical_history = [
                state.render_section(
                    "past_history"
                )
            ]

        medications = self._as_list(
            known_fields.get(
                "medications"
            )
        )

        allergies = self._as_list(
            known_fields.get(
                "allergies"
            )
        )

        clinical_signal_names = sorted(
            {
                str(
                    fact.get(
                        "field"
                    )
                )
                for fact in state.facts
                if fact.get(
                    "field"
                )
                and not str(
                    fact.get(
                        "field"
                    )
                ).startswith(
                    "custom_"
                )
                and not str(
                    fact.get(
                        "field"
                    )
                ).startswith(
                    "_"
                )
            }
        )

        values = {
            "status": SummaryStatus.READY,
            "chief_complaint": complaint,
            "history_of_present_illness": history,
            "past_medical_history": past_medical_history,
            "medications": medications,
            "allergies": allergies,
            "clinical_signals": clinical_signal_names,
            "generated_at": datetime.now(
                timezone.utc
            ),
        }

        if existing is None:
            return (
                await self.summary_service.create_summary(
                    ClinicalSummary(
                        summary_id=f"summary_{uuid4().hex}",
                        session_id=session_id,
                        **values,
                    )
                )
            )

        updated = (
            await self.summary_service.update_summary(
                existing.summary_id,
                values,
            )
        )

        if updated is None:
            raise ValueError(
                "Clinical summary could not be updated"
            )

        return updated

    @staticmethod
    def _as_list(
        value: Any,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return [
                str(item)
                for item in value
                if str(item).strip()
            ]

        value_text = str(
            value
        ).strip()

        return (
            [value_text]
            if value_text
            else []
        )

    @staticmethod
    def _value_as_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        value_text = str(
            value
        ).strip()

        return (
            value_text
            or None
        )

    @staticmethod
    def _red_flag_message(
        language: str | None,
    ) -> str:
        if language == "hi":
            return (
                "आपकी जानकारी दर्ज कर ली गई है। कृपया आगे बढ़ें ताकि स्वास्थ्यकर्मी इसकी जल्द समीक्षा कर सकें।"
            )

        return (
            "I have recorded what you shared. Please continue so a healthcare professional can review it promptly."
        )

    @staticmethod
    def _completion_message(
        language: str | None,
    ) -> str:
        if language == "hi":
            return (
                "धन्यवाद। आपकी मेडिकल हिस्ट्री दर्ज कर ली गई है।"
            )

        return (
            "Thank you. Your medical history has been recorded."
        )