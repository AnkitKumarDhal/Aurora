from uuid import uuid4
from backend.domain.enums import SessionStatus
from backend.domain.triage import TriageResult
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.triage import TriageService


class IntakeService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        summary_service: ClinicalSummaryService,
        triage_service: TriageService,
    ) -> None:
        self.session_service = session_service
        self.summary_service = summary_service
        self.triage_service = triage_service

    async def finalize(self, session_id: str):
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status not in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError("Session is not ready for intake finalization")

        summary = await self.summary_service.get_session_summary(session_id)

        if summary is None:
            raise ValueError("Clinical summary not found")

        existing_triage = await self.triage_service.get_session_result(session_id)

        if existing_triage is None:
            triage = TriageResult(
                triage_id=f"triage_{uuid4().hex}",
                session_id=session_id,
            )
            await self.triage_service.create_result(triage)

        return await self.session_service.transition_session(
            session_id,
            SessionStatus.SUMMARY_READY,
        )
