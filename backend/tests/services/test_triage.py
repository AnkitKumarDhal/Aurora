from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.triage import TriageRepository
from backend.domain.enums import TriageStatus, UrgencyLevel
from backend.domain.triage import TriageResult
from backend.models.triage import TriageResultDocument
from backend.services.triage import TriageService


@pytest.fixture
def repository() -> TriageRepository:
    return AsyncMock(spec=TriageRepository)


@pytest.fixture
def service(repository: TriageRepository) -> TriageService:
    return TriageService(repository)


@pytest.fixture
def document() -> TriageResultDocument:
    timestamp = datetime.now(timezone.utc)

    return TriageResultDocument(
        triage_result_id="triage-1",
        session_id="session-1",
        status=TriageStatus.PENDING,
        urgency_level=UrgencyLevel.LEVEL_3,
        priority_score=60,
        red_flags_present=False,
        assessed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_result(
    service: TriageService,
    repository: TriageRepository,
    document: TriageResultDocument,
) -> None:
    repository.get_result.return_value = document

    result = await service.get_result("triage-1")

    assert result is not None
    assert result.triage_id == "triage-1"
    assert result.session_id == "session-1"
    assert result.urgency_level == UrgencyLevel.LEVEL_3
    assert result.priority_score == 60

    repository.get_result.assert_awaited_once_with("triage-1")


@pytest.mark.asyncio
async def test_get_result_missing(
    service: TriageService,
    repository: TriageRepository,
) -> None:
    repository.get_result.return_value = None

    result = await service.get_result("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_session_result(
    service: TriageService,
    repository: TriageRepository,
    document: TriageResultDocument,
) -> None:
    repository.get_session_result.return_value = document

    result = await service.get_session_result("session-1")

    assert result is not None
    assert result.triage_id == "triage-1"
    assert result.session_id == "session-1"

    repository.get_session_result.assert_awaited_once_with("session-1")


@pytest.mark.asyncio
async def test_create_result(
    service: TriageService,
    repository: TriageRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    result = TriageResult(
        triage_id="triage-1",
        session_id="session-1",
        status=TriageStatus.PENDING,
        urgency_level=UrgencyLevel.LEVEL_3,
        priority_score=60,
        red_flags_present=False,
        assessed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )

    created = await service.create_result(result)

    assert created is result
    repository.create_result.assert_awaited_once()

    created_document = repository.create_result.await_args.args[0]

    assert created_document.triage_result_id == "triage-1"
    assert created_document.session_id == "session-1"
    assert created_document.urgency_level == UrgencyLevel.LEVEL_3
    assert created_document.priority_score == 60


@pytest.mark.asyncio
async def test_assess(
    service: TriageService,
    repository: TriageRepository,
    document: TriageResultDocument,
) -> None:
    assessed = document.model_copy(
        update={
            "status": TriageStatus.ASSESSED,
            "urgency_level": UrgencyLevel.LEVEL_2,
            "priority_score": 85,
            "red_flags_present": True,
            "assessed_at": datetime.now(timezone.utc),
        },
    )

    repository.update_result.return_value = assessed

    result = await service.assess(
        "triage-1",
        UrgencyLevel.LEVEL_2,
        85,
        True,
    )

    assert result is not None
    assert result.status == TriageStatus.ASSESSED
    assert result.urgency_level == UrgencyLevel.LEVEL_2
    assert result.priority_score == 85
    assert result.red_flags_present is True
    assert result.assessed_at is not None

    repository.update_result.assert_awaited_once()

    updates = repository.update_result.await_args.args[1]

    assert updates["status"] == TriageStatus.ASSESSED
    assert updates["urgency_level"] == UrgencyLevel.LEVEL_2
    assert updates["priority_score"] == 85
    assert updates["red_flags_present"] is True
    assert updates["assessed_at"] is not None


@pytest.mark.asyncio
async def test_fail(
    service: TriageService,
    repository: TriageRepository,
    document: TriageResultDocument,
) -> None:
    failed = document.model_copy(
        update={
            "status": TriageStatus.FAILED,
            "assessed_at": datetime.now(timezone.utc),
        },
    )

    repository.update_result.return_value = failed

    result = await service.fail("triage-1")

    assert result is not None
    assert result.status == TriageStatus.FAILED
    assert result.assessed_at is not None

    repository.update_result.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_missing_result(
    service: TriageService,
    repository: TriageRepository,
) -> None:
    repository.update_result.return_value = None

    result = await service.update_result(
        "missing",
        {"status": TriageStatus.ASSESSED},
    )

    assert result is None
