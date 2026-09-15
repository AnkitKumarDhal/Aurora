from unittest.mock import AsyncMock

import pytest

from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.enums import TriageStatus, UrgencyLevel
from backend.domain.triage import TriageResult
from backend.services.triage import TriageService


@pytest.mark.asyncio
async def test_assess_from_signals_uses_triage_engine():
    repository = AsyncMock()
    repository.update_result.return_value = {
        "triage_result_id": "triage-1",
        "session_id": "session-1",
        "status": TriageStatus.ASSESSED,
        "urgency_level": UrgencyLevel.LEVEL_4,
        "priority_score": 75,
        "red_flags_present": False,
        "assessed_at": None,
        "created_at": None,
        "updated_at": None,
    }

    service = TriageService(repository)

    signals = [
        ClinicalSignal(
            signal_id="signal-1",
            session_id="session-1",
            type="symptom",
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
    repository.update_result.return_value = {
        "triage_result_id": "triage-1",
        "session_id": "session-1",
        "status": TriageStatus.ASSESSED,
        "urgency_level": UrgencyLevel.LEVEL_5,
        "priority_score": 100,
        "red_flags_present": True,
        "assessed_at": None,
        "created_at": None,
        "updated_at": None,
    }

    service = TriageService(repository)

    signals = [
        ClinicalSignal(
            signal_id="signal-1",
            session_id="session-1",
            type="red_flag",
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
