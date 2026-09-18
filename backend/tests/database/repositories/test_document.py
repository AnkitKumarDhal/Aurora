from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.database.repositories.document import DocumentRepository
from backend.domain.enums import DocumentStatus, DocumentType
from backend.models.document import DocumentDocument


def make_document() -> DocumentDocument:
    timestamp = datetime.now(timezone.utc)

    return DocumentDocument(
        document_id="document-1",
        session_id="session-1",
        document_type=DocumentType.PRESCRIPTION,
        filename="prescription.pdf",
        storage_reference="documents/prescription.pdf",
        status=DocumentStatus.PROCESSED,
        content_type="application/pdf",
        size_bytes=1024,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_session_documents_uses_lazy_collection():
    repository = DocumentRepository()
    document = make_document()

    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter([document.to_mongo()])

    collection = MagicMock()
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(return_value=collection)

    result = await repository.get_session_documents("session-1")

    repository._get_collection.assert_called_once_with()
    collection.find.assert_called_once_with(
        {"session_id": "session-1"},
        sort=[("created_at", 1)],
    )

    assert len(result) == 1
    assert result[0].document_id == "document-1"
