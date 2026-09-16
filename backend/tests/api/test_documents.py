from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_assignment_repository, get_document_service, get_storage
from backend.auth.dependencies import get_current_user
from backend.domain.document import Document, DocumentExtraction
from backend.domain.enums import ActorRole, AssignmentStatus, DocumentStatus, DocumentType
from backend.domain.user import User
from backend.main import app


def build_document(session_id: str = "sess-test") -> Document:
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


def build_user(actor_id: str = "doctor-1") -> User:
    now = datetime.now(timezone.utc)

    return User(
        user_id=f"user-{actor_id}",
        username=actor_id,
        password_hash="",
        role=ActorRole.DOCTOR,
        actor_id=actor_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def build_assignment(doctor_id: str = "doctor-1"):
    now = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "sess-test",
            "doctor_id": doctor_id,
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": now,
            "released_at": None,
        },
    )()


def override_service(service: AsyncMock) -> None:
    app.dependency_overrides[get_document_service] = lambda: service


def override_doctor(doctor_id: str = "doctor-1") -> None:
    app.dependency_overrides[get_current_user] = lambda: build_user(doctor_id)

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = build_assignment(
        doctor_id
    )
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_upload_document() -> None:
    service = AsyncMock()
    storage = AsyncMock()

    storage.save.return_value = "mock://documents/uploaded.pdf"
    service.create_document.return_value = build_document()

    override_service(service)
    app.dependency_overrides[get_storage] = lambda: storage

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
    service = AsyncMock()
    service.get_session_documents.return_value = [build_document()]

    override_service(service)
    override_doctor()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents",
        )

    assert response.status_code == 200
    assert len(response.json()["data"]["documents"]) == 1
    assert response.json()["data"]["documents"][0]["document_id"] == "doc-test"


def test_get_session_documents_requires_authentication() -> None:
    service = AsyncMock()
    override_service(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents",
        )

    assert response.status_code == 401
    service.get_session_documents.assert_not_awaited()


def test_get_session_documents_rejects_unassigned_doctor() -> None:
    service = AsyncMock()

    override_service(service)
    app.dependency_overrides[get_current_user] = lambda: build_user("doctor-1")

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = build_assignment(
        "doctor-2"
    )
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents"
        )

    assert response.status_code == 403
    service.get_session_documents.assert_not_awaited()


def test_get_document() -> None:
    service = AsyncMock()
    service.get_document.return_value = build_document()

    override_service(service)
    override_doctor()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 200
    assert response.json()["data"]["document_id"] == "doc-test"


def test_get_document_requires_authentication() -> None:
    service = AsyncMock()
    override_service(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 401
    service.get_document.assert_not_awaited()


def test_get_document_rejects_wrong_session() -> None:
    service = AsyncMock()
    service.get_document.return_value = build_document(
        session_id="different-session",
    )

    override_service(service)
    override_doctor()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test",
        )

    assert response.status_code == 404


def test_get_document_extraction() -> None:
    service = AsyncMock()
    service.get_document.return_value = build_document()
    service.get_extraction.return_value = build_extraction()

    override_service(service)
    override_doctor()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test/extraction",
        )

    assert response.status_code == 200
    assert response.json()["data"]["extraction_id"] == "ext-test"
    assert response.json()["data"]["status"] == "PROCESSED"


def test_get_document_extraction_requires_authentication() -> None:
    service = AsyncMock()
    override_service(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/documents/doc-test/extraction",
        )

    assert response.status_code == 401
    service.get_document.assert_not_awaited()
