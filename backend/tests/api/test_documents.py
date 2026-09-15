from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import (
    get_document_service,
    get_storage,
)
from backend.domain.document import Document, DocumentExtraction
from backend.domain.enums import DocumentStatus, DocumentType
from backend.main import app


def build_document(
    session_id: str = "sess-test",
) -> Document:
    timestamp = datetime.now(timezone.utc)

    return Document(
        document_id="doc-test",
        session_id=session_id,
        filename="blood-report.pdf",
        document_type=DocumentType.LAB_REPORT,
        content_type="application/pdf",
        size_bytes=1024,
        storage_reference="mock://documents/doc-test",
        status=DocumentStatus.UPLOADED,
        created_at=timestamp,
        updated_at=timestamp,
    )


def build_extraction() -> DocumentExtraction:
    timestamp = datetime.now(timezone.utc)

    return DocumentExtraction(
        extraction_id="ext-test",
        document_id="doc-test",
        status=DocumentStatus.PROCESSED,
        extracted_text="Hemoglobin: 13.2 g/dL",
        structured_data={
            "hemoglobin": 13.2,
        },
        processed_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )


def override_service() -> AsyncMock:
    service = AsyncMock()
    app.dependency_overrides[get_document_service] = lambda: service
    return service


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_upload_document() -> None:
    service = override_service()

    storage = AsyncMock()
    storage.save.return_value = "mock://documents/uploaded.pdf"
    app.dependency_overrides[get_storage] = lambda: storage

    service.create_document.return_value = build_document()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/sess-test/documents",
            params={"document_type": "LAB_REPORT"},
            files={
                "file": (
                    "blood-report.pdf",
                    b"fake pdf content",
                    "application/pdf",
                ),
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["document_id"] == "doc-test"
    assert response.json()["data"]["document_type"] == "LAB_REPORT"

    storage.save.assert_awaited_once()

    uploaded_document = service.create_document.await_args.args[0]
    assert uploaded_document.session_id == "sess-test"
    assert uploaded_document.filename == "blood-report.pdf"
    assert uploaded_document.document_type == DocumentType.LAB_REPORT


def test_get_session_documents() -> None:
    service = override_service()
    service.get_session_documents.return_value = [build_document()]

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents",
        )

    assert response.status_code == 200
    assert len(response.json()["data"]["documents"]) == 1
    assert response.json()["data"]["documents"][0]["document_id"] == "doc-test"


def test_get_document() -> None:
    service = override_service()
    service.get_document.return_value = build_document()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 200
    assert response.json()["data"]["document_id"] == "doc-test"


def test_get_document_rejects_wrong_session() -> None:
    service = override_service()
    service.get_document.return_value = build_document(
        session_id="different-session",
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 404


def test_get_document_extraction() -> None:
    service = override_service()
    service.get_document.return_value = build_document()
    service.get_extraction.return_value = build_extraction()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test/extraction",
        )

    assert response.status_code == 200
    assert response.json()["data"]["extraction_id"] == "ext-test"
    assert response.json()["data"]["status"] == "PROCESSED"
