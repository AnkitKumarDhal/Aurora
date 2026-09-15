from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_document_service
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
    assert response.json()["data"]["documents"][0]["status"] == "UPLOADED"


def test_get_document() -> None:
    service = override_service()
    service.get_document.return_value = build_document()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 200
    assert response.json()["data"]["document_id"] == "doc-test"
    assert response.json()["data"]["session_id"] == "sess-test"


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
    assert response.json()["data"]["extracted_text"] == (
        "Hemoglobin: 13.2 g/dL"
    )


def test_get_missing_document_extraction() -> None:
    service = override_service()
    service.get_document.return_value = build_document()
    service.get_extraction.return_value = None

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test/extraction",
        )

    assert response.status_code == 200
    assert response.json()["data"] is None
