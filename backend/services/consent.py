from backend.domain.enums import (
    ConsentStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.services.clinical_session import ClinicalSessionService
from backend.services.verification import VerificationService


class ConsentService:
    CONSENT_VERSION = "1.0"
    CONSENT_TEXT = "Consent text approved for the current deployment."
    SUPPORTED_LANGUAGES = ["en", "hi", "od"]

    def __init__(
        self,
        session_service: ClinicalSessionService,
        verification_service: VerificationService,
    ) -> None:
        self.session_service = session_service
        self.verification_service = verification_service

    async def grant(
        self,
        session_id: str,
        version: str,
        method: str,
        identifier: str,
    ) -> SessionStatus:
        self._validate_version(version)

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if (
            session.status == SessionStatus.CONSENTED
            and session.consent_status == ConsentStatus.GRANTED
        ):
            return session.status

        if session.verification_status != VerificationStatus.VERIFIED:
            raise ValueError(
                "Patient identity must be verified before consent",
            )

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError(
                "Session must be identifying before consent",
            )

        await self.verification_service.persist_identity(
            session_id,
            method,
            identifier,
        )

        updated_session = await self.session_service.set_consent(
            session_id,
            ConsentStatus.GRANTED,
        )

        if updated_session is None:
            raise ValueError(
                "Clinical session could not be updated",
            )

        updated_session = await self.session_service.transition_session(
            session_id,
            SessionStatus.CONSENTED,
        )

        if updated_session is None:
            raise ValueError(
                "Clinical session could not enter consented state",
            )

        return updated_session.status

    async def deny(
        self,
        session_id: str,
        version: str,
    ) -> SessionStatus:
        self._validate_version(version)

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.verification_status != VerificationStatus.VERIFIED:
            raise ValueError(
                "Patient identity must be verified before consent",
            )

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError(
                "Session must be identifying before consent",
            )

        updated_session = await self.session_service.set_consent(
            session_id,
            ConsentStatus.DENIED,
        )

        if updated_session is None:
            raise ValueError(
                "Clinical session could not be updated",
            )

        return updated_session.status

    async def get_status(
        self,
        session_id: str,
    ) -> ConsentStatus:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        return session.consent_status

    @staticmethod
    def get_information() -> dict:
        return {
            "version": ConsentService.CONSENT_VERSION,
            "text": ConsentService.CONSENT_TEXT,
            "audio_available": True,
            "supported_languages": ConsentService.SUPPORTED_LANGUAGES,
        }

    def _validate_version(self, version: str) -> None:
        if version != self.CONSENT_VERSION:
            raise ValueError(
                f"Unsupported consent version: {version}",
            )
