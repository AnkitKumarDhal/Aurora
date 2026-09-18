from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from backend.domain.common import utc_now
from backend.domain.enums import SessionStatus, VerificationStatus
from backend.domain.patient import Patient
from backend.integrations.identity import (
    IdentityProvider,
    IdentityVerificationResult,
)
from backend.services.clinical_session import ClinicalSessionService
from backend.services.healthcare_integration import (
    HealthcareIntegrationService,
)
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
        self.healthcare_integration_service = (
            healthcare_integration_service
        )

    async def verify(
        self,
        session_id: str,
        method: str,
        identifier: str,
    ) -> tuple[str, IdentityVerificationResult, Patient | None]:
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
                "Clinical session could not enter identifying state",
            )

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError(
                "Session must be identifying for identification",
            )

        result = await self.identity_provider.verify(
            method,
            identifier,
        )

        if result.status != VerificationStatus.VERIFIED:
            return f"ver_{uuid4().hex}", result, None

        existing_patient = await self._find_existing_patient(
            method,
            identifier,
            result,
        )

        await self.session_service.set_verification_status(
            session_id,
            VerificationStatus.VERIFIED,
        )

        return (
            f"ver_{uuid4().hex}",
            result,
            existing_patient,
        )

    async def persist_identity(
        self,
        session_id: str,
        method: str,
        identifier: str,
    ) -> Patient:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.IDENTIFYING:
            raise ValueError(
                "Session must be identifying before identity is persisted",
            )

        result = await self.identity_provider.verify(
            method,
            identifier,
        )

        if result.status != VerificationStatus.VERIFIED:
            raise ValueError("Patient identity could not be verified")

        existing_patient = await self._find_existing_patient(
            method,
            identifier,
            result,
        )

        timestamp = utc_now()
        normalized_method = method.upper()
        normalized_identifier = self._normalize_identifier(identifier)

        if existing_patient is not None:
            updates = {
                "storage_consent_granted_at": timestamp,
            }

            if normalized_method == "ABHA":
                updates["abha_reference"] = normalized_identifier

            if normalized_method == "AADHAAR":
                updates["aadhaar_reference"] = normalized_identifier

            patient = await self.patient_service.update_patient(
                existing_patient.patient_id,
                updates,
            )

            if patient is None:
                patient = existing_patient
        else:
            if (
                result.patient_id is None
                or result.display_name is None
            ):
                raise ValueError(
                    "Verified identity is missing patient information",
                )

            patient = Patient(
                patient_id=result.patient_id,
                display_name=result.display_name,
                date_of_birth=result.date_of_birth,
                age=result.age,
                abha_reference=(
                    normalized_identifier
                    if normalized_method == "ABHA"
                    else result.abha_reference
                ),
                aadhaar_reference=(
                    normalized_identifier
                    if normalized_method == "AADHAAR"
                    else result.aadhaar_reference
                ),
                hospital_reference=result.hospital_reference,
                storage_consent_granted_at=timestamp,
                created_at=timestamp,
                updated_at=timestamp,
            )

            try:
                await self.patient_service.create_patient(patient)
            except DuplicateKeyError:
                existing_patient = await self._find_existing_patient(
                    method,
                    identifier,
                    result,
                )

                if existing_patient is None:
                    raise

                patient = await self.patient_service.update_patient(
                    existing_patient.patient_id,
                    {
                        "storage_consent_granted_at": timestamp,
                    },
                ) or existing_patient

        await self.healthcare_integration_service.sync_patient(
            patient,
        )

        updated_session = await self.session_service.set_identity(
            session_id,
            patient.patient_id,
            VerificationStatus.VERIFIED,
        )

        if updated_session is None:
            raise ValueError(
                "Clinical session could not be linked to patient",
            )

        return patient

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
            None
            if session.patient_id == "unverified"
            else session.patient_id,
        )

    async def _find_existing_patient(
        self,
        method: str,
        identifier: str,
        result: IdentityVerificationResult,
    ) -> Patient | None:
        patient = await self.patient_service.get_by_identity(
            method,
            identifier,
        )

        if patient is not None:
            return patient

        if result.patient_id is not None:
            return await self.patient_service.get_patient(
                result.patient_id,
            )

        return None

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return "".join(
            character
            for character in identifier
            if character.isdigit()
        )
