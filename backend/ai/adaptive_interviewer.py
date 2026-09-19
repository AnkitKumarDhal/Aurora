from __future__ import annotations

import json
from typing import Any, Iterable

from .aurora_integration import AuroraClinicalAdapter
from .clinical_service import ClinicalSession
from .question_planner import QuestionPlanner


def process_response_for_field(
    session: ClinicalSession,
    response: str,
    target_field: str,
) -> dict[str, Any]:
    original_queue = list(
        session.question_queue,
    )

    target_question = None

    for question in original_queue:
        if question.get("field") == target_field:
            target_question = dict(question)
            break

    if target_question is None:
        raise ValueError(
            "Selected interview field is not part of the clinical schema",
        )

    session.question_queue = [
        target_question,
        *[
            dict(question)
            for question in original_queue
            if question.get("field") != target_field
        ],
    ]
    session.question_index = 0
    session.completed = False

    try:
        result = session.process_response(
            response,
        )
    finally:
        session.question_queue = original_queue
        session.question_index = _first_missing_index(
            session,
            original_queue,
        )

    return result


def _first_missing_index(
    session: ClinicalSession,
    queue: list[dict[str, str]],
) -> int:
    for index, question in enumerate(queue):
        field = question.get("field")

        if (
            field
            and not session._field_has_value(field)
        ):
            return index

    return len(queue)


class AdaptiveAuroraClinicalAdapter:
    def __init__(
        self,
        base_adapter: AuroraClinicalAdapter,
        planner: QuestionPlanner | None = None,
    ) -> None:
        self.base_adapter = base_adapter
        self.planner = planner or QuestionPlanner()

    def process_turn(
        self,
        session_id: str,
        patient_text: str,
        previous_patient_turns: Iterable[Any] | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        previous_turns = list(
            previous_patient_turns or [],
        )

        if not str(session_id).strip():
            raise ValueError("session_id is required")

        if not str(patient_text).strip():
            raise ValueError("patient_text is required")

        pending_question_field = (
            self._pending_question_field(
                previous_turns,
            )
        )

        session = self.base_adapter._rebuild_session(
            previous_turns,
        )

        if pending_question_field:
            result = process_response_for_field(
                session=session,
                response=str(patient_text),
                target_field=pending_question_field,
            )
        else:
            result = session.process_response(
                str(patient_text),
            )

        decision = self.planner.plan(
            session=session,
            language=language or "en",
            previous_turns=[
                self._normalise_turn(turn)
                for turn in previous_turns
            ],
            interview_mode="GENERAL",
        )

        if decision is not None:
            if decision.action == "COMPLETE":
                session.completed = True
                next_question = None
                question_field = None
                question_source = "llm"
                question_reason = decision.reason
                answer_mode = None
            else:
                next_question = decision.question
                question_field = decision.next_field
                question_source = "llm"
                question_reason = decision.reason
                answer_mode = decision.answer_mode
        else:
            fallback = self.planner.deterministic_fallback(
                session=session,
                interview_mode="GENERAL",
            )

            if fallback is None:
                session.completed = True
                next_question = None
                question_field = None
                question_source = "deterministic"
                question_reason = (
                    "No remaining approved clinical objectives."
                )
                answer_mode = None
            else:
                question_field, next_question = fallback
                question_source = "deterministic"
                question_reason = (
                    "The adaptive interviewer was unavailable or "
                    "returned an invalid decision."
                )
                answer_mode = self.planner._answer_mode(
                    question_field,
                )

        signals = self.base_adapter._build_signal_records(
            session_id=session_id,
            session=session,
        )

        return {
            "session_id": session_id,
            "language": language,
            "input_type": "TEXT",
            "patient_text": str(patient_text),
            "assistant_response": next_question,
            "next_question": next_question,
            "field": result.get("field"),
            "question_field": question_field,
            "question_source": question_source,
            "question_reason": question_reason,
            "answer_mode": answer_mode,
            "completed": bool(session.completed),
            "history": session.patient_history,
            "red_flags": list(session.red_flags),
            "triage_required": bool(
                session.triage_required,
            ),
            "physician_review_required": bool(
                session.review_required,
            ),
            "contradictions": list(
                session.contradictions,
            ),
            "clinical_evidence": (
                session.evidence_store.to_dict()
            ),
            "signals": signals,
        }

    def extract_signals(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.base_adapter.extract_signals(
            *args,
            **kwargs,
        )

    def generate_summary(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.base_adapter.generate_summary(
            *args,
            **kwargs,
        )

    def finalize_clinical_session(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.base_adapter.finalize_clinical_session(
            *args,
            **kwargs,
        )

    @staticmethod
    def _normalise_turn(
        turn: Any,
    ) -> dict[str, Any]:
        if isinstance(turn, dict):
            return turn

        speaker = getattr(
            turn,
            "speaker",
            None,
        )

        return {
            "turn_id": getattr(
                turn,
                "turn_id",
                None,
            ),
            "speaker": getattr(
                speaker,
                "value",
                speaker,
            ),
            "content": getattr(
                turn,
                "content",
                None,
            ),
            "language": getattr(
                turn,
                "language",
                None,
            ),
            "media_reference": getattr(
                turn,
                "media_reference",
                None,
            ),
            "created_at": getattr(
                turn,
                "created_at",
                None,
            ),
        }

    @staticmethod
    def _pending_question_field(
        turns: Iterable[Any],
    ) -> str | None:
        for turn in reversed(
            list(turns),
        ):
            normalised = (
                AdaptiveAuroraClinicalAdapter._normalise_turn(
                    turn,
                )
            )

            speaker = str(
                normalised.get(
                    "speaker",
                    "",
                ),
            ).strip().lower()

            if speaker != "system":
                continue

            media_reference = normalised.get(
                "media_reference",
            )

            if not media_reference:
                continue

            try:
                metadata = json.loads(
                    media_reference,
                )
            except (
                TypeError,
                json.JSONDecodeError,
            ):
                continue

            field = metadata.get(
                "question_field",
            )

            if field:
                return str(field)

        return None
