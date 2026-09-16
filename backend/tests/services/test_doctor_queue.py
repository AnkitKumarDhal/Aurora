from unittest.mock import AsyncMock
import pytest
from backend.services.doctor_queue import DoctorQueueService


def make_doctor():
    return type(
        "Doctor",
        (),
        {
            "doctor_id": "doctor-1",
            "department_ids": ["general-medicine"],
        },
    )()


def make_queue_entry():
    return type(
        "QueueEntry",
        (),
        {
            "queue_entry_id": "queue-1",
            "session_id": "session-1",
            "doctor_id": "doctor-1",
            "department_id": "general-medicine",
            "position": 1,
        },
    )()


def make_session():
    return type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "patient_id": "patient-1",
        },
    )()


def make_patient():
    return type(
        "Patient",
        (),
        {
            "patient_id": "patient-1",
            "display_name": "Demo Patient",
            "age": 28,
        },
    )()


@pytest.mark.asyncio
async def test_get_doctor_queue_returns_assigned_entries():
    doctor_repository = AsyncMock()
    session_service = AsyncMock()
    queue_service = AsyncMock()
    patient_service = AsyncMock()
    summary_service = AsyncMock()

    doctor_repository.get_doctor.return_value = make_doctor()
    queue_service.get_department_queue.return_value = [
        make_queue_entry(),
    ]
    session_service.get_session.return_value = make_session()
    patient_service.get_patient.return_value = make_patient()
    summary_service.get_session_summary.return_value = None

    service = DoctorQueueService(
        doctor_repository=doctor_repository,
        session_service=session_service,
        queue_service=queue_service,
        patient_service=patient_service,
        summary_service=summary_service,
    )

    result = await service.get_doctor_queue("doctor-1")

    assert len(result) == 1
    assert result[0]["queue_entry"].queue_entry_id == "queue-1"
    assert result[0]["patient"].patient_id == "patient-1"
    assert result[0]["summary"] is None

    doctor_repository.get_doctor.assert_awaited_once_with(
        "doctor-1",
    )
    queue_service.get_department_queue.assert_awaited_once_with(
        "general-medicine",
    )


@pytest.mark.asyncio
async def test_get_doctor_queue_filters_entries_for_other_doctors():
    doctor_repository = AsyncMock()
    session_service = AsyncMock()
    queue_service = AsyncMock()
    patient_service = AsyncMock()
    summary_service = AsyncMock()

    other_entry = make_queue_entry()
    other_entry.doctor_id = "doctor-2"

    doctor_repository.get_doctor.return_value = make_doctor()
    queue_service.get_department_queue.return_value = [
        other_entry,
    ]

    service = DoctorQueueService(
        doctor_repository=doctor_repository,
        session_service=session_service,
        queue_service=queue_service,
        patient_service=patient_service,
        summary_service=summary_service,
    )

    result = await service.get_doctor_queue("doctor-1")

    assert result == []
    session_service.get_session.assert_not_awaited()
    patient_service.get_patient.assert_not_awaited()
    summary_service.get_session_summary.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_doctor_queue_returns_empty_for_unknown_doctor():
    doctor_repository = AsyncMock()
    session_service = AsyncMock()
    queue_service = AsyncMock()
    patient_service = AsyncMock()
    summary_service = AsyncMock()

    doctor_repository.get_doctor.return_value = None

    service = DoctorQueueService(
        doctor_repository=doctor_repository,
        session_service=session_service,
        queue_service=queue_service,
        patient_service=patient_service,
        summary_service=summary_service,
    )

    result = await service.get_doctor_queue("missing-doctor")

    assert result == []
    queue_service.get_department_queue.assert_not_awaited()
