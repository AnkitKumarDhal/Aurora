from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.clinical_signal import ClinicalSignalRepository
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.enums import ClinicalSignalType
from backend.models.clinical_signal import ClinicalSignalDocument
from backend.services.clinical_signal import ClinicalSignalService


@pytest.fixture
def repository() -> ClinicalSignalRepository:
    return AsyncMock(spec=ClinicalSignalRepository)


@pytest.fixture
def service(
    repository: ClinicalSignalRepository,
) -> ClinicalSignalService:
    return ClinicalSignalService(repository)


@pytest.fixture
def document() -> ClinicalSignalDocument:
    timestamp = datetime.now(timezone.utc)

    return ClinicalSignalDocument(
        signal_id="signal-1",
        session_id="session-1",
        signal_type=ClinicalSignalType.SYMPTOM,
        name="headache",
        value=True,
        confidence=0.95,
        source="conversation",
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_signal(
    service: ClinicalSignalService,
    repository: ClinicalSignalRepository,
    document: ClinicalSignalDocument,
) -> None:
    repository.get_signal.return_value = document

    result = await service.get_signal("signal-1")

    assert result is not None
    assert result.signal_id == "signal-1"
    assert result.name == "headache"
    assert result.value is True
    assert result.confidence == 0.95

    repository.get_signal.assert_awaited_once_with("signal-1")


@pytest.mark.asyncio
async def test_get_signal_missing(
    service: ClinicalSignalService,
    repository: ClinicalSignalRepository,
) -> None:
    repository.get_signal.return_value = None

    result = await service.get_signal("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_session_signals(
    service: ClinicalSignalService,
    repository: ClinicalSignalRepository,
    document: ClinicalSignalDocument,
) -> None:
    repository.get_session_signals.return_value = [document]

    result = await service.get_session_signals("session-1")

    assert len(result) == 1
    assert result[0].signal_id == "signal-1"

    repository.get_session_signals.assert_awaited_once_with(
        "session-1",
    )


@pytest.mark.asyncio
async def test_create_signal(
    service: ClinicalSignalService,
    repository: ClinicalSignalRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    signal = ClinicalSignal(
        signal_id="signal-1",
        session_id="session-1",
        signal_type=ClinicalSignalType.SYMPTOM,
        name="fever",
        value=True,
        confidence=0.9,
        source="conversation",
        created_at=timestamp,
        updated_at=timestamp,
    )

    result = await service.create_signal(signal)

    assert result is signal
    repository.create_signal.assert_awaited_once()

    created_document = repository.create_signal.await_args.args[0]

    assert created_document.signal_id == "signal-1"
    assert created_document.name == "fever"
    assert created_document.value is True


@pytest.mark.asyncio
async def test_update_signal(
    service: ClinicalSignalService,
    repository: ClinicalSignalRepository,
    document: ClinicalSignalDocument,
) -> None:
    updated = document.model_copy(
        update={"confidence": 0.99},
    )

    repository.update_signal.return_value = updated

    result = await service.update_signal(
        "signal-1",
        {"confidence": 0.99},
    )

    assert result is not None
    assert result.confidence == 0.99

    repository.update_signal.assert_awaited_once_with(
        "signal-1",
        {"confidence": 0.99},
    )
