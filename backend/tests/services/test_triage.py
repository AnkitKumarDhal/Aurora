from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.enums import ClinicalSignalType, TriageStatus, UrgencyLevel
from backend.models.triage import TriageResultDocument
from backend.services.triage import TriageService


def make_result(
    urgency_level: UrgencyLevel,
    priority_score: int,
    red_flags_present: bool,
) -> TriageResultDocument:
    timestamp = datetime.now(timezone.utc)

    return TriageResultDocument(
        triage_result_id="triage-1",
        session_id="session-1",
        status=TriageStatus.ASSESSED,
        urgency_level=urgency_level,
        priority_score=priority_score,
        red_flags_present=red_flags_present,
        assessed_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_assess_from_signals_uses_triage_engine():
    repository = AsyncMock()
    repository.update_result.return_value = make_result(
        UrgencyLevel.LEVEL_4,
        75,
        False,
    )

    service = TriageService(repository)

    signals = [
        ClinicalSignal(
            signal_id="signal-1",
            session_id="session-1",
            signal_type=ClinicalSignalType.SYMPTOM,
            name="severe_pain",
            value=True,
            confidence=1.0,
            source="ai",
        )
    ]

    result = await service.assess_from_signals("triage-1", signals)

    assert result is not None
    assert result.urgency_level == UrgencyLevel.LEVEL_4
    assert result.priority_score == 75
    assert result.red_flags_present is False
    repository.update_result.assert_awaited_once()


@pytest.mark.asyncio
async def test_assess_from_signals_persists_critical_red_flag():
    repository = AsyncMock()
    repository.update_result.return_value = make_result(
        UrgencyLevel.LEVEL_5,
        100,
        True,
    )

    service = TriageService(repository)

    signals = [
        ClinicalSignal(
            signal_id="signal-1",
            session_id="session-1",
            signal_type=ClinicalSignalType.RED_FLAG,
            name="severe_chest_pain",
            value=True,
            confidence=1.0,
            source="ai",
        )
    ]

    result = await service.assess_from_signals("triage-1", signals)

    assert result is not None
    assert result.urgency_level == UrgencyLevel.LEVEL_5
    assert result.priority_score == 100
    assert result.red_flags_present is True
