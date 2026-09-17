from datetime import datetime, timedelta, timezone
from backend.api.routes.doctor_queue import _waiting_time_seconds
from backend.domain.enums import QueueStatus


def test_waiting_time_grows_for_waiting_entry():
    queued_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    result = _waiting_time_seconds(
        queued_at,
        QueueStatus.WAITING,
    )

    assert result is not None
    assert 299 <= result <= 301


def test_waiting_time_freezes_at_called_at():
    queued_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    called_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    result = _waiting_time_seconds(
        queued_at,
        QueueStatus.CALLED,
        called_at,
    )

    assert result is not None
    assert 899 <= result <= 901


def test_waiting_time_handles_naive_mongo_datetime():
    queued_at = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).replace(tzinfo=None)

    result = _waiting_time_seconds(
        queued_at,
        QueueStatus.WAITING,
    )

    assert result is not None
    assert 299 <= result <= 301
