from backend.domain.assignment import DoctorAssignment
from backend.domain.clinical_session import ClinicalSession
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.document import Document
from backend.domain.patient import Patient
from backend.domain.triage import TriageResult
from backend.services.assignment import AssignmentService
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.document import DocumentService
from backend.services.patient import PatientService
from backend.services.triage import TriageService


class DoctorCaseService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        patient_service: PatientService,
        summary_service: ClinicalSummaryService,
        document_service: DocumentService,
        triage_service: TriageService,
        assignment_service: AssignmentService,
    ) -> None:
        self.session_service = session_service
        self.patient_service = patient_service
        self.summary_service = summary_service
        self.document_service = document_service
        self.triage_service = triage_service
        self.assignment_service = assignment_service

    async def get_case(
        self,
        session_id: str,
    ) -> dict[str, object] | None:
        session = await self.session_service.get_session(session_id)

        if session is None:
            return None

        patient = await self.patient_service.get_patient(session.patient_id)
        summary = await self.summary_service.get_session_summary(session_id)
        documents = await self.document_service.get_session_documents(
            session_id,
        )
        triage = await self.triage_service.get_session_result(session_id)
        assignment = await self.assignment_service.get_session_assignment(
            session_id,
        )

        return {
            "session": session,
            "patient": patient,
            "summary": summary,
            "documents": documents,
            "triage": triage,
            "assignment": assignment,
        }
