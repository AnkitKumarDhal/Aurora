from functools import lru_cache

from backend.ai.interview.controller import (
    InterviewController,
)
from backend.ai.interview.extractor import (
    InterviewExtractor,
)
from backend.auth.service import (
    AuthenticationService,
)
from backend.config import settings
from backend.database.repositories.assignment import (
    AssignmentRepository,
)
from backend.database.repositories.clinical_session import (
    ClinicalSessionRepository,
)
from backend.database.repositories.clinical_signal import (
    ClinicalSignalRepository,
)
from backend.database.repositories.clinical_summary import (
    ClinicalSummaryRepository,
)
from backend.database.repositories.conversation import (
    ConversationRepository,
)
from backend.database.repositories.doctor import (
    DoctorRepository,
)
from backend.database.repositories.document import (
    DocumentExtractionRepository,
    DocumentRepository,
)
from backend.database.repositories.patient import (
    PatientRepository,
)
from backend.database.repositories.promotion import (
    PromotionRepository,
)
from backend.database.repositories.queue import (
    QueueRepository,
)
from backend.database.repositories.triage import (
    TriageRepository,
)
from backend.database.repositories.user import (
    UserRepository,
)
from backend.integrations.abdm import (
    MockAbdmClient,
)
from backend.integrations.fhir import (
    MockFhirClient,
)
from backend.integrations.his import (
    MockHisClient,
)
from backend.integrations.identity import (
    MockIdentityProvider,
)
from backend.integrations.storage import (
    LocalStorage,
)
from backend.services.admin_dashboard import (
    AdminDashboardService,
)
from backend.services.assignment import (
    AssignmentService,
)
from backend.services.assignment_scheduler import (
    AssignmentSchedulerService,
)
from backend.services.clinical_intelligence import (
    ClinicalIntelligenceService,
)
from backend.services.clinical_session import (
    ClinicalSessionService,
)
from backend.services.clinical_signal import (
    ClinicalSignalService,
)
from backend.services.clinical_summary import (
    ClinicalSummaryService,
)
from backend.services.consent import (
    ConsentService,
)
from backend.services.conversation import (
    ConversationService,
)
from backend.services.doctor_case import (
    DoctorCaseService,
)
from backend.services.doctor_queue import (
    DoctorQueueService,
)
from backend.services.document import (
    DocumentService,
)
from backend.services.document_processing import (
    DocumentProcessingService,
)
from backend.services.ephemeral_identity import (
    EphemeralIdentityService,
)
from backend.services.healthcare_integration import (
    HealthcareIntegrationService,
)
from backend.services.intake import (
    IntakeService,
)
from backend.services.interview_session import (
    InterviewSessionPreparationService,
)
from backend.services.patient import (
    PatientService,
)
from backend.services.patient_registration import (
    PatientRegistrationService,
)
from backend.services.patient_intake_completion import (
    PatientIntakeCompletionService,
)
from backend.services.promotion import (
    PromotionService,
)
from backend.services.promotion_workflow import (
    PromotionWorkflowService,
)
from backend.services.queue import (
    QueueService,
)
from backend.services.reassignment import (
    ReassignmentService,
)
from backend.services.triage import (
    TriageService,
)
from backend.services.verification import (
    VerificationService,
)
from backend.services.workflow import (
    WorkflowService,
)


def get_authentication_service() -> AuthenticationService:
    return AuthenticationService(
        UserRepository(),
    )


def get_promotion_service() -> PromotionService:
    return PromotionService(
        PromotionRepository(),
    )


@lru_cache(maxsize=1)
def get_promotion_workflow_service() -> PromotionWorkflowService:
    return PromotionWorkflowService(
        promotion_service=get_promotion_service(),
        queue_service=QueueService(
            QueueRepository(),
        ),
        reassignment_service=ReassignmentService(
            queue_repository=QueueRepository(),
            assignment_repository=(
                AssignmentRepository()
            ),
            doctor_repository=(
                DoctorRepository()
            ),
        ),
        doctor_repository=DoctorRepository(),
        assignment_repository=(
            AssignmentRepository()
        ),
    )


def get_doctor_repository() -> DoctorRepository:
    return DoctorRepository()


def get_assignment_repository() -> AssignmentRepository:
    return AssignmentRepository()


def get_clinical_session_service() -> ClinicalSessionService:
    return ClinicalSessionService(
        ClinicalSessionRepository(),
    )


def get_clinical_signal_service() -> ClinicalSignalService:
    return ClinicalSignalService(
        ClinicalSignalRepository(),
    )


def get_clinical_summary_service() -> ClinicalSummaryService:
    return ClinicalSummaryService(
        ClinicalSummaryRepository(),
    )


def get_intake_service() -> IntakeService:
    return IntakeService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        summary_service=ClinicalSummaryService(
            ClinicalSummaryRepository(),
        ),
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=(
                ClinicalSignalRepository()
            ),
        ),
    )


def get_queue_service() -> QueueService:
    return QueueService(
        QueueRepository(),
    )


def get_triage_service() -> TriageService:
    return TriageService(
        repository=TriageRepository(),
        signal_repository=(
            ClinicalSignalRepository()
        ),
    )


def get_healthcare_integration_service() -> HealthcareIntegrationService:
    return HealthcareIntegrationService(
        abdm_client=MockAbdmClient(),
        fhir_client=MockFhirClient(),
        his_client=MockHisClient(),
    )


def get_workflow_service() -> WorkflowService:
    assignment_repository = (
        AssignmentRepository()
    )

    assignment_service = AssignmentService(
        assignment_repository,
    )

    return WorkflowService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        queue_service=QueueService(
            QueueRepository(),
        ),
        assignment_scheduler=(
            AssignmentSchedulerService(
                doctor_repository=(
                    DoctorRepository()
                ),
                assignment_repository=(
                    assignment_repository
                ),
                assignment_service=(
                    assignment_service
                ),
            )
        ),
        assignment_service=assignment_service,
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=(
                ClinicalSignalRepository()
            ),
        ),
        healthcare_integration_service=(
            get_healthcare_integration_service()
        ),
        promotion_workflow=(
            get_promotion_workflow_service()
        ),
    )


def get_reassignment_service() -> ReassignmentService:
    return ReassignmentService(
        queue_repository=QueueRepository(),
        assignment_repository=(
            AssignmentRepository()
        ),
        doctor_repository=DoctorRepository(),
    )


def get_patient_service() -> PatientService:
    return PatientService(
        PatientRepository(),
    )


def get_interview_session_service() -> InterviewSessionPreparationService:
    return InterviewSessionPreparationService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        ephemeral_identity_service=(
            get_ephemeral_identity_service()
        ),
    )


def get_verification_service() -> VerificationService:
    return VerificationService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        patient_service=PatientService(
            PatientRepository(),
        ),
        identity_provider=MockIdentityProvider(
            demo_mode=settings.identity_demo_mode,
        ),
        healthcare_integration_service=(
            get_healthcare_integration_service()
        ),
    )


@lru_cache(maxsize=1)
def get_ephemeral_identity_service() -> EphemeralIdentityService:
    return EphemeralIdentityService(
        identity_provider=MockIdentityProvider(
            demo_mode=settings.identity_demo_mode,
        ),
    )


def get_document_processing_service() -> DocumentProcessingService:
    return DocumentProcessingService(
        document_repository=DocumentRepository(),
        extraction_repository=(
            DocumentExtractionRepository()
        ),
    )


def get_document_service() -> DocumentService:
    return DocumentService(
        document_repository=DocumentRepository(),
        extraction_repository=(
            DocumentExtractionRepository()
        ),
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        processing_service=(
            get_document_processing_service()
        ),
    )


def get_conversation_service() -> ConversationService:
    return ConversationService(
        repository=ConversationRepository(),
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
    )


def get_patient_registration_service() -> PatientRegistrationService:
    return PatientRegistrationService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        patient_service=PatientService(
            PatientRepository(),
        ),
        verification_service=(
            get_verification_service()
        ),
        conversation_service=(
            get_conversation_service()
        ),
        document_service=(
            get_document_service()
        ),
        storage=get_storage(),
        ephemeral_identity_service=(
            get_ephemeral_identity_service()
        ),
    )


def get_doctor_queue_service() -> DoctorQueueService:
    return DoctorQueueService(
        doctor_repository=DoctorRepository(),
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        queue_service=QueueService(
            QueueRepository(),
        ),
        patient_service=PatientService(
            PatientRepository(),
        ),
        summary_service=ClinicalSummaryService(
            ClinicalSummaryRepository(),
        ),
    )


def get_consent_service() -> ConsentService:
    verification_service = (
        get_verification_service()
    )

    return ConsentService(
        session_service=(
            verification_service.session_service
        ),
        verification_service=(
            verification_service
        ),
    )


def get_storage() -> LocalStorage:
    return LocalStorage()


def get_doctor_case_service() -> DoctorCaseService:
    assignment_repository = (
        AssignmentRepository()
    )

    return DoctorCaseService(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository(),
        ),
        patient_service=PatientService(
            PatientRepository()
        ),
        summary_service=ClinicalSummaryService(
            ClinicalSummaryRepository()
        ),
        document_service=(
            get_document_service()
        ),
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=(
                ClinicalSignalRepository()
            ),
        ),
        assignment_service=AssignmentService(
            assignment_repository,
        ),
    )


def get_interview_controller() -> InterviewController:
    return InterviewController(
        session_service=ClinicalSessionService(
            ClinicalSessionRepository()
        ),
        conversation_service=(
            get_conversation_service()
        ),
        signal_service=ClinicalSignalService(
            ClinicalSignalRepository()
        ),
        summary_service=ClinicalSummaryService(
            ClinicalSummaryRepository()
        ),
        triage_service=TriageService(
            repository=TriageRepository(),
            signal_repository=(
                ClinicalSignalRepository()
            ),
        ),
        extractor=InterviewExtractor(),
    )


def get_clinical_intelligence_service() -> ClinicalIntelligenceService:
    return ClinicalIntelligenceService(
        session_service=(
            get_clinical_session_service()
        ),
        signal_service=(
            get_clinical_signal_service()
        ),
        summary_service=(
            get_clinical_summary_service()
        ),
        conversation_service=(
            get_conversation_service()
        ),
        document_service=(
            get_document_service()
        ),
    )


def get_patient_intake_completion_service() -> PatientIntakeCompletionService:
    return PatientIntakeCompletionService(
        session_service=(
            get_clinical_session_service()
        ),
        ephemeral_identity_service=(
            get_ephemeral_identity_service()
        ),
        interview_controller=(
            get_interview_controller()
        ),
        workflow_service=(
            get_workflow_service()
        ),
    )


def get_admin_dashboard_service() -> AdminDashboardService:
    return AdminDashboardService(
        doctor_repository=DoctorRepository(),
        assignment_repository=(
            AssignmentRepository()
        ),
        queue_service=QueueService(
            QueueRepository()
        ),
        session_service=ClinicalSessionService(
            ClinicalSessionRepository()
        ),
        patient_service=PatientService(
            PatientRepository()
        ),
        summary_service=ClinicalSummaryService(
            ClinicalSummaryRepository()
        ),
        promotion_service=(
            get_promotion_service()
        ),
    )
