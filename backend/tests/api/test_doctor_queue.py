from datetime import datetime, timedelta, timezone

from backend.api.routes.doctor_queue import _waiting_time_seconds


def test_waiting_time_seconds_handles_timezone_aware_datetime() -> None:
    queued_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    result = _waiting_time_seconds(queued_at)

    assert result is not None
    assert 299 <= result <= 301


def test_waiting_time_seconds_handles_timezone_naive_datetime() -> None:
    queued_at = (datetime.now(timezone.utc) -
                 timedelta(minutes=5)).replace(tzinfo=None)

    result = _waiting_time_seconds(queued_at)

    assert result is not None
    assert 299 <= result <= 301


def test_waiting_time_seconds_returns_none_for_missing_datetime() -> None:
    assert _waiting_time_seconds(None) is None
