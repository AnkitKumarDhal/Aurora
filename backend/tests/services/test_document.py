from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.document import (
    DocumentExtractionRepository,
    DocumentRepository,
)
from backend.domain.document import Document, DocumentExtraction
from backend.domain.enums import DocumentStatus, DocumentType
from backend.models.document import (
    DocumentDocument,
    DocumentExtractionDocument,
)
from backend.services.document import DocumentService


@pytest.fixture
def document_repository() -> DocumentRepository:
    return AsyncMock(spec=DocumentRepository)


@pytest.fixture
def extraction_repository() -> DocumentExtractionRepository:
    return AsyncMock(spec=DocumentExtractionRepository)


@pytest.fixture
def service(
    document_repository: DocumentRepository,
    extraction_repository: DocumentExtractionRepository,
) -> DocumentService:
    return DocumentService(
        document_repository,
        extraction_repository,
    )


@pytest.fixture
def document() -> DocumentDocument:
    timestamp = datetime.now(timezone.utc)

    return DocumentDocument(
        document_id="doc-1",
        session_id="session-1",
        document_type=DocumentType.LAB_REPORT,
        filename="blood-report.pdf",
        storage_reference="uploads/doc-1",
        status=DocumentStatus.UPLOADED,
        content_type="application/pdf",
        size_bytes=1024,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.fixture
def extraction() -> DocumentExtractionDocument:
    timestamp = datetime.now(timezone.utc)

    return DocumentExtractionDocument(
        extraction_id="extraction-1",
        document_id="doc-1",
        status=DocumentStatus.PROCESSING,
        extracted_text=None,
        structured_data=None,
        processed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_document(
    service: DocumentService,
    document_repository: DocumentRepository,
    document: DocumentDocument,
) -> None:
    document_repository.get_document.return_value = document

    result = await service.get_document("doc-1")

    assert result is not None
    assert result.document_id == "doc-1"
    assert result.filename == "blood-report.pdf"

    document_repository.get_document.assert_awaited_once_with("doc-1")


@pytest.mark.asyncio
async def test_get_session_documents(
    service: DocumentService,
    document_repository: DocumentRepository,
    document: DocumentDocument,
) -> None:
    document_repository.get_session_documents.return_value = [document]

    result = await service.get_session_documents("session-1")

    assert len(result) == 1
    assert result[0].document_id == "doc-1"


@pytest.mark.asyncio
async def test_create_document(
    service: DocumentService,
    document_repository: DocumentRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    document = Document(
        document_id="doc-1",
        session_id="session-1",
        filename="report.pdf",
        document_type=DocumentType.LAB_REPORT,
        content_type="application/pdf",
        size_bytes=500,
        storage_reference="uploads/doc-1",
        status=DocumentStatus.UPLOADED,
        created_at=timestamp,
        updated_at=timestamp,
    )

    result = await service.create_document(document)

    assert result is document
    document_repository.create_document.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_processing(
    service: DocumentService,
    document_repository: DocumentRepository,
    document: DocumentDocument,
) -> None:
    processing_document = document.model_copy(
        update={"status": DocumentStatus.PROCESSING},
    )

    document_repository.update_document.return_value = processing_document

    result = await service.mark_processing("doc-1")

    assert result is not None
    assert result.status == DocumentStatus.PROCESSING

    document_repository.update_document.assert_awaited_once_with(
        "doc-1",
        {"status": DocumentStatus.PROCESSING},
    )


@pytest.mark.asyncio
async def test_get_extraction(
    service: DocumentService,
    extraction_repository: DocumentExtractionRepository,
    extraction: DocumentExtractionDocument,
) -> None:
    extraction_repository.get_document_extraction.return_value = extraction

    result = await service.get_extraction("doc-1")

    assert result is not None
    assert result.extraction_id == "extraction-1"
    assert result.document_id == "doc-1"


@pytest.mark.asyncio
async def test_complete_extraction(
    service: DocumentService,
    extraction_repository: DocumentExtractionRepository,
    extraction: DocumentExtractionDocument,
) -> None:
    processed = extraction.model_copy(
        update={
            "status": DocumentStatus.PROCESSED,
            "extracted_text": "Hemoglobin: 13.2",
            "structured_data": {
                "hemoglobin": 13.2,
            },
        },
    )

    extraction_repository.update_extraction.return_value = processed

    result = await service.complete_extraction(
        "extraction-1",
        extracted_text="Hemoglobin: 13.2",
        structured_data={"hemoglobin": 13.2},
    )

    assert result is not None
    assert result.status == DocumentStatus.PROCESSED
    assert result.extracted_text == "Hemoglobin: 13.2"

    extraction_repository.update_extraction.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_missing_document(
    service: DocumentService,
    document_repository: DocumentRepository,
) -> None:
    document_repository.update_document.return_value = None

    result = await service.update_document(
        "missing",
        {"status": DocumentStatus.PROCESSING},
    )

    assert result is None
