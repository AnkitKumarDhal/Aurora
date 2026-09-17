from datetime import datetime, timedelta, timezone

from backend.domain.enums import QueueStatus, UrgencyLevel
from backend.domain.queue import QueueEntry
from backend.services.queue_engine import QueueEngine


def make_entry(
    queue_entry_id: str,
    priority_score: int,
    queued_at: datetime,
    status: QueueStatus = QueueStatus.WAITING,
) -> QueueEntry:
    return QueueEntry(
        queue_entry_id=queue_entry_id,
        session_id=f"session-{queue_entry_id}",
        department_id="general-medicine",
        status=status,
        priority_score=priority_score,
        urgency_level=UrgencyLevel.LEVEL_1,
        queued_at=queued_at,
    )


def test_higher_priority_patient_is_first():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entries = [
        make_entry("low", 30, now),
        make_entry("high", 80, now),
    ]

    ordered = engine.sort_entries(entries, now)

    assert [entry.queue_entry_id for entry in ordered] == ["high", "low"]


def test_waiting_time_increases_effective_priority():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entry = make_entry(
        "patient-1",
        40,
        now - timedelta(minutes=10),
    )

    assert engine.effective_priority(entry, now) == 45.0


def test_waiting_time_can_move_patient_ahead():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    newer_high = make_entry(
        "newer-high",
        50,
        now,
    )

    older_low = make_entry(
        "older-low",
        45,
        now - timedelta(minutes=20),
    )

    ordered = engine.sort_entries(
        [newer_high, older_low],
        now,
    )

    assert [entry.queue_entry_id for entry in ordered] == [
        "older-low",
        "newer-high",
    ]


def test_waiting_bonus_is_capped():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entry = make_entry(
        "patient-1",
        40,
        now - timedelta(hours=10),
    )

    assert engine.effective_priority(entry, now) == 70.0


def test_missing_priority_score_is_lowest_priority():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entry = make_entry(
        "patient-1",
        40,
        now,
    )

    entry.priority_score = None

    other = make_entry(
        "patient-2",
        1,
        now,
    )

    ordered = engine.sort_entries([entry, other], now)

    assert [item.queue_entry_id for item in ordered] == [
        "patient-2",
        "patient-1",
    ]


def test_non_waiting_entries_are_not_in_queue_order():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    waiting = make_entry(
        "waiting",
        20,
        now,
    )

    called = make_entry(
        "called",
        100,
        now,
        QueueStatus.CALLED,
    )

    ordered = engine.sort_entries(
        [called, waiting],
        now,
    )

    assert [entry.queue_entry_id for entry in ordered] == ["waiting"]


def test_positions_are_assigned_in_queue_order():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entries = [
        make_entry("third", 20, now),
        make_entry("first", 80, now),
        make_entry("second", 50, now),
    ]

    ordered = engine.assign_positions(entries, now)

    assert [entry.queue_entry_id for entry in ordered] == [
        "first",
        "second",
        "third",
    ]

    assert [entry.position for entry in ordered] == [1, 2, 3]


def test_next_patient_returns_highest_priority_patient():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entries = [
        make_entry("patient-1", 30, now),
        make_entry("patient-2", 70, now),
    ]

    patient = engine.next_patient(entries, now)

    assert patient is not None
    assert patient.queue_entry_id == "patient-2"


def test_next_patient_returns_none_for_empty_queue():
    engine = QueueEngine()

    assert engine.next_patient([]) is None


def test_tie_is_deterministic():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entries = [
        make_entry("patient-b", 50, now),
        make_entry("patient-a", 50, now),
    ]

    ordered = engine.sort_entries(entries, now)

    assert [entry.queue_entry_id for entry in ordered] == [
        "patient-a",
        "patient-b",
    ]


def test_future_queue_time_does_not_reduce_priority():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    entry = make_entry(
        "patient-1",
        50,
        now + timedelta(minutes=10),
    )

    assert engine.effective_priority(entry, now) == 50.0


def test_naive_queued_time_is_treated_as_utc():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)
    queued_at = (
        now - timedelta(minutes=10)
    ).replace(tzinfo=None)

    entry = make_entry(
        "patient-1",
        40,
        queued_at,
    )

    assert engine.effective_priority(entry, now) == 45.0


def test_naive_queued_times_can_be_sorted():
    engine = QueueEngine()
    now = datetime.now(timezone.utc)

    older = (
        now - timedelta(minutes=20)
    ).replace(tzinfo=None)
    newer = (
        now - timedelta(minutes=5)
    ).replace(tzinfo=None)

    entries = [
        make_entry("newer", 40, newer),
        make_entry("older", 40, older),
    ]

    ordered = engine.sort_entries(entries, now)

    assert [entry.queue_entry_id for entry in ordered] == [
        "older",
        "newer",
    ]
