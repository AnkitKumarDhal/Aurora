import json
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from backend.ai.adaptive_interviewer import (
    AdaptiveAuroraClinicalAdapter,
)
from backend.ai.aurora_integration import AuroraClinicalAdapter
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import (
    ClinicalSignalType,
    SessionStatus,
    Speaker,
    SummaryStatus,
)
from backend.domain.triage import TriageResult
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_signal import ClinicalSignalService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.conversation import ConversationService
from backend.services.document import DocumentService
from backend.services.triage import TriageService


class ClinicalIntelligenceService:
    def __init__(
        self,
        adapter: AuroraClinicalAdapter,
        conversation_service: ConversationService,
        signal_service: ClinicalSignalService,
        summary_service: ClinicalSummaryService,
        triage_service: TriageService,
        document_service: DocumentService,
        session_service: ClinicalSessionService,
    ) -> None:
        self.adapter = AdaptiveAuroraClinicalAdapter(
            base_adapter=adapter,
        )
        self.conversation_service = conversation_service
        self.signal_service = signal_service
        self.summary_service = summary_service
        self.triage_service = triage_service
        self.document_service = document_service
        self.session_service = session_service

    async def process_turn(
        self,
        turn: ConversationTurn,
    ) -> dict:
        if not turn.content or not turn.content.strip():
            raise ValueError("Conversation content is required")

        existing_turn = await self.conversation_service.get_turn(
            turn.turn_id,
        )

        if existing_turn is None:
            stored_turn = await self.conversation_service.submit_turn(
                turn,
            )
        else:
            if existing_turn.content != turn.content:
                raise ValueError(
                    "Conversation turn already exists with different content",
                )

            stored_turn = existing_turn

        persisted_turns = (
            await self.conversation_service.get_session_turns(
                turn.session_id,
            )
        )

        previous_turns = [
            self._turn_to_payload(item)
            for item in persisted_turns
            if item.turn_id != stored_turn.turn_id
        ]

        result = self.adapter.process_turn(
            session_id=turn.session_id,
            patient_text=stored_turn.content or "",
            previous_patient_turns=previous_turns,
            language=stored_turn.language,
        )

        await self._persist_signals(
            turn.session_id,
            result.get("signals", []),
        )

        assistant_response = result.get(
            "assistant_response",
        )

        if assistant_response:
            system_turn_id = (
                "ai_"
                + sha256(
                    (
                        f"{stored_turn.turn_id}:"
                        f"{result.get('question_field')}:"
                        f"{assistant_response}"
                    ).encode(),
                ).hexdigest()[:24]
            )

            existing_system_turn = (
                await self.conversation_service.get_turn(
                    system_turn_id,
                )
            )

            if existing_system_turn is None:
                system_turn = ConversationTurn(
                    turn_id=system_turn_id,
                    session_id=stored_turn.session_id,
                    speaker=Speaker.SYSTEM,
                    input_type=turn.input_type,
                    content=str(assistant_response),
                    language=turn.language,
                    media_reference=json.dumps(
                        {
                            "question_field": result.get(
                                "question_field",
                            ),
                            "question_source": result.get(
                                "question_source",
                            ),
                            "question_reason": result.get(
                                "question_reason",
                            ),
                            "answer_mode": result.get(
                                "answer_mode",
                            ),
                        },
                        ensure_ascii=False,
                    ),
                )

                await self.conversation_service.add_turn(
                    system_turn,
                )

        return {
            "turn": stored_turn,
            "assistant_response": assistant_response,
            "next_question": result.get(
                "next_question",
            ),
            "completed": bool(
                result.get(
                    "completed",
                    False,
                )
            ),
            "question_field": result.get(
                "question_field",
            ),
            "question_source": result.get(
                "question_source",
            ),
            "question_reason": result.get(
                "question_reason",
            ),
            "answer_mode": result.get(
                "answer_mode",
            ),
        }

    async def finalize_clinical_session(
        self,
        session_id: str,
    ) -> dict:
        session = await self.session_service.get_session(
            session_id,
        )

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status == SessionStatus.SUMMARY_READY:
            summary = await self.summary_service.get_session_summary(
                session_id,
            )

            triage = await self.triage_service.get_session_result(
                session_id,
            )

            if summary is None:
                raise ValueError(
                    "Clinical summary not found",
                )

            return {
                "session": session,
                "summary": summary,
                "triage": triage,
                "clinical_result": None,
            }

        if session.status not in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError(
                "Clinical session is not ready for clinical finalization",
            )

        persisted_turns = (
            await self.conversation_service.get_session_turns(
                session_id,
            )
        )

        conversation_turns = [
            self._turn_to_payload(turn)
            for turn in persisted_turns
        ]

        document_summaries = (
            await self._build_document_summaries(
                session_id,
            )
        )

        clinical_result = (
            self.adapter.finalize_clinical_session(
                session_id=session_id,
                patient_turns=conversation_turns,
                document_summaries=document_summaries,
                generate_ai_draft=False,
            )
        )

        await self._persist_signals(
            session_id,
            clinical_result.get(
                "signals",
                [],
            ),
        )

        summary = await self._upsert_summary(
            session_id,
            clinical_result["aurora_summary"],
        )

        triage = await self.triage_service.get_session_result(
            session_id,
        )

        if triage is None:
            triage = TriageResult(
                triage_id=f"triage_{uuid4().hex}",
                session_id=session_id,
            )

            triage = await self.triage_service.create_result(
                triage,
            )

        signals = await self.signal_service.get_session_signals(
            session_id,
        )

        assessed_triage = await self.triage_service.assess_from_signals(
            triage.triage_id,
            signals,
        )

        if assessed_triage is None:
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
            "triage": assessed_triage,
            "clinical_result": clinical_result,
        }

    async def _persist_signals(
        self,
        session_id: str,
        signals: list[dict],
    ) -> None:
        existing_signals = (
            await self.signal_service.get_session_signals(
                session_id,
            )
        )

        existing_ids = {
            signal.signal_id
            for signal in existing_signals
        }

        for signal_data in signals:
            if not isinstance(signal_data, dict):
                continue

            signal_id = str(
                signal_data.get(
                    "signal_id",
                    "",
                )
            ).strip()

            if not signal_id or signal_id in existing_ids:
                continue

            try:
                signal_type = ClinicalSignalType(
                    str(
                        signal_data.get(
                            "signal_type",
                            "OTHER",
                        )
                    ),
                )
            except ValueError:
                signal_type = ClinicalSignalType.OTHER

            signal = ClinicalSignal(
                signal_id=signal_id,
                session_id=session_id,
                signal_type=signal_type,
                name=str(
                    signal_data.get(
                        "name",
                        "",
                    )
                ),
                value=signal_data.get(
                    "value",
                ),
                confidence=signal_data.get(
                    "confidence",
                ),
                source=signal_data.get(
                    "source",
                ),
            )

            await self.signal_service.create_signal(
                signal,
            )

            existing_ids.add(signal_id)

    async def _upsert_summary(
        self,
        session_id: str,
        summary_data: dict,
    ) -> ClinicalSummary:
        existing = (
            await self.summary_service.get_session_summary(
                session_id,
            )
        )

        values = {
            "status": SummaryStatus.READY,
            "chief_complaint": summary_data.get(
                "chief_complaint",
            ),
            "history_of_present_illness": summary_data.get(
                "history_of_present_illness",
            ),
            "past_medical_history": summary_data.get(
                "past_medical_history",
                [],
            ),
            "medications": summary_data.get(
                "medications",
                [],
            ),
            "allergies": summary_data.get(
                "allergies",
                [],
            ),
            "relevant_documents": summary_data.get(
                "relevant_documents",
                [],
            ),
            "clinical_signals": summary_data.get(
                "clinical_signals",
                [],
            ),
            "generated_at": self._parse_datetime(
                summary_data.get(
                    "generated_at",
                ),
            ),
        }

        if existing is None:
            summary = ClinicalSummary(
                summary_id=f"summary_{uuid4().hex}",
                session_id=session_id,
                **values,
            )

            return await self.summary_service.create_summary(
                summary,
            )

        updated = await self.summary_service.update_summary(
            existing.summary_id,
            values,
        )

        if updated is None:
            raise ValueError(
                "Clinical summary could not be updated",
            )

        return updated

    async def _build_document_summaries(
        self,
        session_id: str,
    ) -> list[dict]:
        documents = (
            await self.document_service.get_session_documents(
                session_id,
            )
        )

        result = []

        for document in documents:
            payload = {
                "document_id": document.document_id,
                "filename": document.filename,
                "document_type": document.document_type.value,
                "status": document.status.value,
            }

            extraction = await self.document_service.get_extraction(
                document.document_id,
            )

            if extraction is not None:
                if extraction.extracted_text:
                    payload["extracted_text"] = (
                        extraction.extracted_text
                    )

                if extraction.structured_data is not None:
                    payload["structured_data"] = (
                        extraction.structured_data
                    )

            result.append(payload)

        return result

    @staticmethod
    def _turn_to_payload(
        turn: ConversationTurn,
    ) -> dict:
        return {
            "turn_id": turn.turn_id,
            "speaker": turn.speaker.value.lower(),
            "content": turn.content,
            "language": turn.language,
            "media_reference": turn.media_reference,
            "created_at": turn.created_at,
        }

    @staticmethod
    def _parse_datetime(
        value,
    ) -> datetime:
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    ),
                )
            except ValueError:
                pass

        return datetime.now(timezone.utc)
