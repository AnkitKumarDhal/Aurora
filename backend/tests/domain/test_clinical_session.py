import pytest

from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import (
    ConsentStatus,
    SessionStatus,
    VerificationStatus,
)


def make_session() -> ClinicalSession:
    return ClinicalSession(
        session_id="session-001",
        patient_id="patient-001",
        department_id="general-medicine",
    )


def test_session_starts_in_created_state():
    session = make_session()

    assert session.status == SessionStatus.CREATED
    assert session.verification_status == VerificationStatus.PENDING
    assert session.consent_status == ConsentStatus.PENDING
    assert session.started_at is None
    assert session.completed_at is None


def test_valid_session_flow():
    session = make_session()

    session.transition_to(SessionStatus.IDENTIFYING)
    assert session.status == SessionStatus.IDENTIFYING
    assert session.started_at is not None

    session.transition_to(SessionStatus.CONSENTED)
    session.transition_to(SessionStatus.HISTORY_IN_PROGRESS)
    session.transition_to(SessionStatus.DOCUMENT_PROCESSING)
    session.transition_to(SessionStatus.SUMMARY_READY)
    session.transition_to(SessionStatus.QUEUED)
    session.transition_to(SessionStatus.ASSIGNED)
    session.transition_to(SessionStatus.CALLED)
    session.transition_to(SessionStatus.IN_CONSULTATION)
    session.transition_to(SessionStatus.COMPLETED)

    assert session.status == SessionStatus.COMPLETED
    assert session.completed_at is not None


def test_history_can_finish_without_document_processing():
    session = make_session()

    session.transition_to(SessionStatus.IDENTIFYING)
    session.transition_to(SessionStatus.CONSENTED)
    session.transition_to(SessionStatus.HISTORY_IN_PROGRESS)
    session.transition_to(SessionStatus.SUMMARY_READY)

    assert session.status == SessionStatus.SUMMARY_READY


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (SessionStatus.CREATED, SessionStatus.COMPLETED),
        (SessionStatus.CREATED, SessionStatus.QUEUED),
        (SessionStatus.IDENTIFYING, SessionStatus.QUEUED),
        (SessionStatus.CONSENTED, SessionStatus.ASSIGNED),
        (SessionStatus.HISTORY_IN_PROGRESS, SessionStatus.COMPLETED),
        (SessionStatus.SUMMARY_READY, SessionStatus.IN_CONSULTATION),
        (SessionStatus.COMPLETED, SessionStatus.QUEUED),
        (SessionStatus.CANCELLED, SessionStatus.IDENTIFYING),
        (SessionStatus.ABANDONED, SessionStatus.HISTORY_IN_PROGRESS),
        (SessionStatus.ERROR, SessionStatus.QUEUED),
    ],
)
def test_invalid_session_transition_is_rejected(current, target):
    session = make_session()
    session.status = current

    with pytest.raises(ValueError, match="Invalid clinical session transition"):
        session.transition_to(target)


def test_completed_session_is_terminal():
    session = make_session()
    session.status = SessionStatus.COMPLETED

    with pytest.raises(ValueError):
        session.transition_to(SessionStatus.QUEUED)


def test_cancelled_session_is_terminal():
    session = make_session()
    session.status = SessionStatus.CANCELLED

    with pytest.raises(ValueError):
        session.transition_to(SessionStatus.IDENTIFYING)


def test_completed_at_is_only_set_when_completed():
    session = make_session()

    session.transition_to(SessionStatus.IDENTIFYING)
    session.transition_to(SessionStatus.CONSENTED)

    assert session.completed_at is None


def test_required_session_fields():
    with pytest.raises(ValueError):
        ClinicalSession(
            patient_id="patient-001",
            department_id="general-medicine",
        )


def test_empty_session_id_is_rejected():
    with pytest.raises(ValueError):
        ClinicalSession(
            session_id="",
            patient_id="patient-001",
            department_id="general-medicine",
        )
