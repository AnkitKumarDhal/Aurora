from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_doctor_case_service
from backend.api.schemas.doctor_case import (
    DoctorCaseAssignmentResponse,
    DoctorCaseDocumentResponse,
    DoctorCasePatientResponse,
    DoctorCaseResponse,
    DoctorCaseSessionResponse,
    DoctorCaseSummaryResponse,
    DoctorCaseTriageResponse,
)
from backend.auth.authorization import require_doctor_case_access
from backend.domain.assignment import DoctorAssignment
from backend.domain.clinical_session import ClinicalSession
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.document import Document
from backend.domain.patient import Patient
from backend.domain.triage import TriageResult
from backend.domain.user import User
from backend.services.doctor_case import DoctorCaseService


router = APIRouter(
    prefix="/doctors/me/cases",
    tags=["doctor-cases"],
)


def _session_response(
    session: ClinicalSession,
) -> DoctorCaseSessionResponse:
    return DoctorCaseSessionResponse(
        session_id=session.session_id,
        patient_id=session.patient_id,
        department_id=session.department_id,
        status=session.status,
        verification_status=session.verification_status,
        consent_status=session.consent_status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _patient_response(
    patient: Patient,
) -> DoctorCasePatientResponse:
    return DoctorCasePatientResponse(
        patient_id=patient.patient_id,
        display_name=patient.display_name,
        date_of_birth=patient.date_of_birth,
        age=patient.age,
        abha_reference=patient.abha_reference,
        hospital_reference=patient.hospital_reference,
    )


def _summary_response(
    summary: ClinicalSummary,
) -> DoctorCaseSummaryResponse:
    return DoctorCaseSummaryResponse(
        summary_id=summary.summary_id,
        session_id=summary.session_id,
        status=summary.status.value,
        chief_complaint=summary.chief_complaint,
        history_of_present_illness=summary.history_of_present_illness,
        past_medical_history=summary.past_medical_history,
        medications=summary.medications,
        allergies=summary.allergies,
        relevant_documents=summary.relevant_documents,
        clinical_signals=summary.clinical_signals,
        generated_at=summary.generated_at,
        confirmed_by=summary.confirmed_by,
        confirmed_at=summary.confirmed_at,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


def _document_response(
    document: Document,
) -> DoctorCaseDocumentResponse:
    return DoctorCaseDocumentResponse(
        document_id=document.document_id,
        session_id=document.session_id,
        filename=document.filename,
        document_type=document.document_type,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        storage_reference=document.storage_reference,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _triage_response(
    triage: TriageResult,
) -> DoctorCaseTriageResponse:
    return DoctorCaseTriageResponse(
        triage_id=triage.triage_id,
        session_id=triage.session_id,
        status=triage.status,
        urgency_level=triage.urgency_level,
        priority_score=triage.priority_score,
        red_flags_present=triage.red_flags_present,
        assessed_at=triage.assessed_at,
    )


def _assignment_response(
    assignment: DoctorAssignment,
) -> DoctorCaseAssignmentResponse:
    return DoctorCaseAssignmentResponse(
        assignment_id=assignment.assignment_id,
        session_id=assignment.session_id,
        doctor_id=assignment.doctor_id,
        department_id=assignment.department_id,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
    )


@router.get(
    "/{session_id}",
    response_model=dict[str, DoctorCaseResponse],
)
async def get_doctor_case(
    session_id: str,
    current_user: User = Depends(
        require_doctor_case_access,
    ),
    service: DoctorCaseService = Depends(
        get_doctor_case_service,
    ),
) -> dict[str, DoctorCaseResponse]:
    case = await service.get_case(session_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical session not found",
        )

    patient = case["patient"]
    summary = case["summary"]
    triage = case["triage"]
    assignment = case["assignment"]

    response = DoctorCaseResponse(
        session=_session_response(case["session"]),
        patient=_patient_response(patient) if patient is not None else None,
        summary=_summary_response(summary) if summary is not None else None,
        documents=[
            _document_response(document)
            for document in case["documents"]
        ],
        triage=_triage_response(triage) if triage is not None else None,
        assignment=(
            _assignment_response(assignment)
            if assignment is not None
            else None
        ),
    )

    return {"data": response}
