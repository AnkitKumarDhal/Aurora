from backend.domain.enums import SessionStatus
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService


class IntakeService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        summary_service: ClinicalSummaryService,
    ) -> None:
        self.session_service = session_service
        self.summary_service = summary_service

    async def finalize(self, session_id: str):
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        summary = await self.summary_service.get_session_summary(session_id)

        if summary is None:
            raise ValueError("Clinical summary not found")

        if session.status not in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError("Session is not ready for intake finalization")

        return await self.session_service.transition_session(
            session_id,
            SessionStatus.SUMMARY_READY,
        )
