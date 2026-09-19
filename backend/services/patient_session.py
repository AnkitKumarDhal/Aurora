import hashlib

from backend.domain.clinical_session import ClinicalSession
from backend.domain.common import utc_now
from backend.domain.enums import (
    ConsentStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.services.clinical_session import ClinicalSessionService
from backend.services.ephemeral_identity import EphemeralIdentityService


class PatientSessionPreparationService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        ephemeral_identity_service: EphemeralIdentityService,
    ) -> None:
        self.session_service = session_service
        self.ephemeral_identity_service = ephemeral_identity_service

    async def prepare(
        self,
        draft_id: str,
        verification_token: str,
        identity_method: str,
        identity_identifier: str,
        consent_version: str,
        department_id: str,
    ) -> ClinicalSession:
        await self.ephemeral_identity_service.get_verified_identity(
            draft_id,
            verification_token,
            identity_method,
            identity_identifier,
        )

        if consent_version != "1.0":
            raise ValueError("Unsupported consent version")

        session_id = self.session_id_for_draft(draft_id)
        session = await self.session_service.get_session(session_id)

        if session is None:
            now = utc_now()

            session = ClinicalSession(
                session_id=session_id,
                patient_id="unverified",
                department_id=department_id,
                status=SessionStatus.IDENTIFYING,
                verification_status=VerificationStatus.VERIFIED,
                consent_status=ConsentStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

            await self.session_service.create_session(session)

        if session.department_id != department_id:
            raise ValueError("Patient session department does not match")

        if session.status in {
            SessionStatus.CANCELLED,
            SessionStatus.ABANDONED,
            SessionStatus.ERROR,
            SessionStatus.COMPLETED,
        }:
            raise ValueError("Patient session is no longer active")

        if session.status == SessionStatus.CREATED:
            session = await self.session_service.transition_session(
                session_id,
                SessionStatus.IDENTIFYING,
            )

            if session is None:
                raise ValueError(
                    "Patient session could not enter identifying state",
                )

        if session.verification_status != VerificationStatus.VERIFIED:
            session = await self.session_service.set_verification_status(
                session_id,
                VerificationStatus.VERIFIED,
            )

            if session is None:
                raise ValueError(
                    "Patient session could not be verified",
                )

        if session.status == SessionStatus.IDENTIFYING:
            if session.consent_status != ConsentStatus.GRANTED:
                session = await self.session_service.set_consent(
                    session_id,
                    ConsentStatus.GRANTED,
                )

                if session is None:
                    raise ValueError(
                        "Patient session consent could not be recorded",
                    )

            session = await self.session_service.transition_session(
                session_id,
                SessionStatus.CONSENTED,
            )

            if session is None:
                raise ValueError(
                    "Patient session could not enter consented state",
                )

        elif session.consent_status != ConsentStatus.GRANTED:
            raise ValueError(
                "Patient session does not have granted consent",
            )

        return session

    async def validate_access(
        self,
        session_id: str,
        draft_id: str,
        verification_token: str,
        identity_method: str,
        identity_identifier: str,
    ) -> ClinicalSession:
        expected_session_id = self.session_id_for_draft(draft_id)

        if session_id != expected_session_id:
            raise ValueError("Patient session does not belong to this draft")

        await self.ephemeral_identity_service.get_verified_identity(
            draft_id,
            verification_token,
            identity_method,
            identity_identifier,
        )

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.verification_status != VerificationStatus.VERIFIED:
            raise ValueError("Patient identity is not verified")

        if session.consent_status != ConsentStatus.GRANTED:
            raise ValueError("Patient consent is required")

        if session.status not in {
            SessionStatus.CONSENTED,
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            raise ValueError("Patient session is not accepting clinical input")

        return session

    @staticmethod
    def session_id_for_draft(draft_id: str) -> str:
        stable_id = hashlib.sha256(
            draft_id.encode(),
        ).hexdigest()[:24]

        return f"sess_{stable_id}"

    @staticmethod
    def turn_id_for_draft(
        draft_id: str,
        local_id: str,
    ) -> str:
        stable_id = hashlib.sha256(
            f"{draft_id}:{local_id}".encode(),
        ).hexdigest()[:24]

        return f"turn_{stable_id}"
