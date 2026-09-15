from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus
from backend.services.clinical_session import ClinicalSessionService


class ConsentService:
    def __init__(self, session_service: ClinicalSessionService) -> None:
        self.session_service = session_service

    async def grant(self, session_id: str) -> SessionStatus:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.verification_status != VerificationStatus.VERIFIED:
            raise ValueError(
                "Patient identity must be verified before consent")

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError("Session must be identifying before consent")

        updated_session = await self.session_service.set_consent(
            session_id,
            ConsentStatus.GRANTED,
        )

        if updated_session is None:
            raise ValueError("Clinical session could not be updated")

        updated_session = await self.session_service.transition_session(
            session_id,
            SessionStatus.CONSENTED,
        )

        if updated_session is None:
            raise ValueError(
                "Clinical session could not enter consented state")

        return updated_session.status

    async def deny(self, session_id: str) -> SessionStatus:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.verification_status != VerificationStatus.VERIFIED:
            raise ValueError(
                "Patient identity must be verified before consent")

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError("Session must be identifying before consent")

        updated_session = await self.session_service.set_consent(
            session_id,
            ConsentStatus.DENIED,
        )

        if updated_session is None:
            raise ValueError("Clinical session could not be updated")

        return updated_session.status

    async def get_status(self, session_id: str) -> ConsentStatus:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        return session.consent_status
