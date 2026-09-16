from backend.auth.service import AuthenticationService
from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.clinical_signal import ClinicalSignalRepository
from backend.database.repositories.conversation import ConversationRepository
from backend.database.repositories.clinical_summary import ClinicalSummaryRepository
from backend.database.repositories.document import DocumentExtractionRepository, DocumentRepository
from backend.database.repositories.patient import PatientRepository
from backend.database.repositories.triage import TriageRepository
from backend.database.repositories.queue import QueueRepository
from backend.database.repositories.promotion import PromotionRepository
from backend.database.repositories.user import UserRepository
from backend.integrations.abdm import MockAbdmClient
from backend.integrations.fhir import MockFhirClient
from backend.integrations.his import MockHisClient
from backend.integrations.identity import MockIdentityProvider
from backend.integrations.storage import LocalStorage
from backend.services.assignment import AssignmentService
from backend.services.assignment_scheduler import AssignmentSchedulerService
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.healthcare_integration import HealthcareIntegrationService
from backend.services.intake import IntakeService
from backend.services.consent import ConsentService
from backend.services.conversation import ConversationService
from backend.services.document import DocumentService
from backend.services.patient import PatientService
from backend.services.verification import VerificationService
from backend.services.triage import TriageService
from backend.services.queue import QueueService
from backend.services.workflow import WorkflowService
from backend.services.promotion import PromotionService


def get_authentication_service() -> AuthenticationService:
    return AuthenticationService(UserRepository())


def get_promotion_service() -> PromotionService:
    return PromotionService(PromotionRepository())


def get_doctor_repository() -> DoctorRepository:
    return DoctorRepository()


def get_assignment_repository() -> AssignmentRepository:
    return AssignmentRepository()


def get_clinical_session_service() -> ClinicalSessionService:
    return ClinicalSessionService(ClinicalSessionRepository())


def get_clinical_summary_service() -> ClinicalSummaryService:
    return ClinicalSummaryService(ClinicalSummaryRepository())


def get_intake_service() -> IntakeService:
    return IntakeService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
        summary_service=ClinicalSummaryService(ClinicalSummaryRepository()),
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=ClinicalSignalRepository(),
        ),
    )


def get_queue_service() -> QueueService:
    return QueueService(QueueRepository())


def get_triage_service() -> TriageService:
    return TriageService(
        repository=TriageRepository(),
        signal_repository=ClinicalSignalRepository(),
    )


def get_workflow_service() -> WorkflowService:
    assignment_repository = AssignmentRepository()
    assignment_service = AssignmentService(assignment_repository)

    return WorkflowService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
        queue_service=QueueService(QueueRepository()),
        assignment_scheduler=AssignmentSchedulerService(
            doctor_repository=DoctorRepository(),
            assignment_repository=assignment_repository,
            assignment_service=assignment_service,
        ),
        assignment_service=assignment_service,
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=ClinicalSignalRepository(),
        ),
    )


def get_patient_service() -> PatientService:
    return PatientService(PatientRepository())


def get_healthcare_integration_service() -> HealthcareIntegrationService:
    return HealthcareIntegrationService(
        abdm_client=MockAbdmClient(),
        fhir_client=MockFhirClient(),
        his_client=MockHisClient(),
    )


def get_verification_service() -> VerificationService:
    return VerificationService(
        session_service=ClinicalSessionService(ClinicalSessionRepository()),
        patient_service=PatientService(PatientRepository()),
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=get_healthcare_integration_service(),
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
