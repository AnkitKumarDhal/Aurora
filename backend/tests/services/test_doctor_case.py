from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.services.doctor_case import DoctorCaseService


def make_session():
    now = datetime.now(timezone.utc)

    return type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "patient_id": "patient-1",
            "department_id": "general-medicine",
            "created_at": now,
            "updated_at": now,
        },
    )()


def make_patient():
    now = datetime.now(timezone.utc)

    return type(
        "Patient",
        (),
        {
            "patient_id": "patient-1",
            "display_name": "Demo Patient",
            "date_of_birth": date(1998, 5, 14),
            "age": 28,
            "abha_reference": "11-22-33-44-55-66",
            "hospital_reference": "HOSP-001",
            "created_at": now,
            "updated_at": now,
        },
    )()


def make_summary():
    now = datetime.now(timezone.utc)

    return type(
        "Summary",
        (),
        {
            "summary_id": "summary-1",
            "session_id": "session-1",
            "status": type("Status", (), {"value": "READY"})(),
            "created_at": now,
            "updated_at": now,
        },
    )()


@pytest.mark.asyncio
async def test_get_case_aggregates_doctor_case_data():
    session_service = AsyncMock()
    patient_service = AsyncMock()
    summary_service = AsyncMock()
    document_service = AsyncMock()
    triage_service = AsyncMock()
    assignment_service = AsyncMock()

    session = make_session()
    patient = make_patient()
    summary = make_summary()
    documents = ["document-1", "document-2"]
    triage = "triage-1"
    assignment = "assignment-1"

    session_service.get_session.return_value = session
    patient_service.get_patient.return_value = patient
    summary_service.get_session_summary.return_value = summary
    document_service.get_session_documents.return_value = documents
    triage_service.get_session_result.return_value = triage
    assignment_service.get_session_assignment_history.return_value = assignment

    service = DoctorCaseService(
        session_service=session_service,
        patient_service=patient_service,
        summary_service=summary_service,
        document_service=document_service,
        triage_service=triage_service,
        assignment_service=assignment_service,
    )

    result = await service.get_case("session-1")

    assert result == {
        "session": session,
        "patient": patient,
        "summary": summary,
        "documents": documents,
        "triage": triage,
        "assignment": assignment,
    }

    session_service.get_session.assert_awaited_once_with("session-1")
    patient_service.get_patient.assert_awaited_once_with("patient-1")
    summary_service.get_session_summary.assert_awaited_once_with(
        "session-1",
    )
    document_service.get_session_documents.assert_awaited_once_with(
        "session-1",
    )
    triage_service.get_session_result.assert_awaited_once_with(
        "session-1",
    )
    assignment_service.get_session_assignment_history.assert_awaited_once_with(
        "session-1",
    )


@pytest.mark.asyncio
async def test_get_case_returns_none_for_missing_session():
    session_service = AsyncMock()
    patient_service = AsyncMock()
    summary_service = AsyncMock()
    document_service = AsyncMock()
    triage_service = AsyncMock()
    assignment_service = AsyncMock()

    session_service.get_session.return_value = None

    service = DoctorCaseService(
        session_service=session_service,
        patient_service=patient_service,
        summary_service=summary_service,
        document_service=document_service,
        triage_service=triage_service,
        assignment_service=assignment_service,
    )

    result = await service.get_case("missing-session")

    assert result is None
    patient_service.get_patient.assert_not_awaited()
    summary_service.get_session_summary.assert_not_awaited()
    document_service.get_session_documents.assert_not_awaited()
    triage_service.get_session_result.assert_not_awaited()
    assignment_service.get_session_assignment_history.assert_not_awaited()
