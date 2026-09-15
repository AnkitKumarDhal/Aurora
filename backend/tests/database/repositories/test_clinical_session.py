from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus
from backend.models.clinical_session import ClinicalSessionDocument


@pytest.fixture
def clinical_session() -> ClinicalSessionDocument:
    now = datetime.now(timezone.utc)

    return ClinicalSessionDocument(
        session_id="session-001",
        patient_id="patient-001",
        department_id="general-medicine",
        status=SessionStatus.CREATED,
        verification_status=VerificationStatus.PENDING,
        consent_status=ConsentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repository() -> ClinicalSessionRepository:
    repository = ClinicalSessionRepository()
    repository.collection = AsyncMock()
    return repository


@pytest.mark.asyncio
async def test_get_session(repository: ClinicalSessionRepository, clinical_session: ClinicalSessionDocument,) -> None:
    repository.collection.find_one.return_value = (clinical_session.to_mongo())
    result = await repository.get_session("session-001")
    assert result is not None
    assert result.session_id == "session-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"session_id": "session-001"},)
