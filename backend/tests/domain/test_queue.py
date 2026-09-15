import pytest
from pydantic import ValidationError

from backend.domain.enums import QueueStatus, UrgencyLevel
from backend.domain.queue import QueueEntry


def make_queue_entry() -> QueueEntry:
    return QueueEntry(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
    )


def test_queue_entry_defaults():
    entry = make_queue_entry()

    assert entry.status == QueueStatus.WAITING
    assert entry.position is None
    assert entry.urgency_level is None
    assert entry.priority_score is None
    assert entry.doctor_id is None
    assert entry.queued_at is None
    assert entry.called_at is None
    assert entry.completed_at is None


def test_queue_entry_accepts_valid_position():
    entry = QueueEntry(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
        position=1,
    )

    assert entry.position == 1


@pytest.mark.parametrize("position", [0, -1])
def test_queue_position_must_be_positive(position):
    with pytest.raises(ValidationError):
        QueueEntry(
            queue_entry_id="queue-001",
            session_id="session-001",
            department_id="general-medicine",
            position=position,
        )


@pytest.mark.parametrize(
    "urgency_level",
    list(UrgencyLevel),
)
def test_queue_accepts_all_urgency_levels(urgency_level):
    entry = QueueEntry(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
        urgency_level=urgency_level,
    )

    assert entry.urgency_level == urgency_level


@pytest.mark.parametrize("priority_score", [0, 50, 100])
def test_queue_accepts_valid_priority_scores(priority_score):
    entry = QueueEntry(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
        priority_score=priority_score,
    )

    assert entry.priority_score == priority_score


@pytest.mark.parametrize("priority_score", [-1, 101])
def test_queue_rejects_invalid_priority_scores(priority_score):
    with pytest.raises(ValidationError):
        QueueEntry(
            queue_entry_id="queue-001",
            session_id="session-001",
            department_id="general-medicine",
            priority_score=priority_score,
        )


def test_queue_entry_supports_assignment():
    entry = QueueEntry(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
        doctor_id="doctor-001",
        position=3,
    )

    assert entry.doctor_id == "doctor-001"
    assert entry.position == 3
