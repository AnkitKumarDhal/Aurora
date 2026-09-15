from collections.abc import AsyncGenerator
from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from backend.database import get_database
from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.queue import QueueRepository
from backend.services.clinical_session import ClinicalSessionService
from backend.services.queue import QueueService


async def get_clinical_session_service(database: AsyncDatabase = Depends(get_database)) -> AsyncGenerator[ClinicalSessionService, None]:
    repository = ClinicalSessionRepository(database)
    yield ClinicalSessionService(repository)


async def get_queue_service(database: AsyncDatabase = Depends(get_database)) -> AsyncGenerator[QueueService, None]:
    repository = QueueRepository(database)
    yield QueueService(repository)
