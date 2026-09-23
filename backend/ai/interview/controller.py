from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from backend.ai.interview.extractor import (
    InterviewExtractor,
    InterviewPlan,
)
from backend.ai.interview.state import (
    FIELD_PRIMARY_SECTION,
    REQUIRED_SECTIONS,
    STATE_SIGNAL_NAME,
    InterviewState,
    normalize_field_name,
    normalize_section,
)
from backend.ai.red_flag_engine import detect_red_flags
from backend.config import settings
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import (
    ClinicalSignalType,
    SessionStatus,
    Speaker,
    SummaryStatus,
    UrgencyLevel,
)
from backend.domain.triage import TriageResult
from backend.services.clinical_session import (
    ClinicalSessionService,
)
from backend.services.clinical_signal import (
    ClinicalSignalService,
)
from backend.services.clinical_summary import (
    ClinicalSummaryService,
)
from backend.services.conversation import (
    ConversationService,
)
from backend.services.triage import (
    TriageService,
)


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
    ) -> dict[str, Any]:
        session = await self.session_service.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                "Clinical session not found"
            )

        signals = await self.signal_service.get_session_signals(
            session_id
        )

        state = self._load_state(
            signals
        )

        turns = await self.conversation_service.get_session_turns(
            session_id
        )

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        known_fields = state.known_fields()

        red_flags = self._run_red_flag_screen(
            patient_turns,
            known_fields,
        )

        completed = (
            REQUIRED_SECTIONS.issubset(
                state.completed_sections
            )
            or red_flags[
                "triage_required"
            ]
        )

        latest_question = (
            state.question_history[-1]
            if state.question_history
            else None
        )

        self._debug(
            "STATE",
            session_id=session_id,
            topic=state.topic,
            section=state.current_section,
            completed_sections=sorted(
                state.completed_sections
            ),
            known_fields=known_fields,
            patient_turns=len(
                patient_turns
            ),
            next_question=latest_question,
            completed=completed,
            red_flags=red_flags[
                "red_flags"
            ],
        )

        return {
            "session_id": session_id,
            "topic": state.topic,
            "known_fields": known_fields,
            "patient_turns": len(
                patient_turns
            ),
            "next_question": (
                None
                if completed
                else latest_question
            ),
            "completed": completed,
            "red_flags": red_flags[
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

        self._debug(
            "TURN_RECEIVED",
            session_id=session_id,
            turn_id=turn_id,
            content=text,
            input_type=str(
                input_type
            ),
            language=language,
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

        existing_turn = await self.conversation_service.get_turn(
            turn_id
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

        signals = await self.signal_service.get_session_signals(
            session_id
        )

        state = self._load_state(
            signals
        )

        state_before = self._state_debug_value(
            state
        )

        turns = await self.conversation_service.get_session_turns(
            session_id
        )

        response_language = (
            language
            or next(
                (
                    turn.language
                    for turn in reversed(
                        turns
                    )
                    if turn.language
                ),
                "en",
            )
        )

        plan = await self.extractor.plan(
            patient_text=text,
            state=state,
            conversation=self._conversation_for_ai(
                turns
            ),
            language=response_language,
            session_id=session_id,
            turn_id=turn_id,
        )

        self._apply_plan(
            state=state,
            plan=plan,
            patient_text=text,
            turn_id=turn_id,
        )

        known_fields = state.known_fields()

        self._debug(
            "STATE_AFTER_PLAN",
            session_id=session_id,
            turn_id=turn_id,
            before=state_before,
            after=self._state_debug_value(
                state
            ),
            plan=self.extractor.plan_dict(
                plan
            ),
        )

        await self._persist_clinical_facts(
            session_id=session_id,
            state=state,
            turn_id=turn_id,
            patient_text=text,
        )

        state.current_section = (
            self._resolve_next_section(
                state=state,
                plan=plan,
            )
        )

        completed = (
            REQUIRED_SECTIONS.issubset(
                state.completed_sections
            )
        )

        if (
            plan.completed
            and not completed
        ):
            self._debug(
                "MODEL_COMPLETION_OVERRIDDEN",
                session_id=session_id,
                turn_id=turn_id,
                completed_sections=sorted(
                    state.completed_sections
                ),
            )

        red_flag_result = self._run_red_flag_screen(
            [
                turn
                for turn in turns
                if turn.speaker
                == Speaker.PATIENT
            ],
            known_fields,
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        if red_flag_result[
            "triage_required"
        ]:
            completed = True

            await self._upsert_signal(
                session_id=session_id,
                name="_interview_completed",
                value=True,
                signal_type=ClinicalSignalType.OTHER,
                confidence=1.0,
            )

            assistant_response = (
                self._red_flag_message(
                    response_language
                )
            )

            next_question = None

        elif completed:
            assistant_response = (
                self._completion_message(
                    response_language
                )
            )

            next_question = None

        else:
            next_question = self._select_question(
                plan=plan,
                state=state,
                language=response_language,
            )

            assistant_response = next_question

        state.add_question(
            next_question
        )

        await self._persist_state(
            session_id,
            state,
        )

        await self._upsert_signal(
            session_id=session_id,
            name="_interview_section",
            value=state.current_section,
            signal_type=ClinicalSignalType.OTHER,
            confidence=1.0,
        )

        await self._upsert_signal(
            session_id=session_id,
            name="_interview_completed_sections",
            value=json.dumps(
                sorted(
                    state.completed_sections
                ),
                ensure_ascii=False,
            ),
            signal_type=ClinicalSignalType.OTHER,
            confidence=1.0,
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
            system_turn_id = (
                "ai_"
                + sha256(
                    (
                        f"{stored_turn.turn_id}:"
                        f"{assistant_response}"
                    ).encode(
                        "utf-8"
                    ),
                ).hexdigest()[:24]
            )

            if (
                await self.conversation_service.get_turn(
                    system_turn_id
                )
                is None
            ):
                system_turn = ConversationTurn(
                    turn_id=system_turn_id,
                    session_id=session_id,
                    speaker=Speaker.SYSTEM,
                    input_type=input_type,
                    content=assistant_response,
                    language=response_language,
                    media_reference=None,
                )

                await self.conversation_service.add_turn(
                    system_turn
                )

        known_fields = state.known_fields()

        self._debug(
            "TURN_RESULT",
            session_id=session_id,
            turn_id=turn_id,
            topic=state.topic,
            section=state.current_section,
            completed_sections=sorted(
                state.completed_sections
            ),
            known_fields=known_fields,
            next_question=next_question,
            completed=completed,
            red_flags=red_flag_result[
                "red_flags"
            ],
            ai_used=plan.ai_used,
        )

        return {
            "turn": stored_turn,
            "assistant_response": assistant_response,
            "next_question": next_question,
            "completed": completed,
            "topic": state.topic,
            "known_fields": known_fields,
            "extracted_fields": {
                fact["field"]: fact["value"]
                for fact in plan.facts
                if not fact.get(
                    "negative"
                )
            },
            "negative_fields": [
                fact["field"]
                for fact in plan.facts
                if fact.get(
                    "negative"
                )
            ],
            "red_flags": red_flag_result[
                "red_flags"
            ],
            "ai_used": plan.ai_used,
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

        signals = await self.signal_service.get_session_signals(
            session_id
        )

        state = self._load_state(
            signals
        )

        if not REQUIRED_SECTIONS.issubset(
            state.completed_sections
        ):
            raise ValueError(
                "Interview is not complete"
            )

        turns = await self.conversation_service.get_session_turns(
            session_id
        )

        patient_turns = [
            turn
            for turn in turns
            if turn.speaker == Speaker.PATIENT
        ]

        known_fields = state.known_fields()

        red_flag_result = self._run_red_flag_screen(
            patient_turns,
            known_fields,
        )

        await self._persist_critical_red_flags(
            session_id,
            red_flag_result,
        )

        signals = await self.signal_service.get_session_signals(
            session_id
        )

        state = self._load_state(
            signals
        )

        known_fields = state.known_fields()

        summary = await self._upsert_summary(
            session_id=session_id,
            state=state,
            known_fields=known_fields,
        )

        triage = await self.triage_service.get_session_result(
            session_id
        )

        if triage is None:
            triage = TriageResult(
                triage_id=f"triage_{uuid4().hex}",
                session_id=session_id,
                urgency_level=UrgencyLevel.LEVEL_1,
                priority_score=20,
                red_flags_present=False,
            )

            triage = (
                await self.triage_service.create_result(
                    triage
                )
            )

        signals = await self.signal_service.get_session_signals(
            session_id
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

        self._debug(
            "INTERVIEW_FINALIZED",
            session_id=session_id,
            completed_sections=sorted(
                state.completed_sections
            ),
            known_fields=known_fields,
        )

        return {
            "session": final_session,
            "summary": summary,
            "triage": assessed,
        }

    def _apply_plan(
        self,
        state: InterviewState,
        plan: InterviewPlan,
        patient_text: str,
        turn_id: str,
    ) -> None:
        if plan.topic:
            state.topic = (
                str(
                    plan.topic
                ).strip()
                or state.topic
            )

        state.add_facts(
            facts=plan.facts or [],
            evidence=patient_text,
            turn_id=turn_id,
        )

        validated_sections = (
            self._validated_completed_sections(
                state,
                plan.completed_sections,
            )
        )

        state.mark_sections(
            validated_sections
        )

        if (
            plan.completed
            and not plan.completed_sections
            and self._section_has_current_turn_data(
                state,
                turn_id,
                state.current_section,
            )
        ):
            state.mark_sections(
                [state.current_section]
            )

    @staticmethod
    def _validated_completed_sections(
        state: InterviewState,
        sections: list[str] | None,
    ) -> list[str]:
        available: list[str] = []

        for section in sections or []:
            normalized = normalize_section(
                section
            )

            if normalized == "ayush":
                if state.section_facts(
                    "ayush"
                ):
                    available.append(
                        "ayush"
                    )

                continue

            if state.section_facts(
                normalized
            ):
                available.append(
                    normalized
                )

        return list(
            dict.fromkeys(
                available
            )
        )

    @staticmethod
    def _section_has_current_turn_data(
        state: InterviewState,
        turn_id: str,
        section: str,
    ) -> bool:
        normalized = normalize_section(
            section
        )

        return any(
            fact.get(
                "turn_id"
            ) == turn_id
            and normalize_section(
                fact.get(
                    "section"
                )
            )
            == normalized
            for fact in state.facts
        )

    @staticmethod
    def _resolve_next_section(
        state: InterviewState,
        plan: InterviewPlan,
    ) -> str:
        current = normalize_section(
            state.current_section
        )

        if (
            current
            not in state.completed_sections
            and plan.section
            != current
        ):
            return current

        candidate = normalize_section(
            plan.section
        )

        if (
            candidate
            not in state.completed_sections
        ):
            return candidate

        for section in (
            "hpi",
            "past_history",
            "drug_allergy",
            "family_history",
            "personal_history",
            "review_of_systems",
        ):
            if (
                section
                not in state.completed_sections
            ):
                return section

        return current

    def _select_question(
        self,
        plan: InterviewPlan,
        state: InterviewState,
        language: str | None,
    ) -> str:
        candidate = (
            plan.next_question
            or ""
        ).strip()

        previous = (
            state.question_history[-1]
            if state.question_history
            else None
        )

        if (
            candidate
            and previous
            and candidate.lower()
            == previous.lower()
        ):
            candidate = ""

        if (
            candidate
            and candidate.count(
                "?"
            )
            > 1
        ):
            candidate = ""

        if (
            candidate
            and self._looks_compound(
                candidate
            )
        ):
            candidate = ""

        if candidate:
            return candidate

        return self.extractor._fallback_question(
            state=state,
            section=state.current_section,
            language=language,
        )

    @staticmethod
    def _looks_compound(
        question: str,
    ) -> bool:
        lower = question.lower()

        groups = (
            (
                "medicine",
                "medication",
                "drug",
                "supplement",
                "दवा",
            ),
            (
                "allerg",
                "food",
                "एलर्जी",
            ),
            (
                "smoking",
                "tobacco",
                "alcohol",
                "धूम्रपान",
                "तंबाकू",
                "शराब",
            ),
        )

        matched = sum(
            any(
                word in lower
                for word in group
            )
            for group in groups
        )

        return matched > 1

    async def _persist_clinical_facts(
        self,
        session_id: str,
        state: InterviewState,
        turn_id: str,
        patient_text: str,
    ) -> None:
        existing_signals = (
            await self.signal_service.get_session_signals(
                session_id
            )
        )

        existing_values = {
            signal.name: signal.value
            for signal in existing_signals
        }

        for fact in state.facts[-50:]:
            if fact.get(
                "turn_id"
            ) != turn_id:
                continue

            field = normalize_field_name(
                fact.get(
                    "field"
                )
            )

            if field.startswith(
                "custom_"
            ):
                continue

            value = fact.get(
                "value"
            )

            if fact.get(
                "negative"
            ):
                value = False

            field_section = FIELD_PRIMARY_SECTION.get(
                field,
                normalize_section(
                    fact.get(
                        "section"
                    )
                ),
            )

            if field == "onset":
                if (
                    field_section
                    != "hpi"
                ):
                    continue

                if not self._hpi_duration_context(
                    patient_text
                ):
                    continue

            existing_value = existing_values.get(
                field
            )

            final_value = self._merge_signal_value(
                field,
                existing_value,
                value,
            )

            await self._upsert_signal(
                session_id=session_id,
                name=field,
                value=final_value,
                signal_type=self._signal_type_for(
                    field
                ),
                confidence=(
                    0.95
                    if fact.get(
                        "negative"
                    )
                    else 0.90
                ),
            )

            existing_values[field] = final_value

    @staticmethod
    def _hpi_duration_context(
        text: str,
    ) -> bool:
        lower = text.lower()

        historical_context = any(
            phrase in lower
            for phrase in (
                "surgery",
                "operation",
                "operated",
                "hospital",
            )
        )

        explicit_symptom_context = any(
            phrase in lower
            for phrase in (
                "symptom",
                "pain",
                "problem",
                "started",
                "began",
                "since",
                "for",
                "constipat",
                "cough",
                "headache",
            )
        )

        if (
            historical_context
            and not explicit_symptom_context
        ):
            return False

        return True

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

        multi_value_fields = {
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
        }

        if field not in multi_value_fields:
            return new_value

        values: list[str] = []

        for source in (
            existing,
            new_value,
        ):
            items = (
                source
                if isinstance(
                    source,
                    list,
                )
                else [source]
            )

            for item in items:
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

    async def _persist_state(
        self,
        session_id: str,
        state: InterviewState,
    ) -> None:
        await self._upsert_signal(
            session_id=session_id,
            name=STATE_SIGNAL_NAME,
            value=state.to_value(),
            signal_type=ClinicalSignalType.OTHER,
            confidence=1.0,
        )

    async def _persist_critical_red_flags(
        self,
        session_id: str,
        result: dict[str, Any],
    ) -> None:
        critical_signals = result.get(
            "critical_signals",
            {},
        )

        for name, value in critical_signals.items():
            if value is True:
                await self._upsert_signal(
                    session_id=session_id,
                    name=name,
                    value=True,
                    signal_type=ClinicalSignalType.RED_FLAG,
                    confidence=1.0,
                )

        signals = await self.signal_service.get_session_signals(
            session_id
        )

        severity = next(
            (
                signal.value
                for signal in signals
                if signal.name == "severity"
            ),
            None,
        )

        try:
            numeric_severity = float(
                severity
            )
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
                ),
            ).hexdigest()[:24]
        )

        existing = await self.signal_service.get_signal(
            signal_id
        )

        if existing is None:
            await self.signal_service.create_signal(
                ClinicalSignal(
                    signal_id=signal_id,
                    session_id=session_id,
                    signal_type=signal_type,
                    name=name,
                    value=self._signal_value(
                        value
                    ),
                    confidence=confidence,
                    source="interview_ai",
                )
            )

            return

        await self.signal_service.update_signal(
            signal_id,
            {
                "signal_type": signal_type,
                "value": self._signal_value(
                    value
                ),
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
        if isinstance(
            value,
            bool,
        ):
            return value

        if isinstance(
            value,
            (int, float),
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
                separators=(",", ":"),
            )

        if value is None:
            return None

        return str(
            value
        ).strip() or None

    @staticmethod
    def _signal_type_for(
        field: str,
    ) -> ClinicalSignalType:
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

        if field.startswith(
            "_interview_"
        ):
            return ClinicalSignalType.OTHER

        if field in {
            "onset",
            "duration",
        }:
            return ClinicalSignalType.DURATION

        return ClinicalSignalType.SYMPTOM

    @staticmethod
    def _build_known_fields(
        signals: list[ClinicalSignal],
    ) -> dict[str, Any]:
        return {
            signal.name: signal.value
            for signal in signals
        }

    @staticmethod
    def _load_state(
        signals: list[ClinicalSignal],
    ) -> InterviewState:
        values = {
            signal.name: signal.value
            for signal in signals
        }

        return InterviewState.from_value(
            values.get(
                STATE_SIGNAL_NAME
            ),
            legacy_fields=values,
        )

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
                "content": turn.content or "",
                "language": turn.language,
            }
            for turn in turns
            if turn.speaker
            in {
                Speaker.PATIENT,
                Speaker.SYSTEM,
            }
        ]

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

        history_parts = [
            f"{label}: {value}"
            for label, value in section_values
            if value
        ]

        history = (
            "\n".join(
                history_parts
            )
            if history_parts
            else None
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
            "past_medical_history": (
                past_medical_history
            ),
            "medications": medications,
            "allergies": allergies,
            "clinical_signals": (
                clinical_signal_names
            ),
            "generated_at": datetime.now(
                timezone.utc
            ),
        }

        if existing is None:
            return (
                await self.summary_service.create_summary(
                    ClinicalSummary(
                        summary_id=(
                            f"summary_{uuid4().hex}"
                        ),
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

        text = str(
            value
        ).strip()

        return (
            [text]
            if text
            else []
        )

    @staticmethod
    def _value_as_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        text = str(
            value
        ).strip()

        return text or None

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

    @staticmethod
    def _state_debug_value(
        state: InterviewState,
    ) -> dict[str, Any]:
        return {
            "topic": state.topic,
            "current_section": state.current_section,
            "completed_sections": sorted(
                state.completed_sections
            ),
            "known_fields": state.known_fields(),
            "facts": state.facts[-20:],
            "question_history": (
                state.question_history[-10:]
            ),
        }

    @staticmethod
    def _red_flag_message(
        language: str | None,
    ) -> str:
        if language == "hi":
            return (
                "आपकी जानकारी दर्ज कर ली गई है। "
                "कृपया आगे बढ़ें ताकि स्वास्थ्यकर्मी "
                "इसकी जल्द समीक्षा कर सकें।"
            )

        return (
            "I have recorded what you shared. "
            "Please continue so a healthcare professional "
            "can review it promptly."
        )

    @staticmethod
    def _completion_message(
        language: str | None,
    ) -> str:
        if language == "hi":
            return (
                "धन्यवाद। आपकी मेडिकल हिस्ट्री "
                "दर्ज कर ली गई है।"
            )

        return (
            "Thank you. Your medical history "
            "has been recorded."
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
