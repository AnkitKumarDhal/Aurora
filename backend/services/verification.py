from uuid import uuid4
from backend.domain.common import utc_now
from backend.domain.enums import SessionStatus, VerificationStatus
from backend.domain.patient import Patient
from backend.integrations.identity import IdentityProvider, IdentityVerificationResult
from backend.services.clinical_session import ClinicalSessionService
from backend.services.healthcare_integration import HealthcareIntegrationService
from backend.services.patient import PatientService


class VerificationService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        patient_service: PatientService,
        identity_provider: IdentityProvider,
        healthcare_integration_service: HealthcareIntegrationService,
    ) -> None:
        self.session_service = session_service
        self.patient_service = patient_service
        self.identity_provider = identity_provider
        self.healthcare_integration_service = healthcare_integration_service

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
            existing = await self.patient_service.get_by_abha_reference(
                result.abha_reference,
            )

        if existing is not None:
            await self.healthcare_integration_service.sync_patient(existing)
            return

        if result.patient_id is None or result.display_name is None:
            raise ValueError(
                "Verified identity is missing patient information")

        timestamp = utc_now()

        patient = Patient(
            patient_id=result.patient_id,
            display_name=result.display_name,
            date_of_birth=result.date_of_birth,
            age=result.age,
            abha_reference=result.abha_reference,
            hospital_reference=result.hospital_reference,
            created_at=timestamp,
            updated_at=timestamp,
        )

        await self.patient_service.create_patient(patient)
        await self.healthcare_integration_service.sync_patient(patient)
