from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.clinical_signal import ClinicalSignalRepository
from backend.database.repositories.conversation import ConversationRepository
from backend.database.repositories.clinical_summary import ClinicalSummaryRepository
from backend.database.repositories.document import DocumentExtractionRepository, DocumentRepository
from backend.database.repositories.patient import PatientRepository
from backend.database.repositories.triage import TriageRepository
from backend.database.repositories.queue import QueueRepository
from backend.integrations.identity import MockIdentityProvider
from backend.integrations.storage import LocalStorage
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.intake import IntakeService
from backend.services.consent import ConsentService
from backend.services.conversation import ConversationService
from backend.services.document import DocumentService
from backend.services.patient import PatientService
from backend.services.verification import VerificationService
from backend.services.triage import TriageService
from backend.services.queue import QueueService


def get_clinical_session_service() -> ClinicalSessionService:
    return ClinicalSessionService(ClinicalSessionRepository())


def get_clinical_summary_service() -> ClinicalSummaryService:
    return ClinicalSummaryService(ClinicalSummaryRepository())


def get_intake_service() -> IntakeService:
    return IntakeService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
        summary_service=ClinicalSummaryService(ClinicalSummaryRepository())
    )


def get_queue_service() -> QueueService:
    return QueueService(QueueRepository())


def get_triage_service() -> TriageService:
    return TriageService(
        repository=TriageRepository(),
        signal_repository=ClinicalSignalRepository(),
    )


def get_patient_service() -> PatientService:
    return PatientService(PatientRepository())


def get_verification_service() -> VerificationService:
    return VerificationService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
        patient_service=PatientService(PatientRepository()),
        identity_provider=MockIdentityProvider(),
    )


def get_consent_service() -> ConsentService:
    return ConsentService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
    )


def get_conversation_service() -> ConversationService:
    return ConversationService(
        repository=ConversationRepository(),
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
    )


def get_storage() -> LocalStorage:
    return LocalStorage()


def get_document_service() -> DocumentService:
    return DocumentService(
        document_repository=DocumentRepository(),
        extraction_repository=DocumentExtractionRepository(),
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
    )
