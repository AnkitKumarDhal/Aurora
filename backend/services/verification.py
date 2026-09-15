from datetime import datetime, timezone
from uuid import uuid4

from backend.database.repositories.patient import PatientRepository
from backend.domain.enums import SessionStatus, VerificationStatus
from backend.models.patient import PatientDocument
from backend.services.clinical_session import ClinicalSessionService
from backend.integrations.identity import IdentityProvider, IdentityVerificationResult


class VerificationService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        patient_repository: PatientRepository,
        identity_provider: IdentityProvider,
    ) -> None:
        self.session_service = session_service
        self.patient_repository = patient_repository
        self.identity_provider = identity_provider

    async def verify(
        self,
        session_id: str,
        method: str,
        identifier: str,
    ) -> tuple[str, IdentityVerificationResult]:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status == SessionStatus.CREATED:
            session = await self.session_service.transition_session(
                session_id,
                SessionStatus.IDENTIFYING,
            )

        if session is None:
            raise ValueError(
                "Clinical session could not enter identifying state")

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError("Session must be identifying for verification")

        result = await self.identity_provider.verify(method, identifier)

        if result.status != VerificationStatus.VERIFIED:
            return f"ver_{uuid4().hex}", result

        await self._save_patient(result)

        updated_session = await self.session_service.set_identity(
            session_id,
            result.patient_id,
            VerificationStatus.VERIFIED,
        )

        if updated_session is None:
            raise ValueError("Clinical session could not be updated")

        return f"ver_{uuid4().hex}", result

    async def get_status(
        self,
        session_id: str,
    ) -> tuple[str, VerificationStatus, str | None]:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        return (
            f"ver_{session_id}",
            session.verification_status,
            None if session.patient_id == "unverified" else session.patient_id,
        )

    async def _save_patient(
        self,
        result: IdentityVerificationResult,
    ) -> None:
        existing = None

        if result.abha_reference is not None:
            existing = await self.patient_repository.get_by_abha_reference(
                result.abha_reference,
            )

        if existing is not None:
            return

        if result.patient_id is None or result.display_name is None:
            raise ValueError(
                "Verified identity is missing patient information")

        timestamp = datetime.now(timezone.utc)

        await self.patient_repository.create_patient(
            PatientDocument(
                patient_id=result.patient_id,
                display_name=result.display_name,
                date_of_birth=result.date_of_birth,
                age=result.age,
                abha_reference=result.abha_reference,
                hospital_reference=result.hospital_reference,
                created_at=timestamp,
                updated_at=timestamp,
            ),
        )
