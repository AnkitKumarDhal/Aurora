from datetime import date, datetime

from pydantic import BaseModel

from backend.domain.enums import (
    AssignmentStatus,
    ConsentStatus,
    DocumentStatus,
    DocumentType,
    SessionStatus,
    TriageStatus,
    UrgencyLevel,
    VerificationStatus,
)


class DoctorCasePatientResponse(BaseModel):
    patient_id: str
    display_name: str
    date_of_birth: date | None = None
    age: int | None = None
    abha_reference: str | None = None
    hospital_reference: str | None = None


class DoctorCaseSessionResponse(BaseModel):
    session_id: str
    patient_id: str
    department_id: str
    status: SessionStatus
    verification_status: VerificationStatus
    consent_status: ConsentStatus
    created_at: datetime
    updated_at: datetime


class DoctorCaseDocumentResponse(BaseModel):
    document_id: str
    session_id: str
    filename: str
    document_type: DocumentType
    content_type: str
    size_bytes: int
    storage_reference: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DoctorCaseSummaryResponse(BaseModel):
    summary_id: str
    session_id: str
    status: str
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: list[str]
    medications: list[str]
    allergies: list[str]
    relevant_documents: list[str]
    clinical_signals: list[str]
    generated_at: datetime | None = None
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DoctorCaseTriageResponse(BaseModel):
    triage_id: str
    session_id: str
    status: TriageStatus
    urgency_level: UrgencyLevel | None
    priority_score: int | None
    red_flags_present: bool
    assessed_at: datetime | None


class DoctorCaseAssignmentResponse(BaseModel):
    assignment_id: str
    session_id: str
    doctor_id: str
    department_id: str
    status: AssignmentStatus
    assigned_at: datetime | None
    released_at: datetime | None


class DoctorCaseResponse(BaseModel):
    session: DoctorCaseSessionResponse
    patient: DoctorCasePatientResponse | None
    summary: DoctorCaseSummaryResponse | None
    documents: list[DoctorCaseDocumentResponse]
    triage: DoctorCaseTriageResponse | None
    assignment: DoctorCaseAssignmentResponse | None
