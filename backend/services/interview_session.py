from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus
from backend.domain.common import utc_now
from backend.services.clinical_session import ClinicalSessionService
from backend.services.ephemeral_identity import EphemeralIdentityService


class InterviewSessionPreparationService:
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
        department_id: str,
    ) -> ClinicalSession:
        await self.ephemeral_identity_service.get_verified_identity(
            draft_id=draft_id,
            token=verification_token,
            method=identity_method,
            identifier=identity_identifier,
        )

        session_id = self._session_id(draft_id)
        existing = await self.session_service.get_session(session_id)

        if existing is not None:
            if existing.status in {
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
                SessionStatus.COMPLETED,
            }:
                raise ValueError("Interview session is no longer active")

            return existing

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

        try:
            return await self.session_service.create_session(session)
        except DuplicateKeyError:
            existing = await self.session_service.get_session(session_id)

            if existing is None:
                raise

            return existing

    @staticmethod
    def _session_id(draft_id: str) -> str:
        return f"sess_{sha256(draft_id.encode()).hexdigest()[:24]}"
