from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.patient import PatientRepository
from backend.integrations.identity import MockIdentityProvider
from backend.services.clinical_session import ClinicalSessionService
from backend.services.consent import ConsentService
from backend.services.verification import VerificationService


def get_clinical_session_service() -> ClinicalSessionService:
    return ClinicalSessionService(ClinicalSessionRepository())


def get_verification_service() -> VerificationService:
    return VerificationService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        patient_repository=PatientRepository(),
        identity_provider=MockIdentityProvider(),
    )


def get_consent_service() -> ConsentService:
    return ConsentService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
    )
