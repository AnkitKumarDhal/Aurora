from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from backend.api.dependencies import get_document_service, get_storage
from backend.api.schemas.documents import (
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentResponse,
)
from backend.auth.authorization import require_assigned_doctor_access
from backend.domain.document import Document
from backend.domain.enums import DocumentStatus, DocumentType
from backend.domain.user import User
from backend.integrations.storage import LocalStorage
from backend.services.document import DocumentService


router = APIRouter(
    prefix="/sessions/{session_id}/documents",
    tags=["documents"],
)


def document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        document_id=document.document_id,
        session_id=document.session_id,
        filename=document.filename,
        document_type=document.document_type,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        storage_reference=document.storage_reference,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def extraction_response(
    extraction,
) -> DocumentExtractionResponse:
    return DocumentExtractionResponse(
        extraction_id=extraction.extraction_id,
        document_id=extraction.document_id,
        status=extraction.status,
        extracted_text=extraction.extracted_text,
        structured_data=extraction.structured_data,
        processed_at=extraction.processed_at,
        created_at=extraction.created_at,
        updated_at=extraction.updated_at,
    )


@router.post(
    "",
    response_model=dict[str, DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    session_id: str,
    document_type: DocumentType,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    storage: LocalStorage = Depends(get_storage),
) -> dict[str, DocumentResponse]:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename",
        )

    size_bytes = file.size or 0

    storage_reference = await storage.save(
        session_id,
        file,
    )

    document = Document(
        document_id=f"doc_{uuid4().hex}",
        session_id=session_id,
        filename=file.filename,
        document_type=document_type,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        storage_reference=storage_reference,
        status=DocumentStatus.UPLOADED,
    )

    try:
        result = await service.create_document(document)
    except ValueError as exc:
        await storage.delete(storage_reference)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": document_response(result),
    }


@router.get(
    "",
    response_model=dict[str, DocumentListResponse],
)
async def get_session_documents(
    session_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: DocumentService = Depends(get_document_service),
) -> dict[str, DocumentListResponse]:
    documents = await service.get_session_documents(session_id)

    return {
        "data": DocumentListResponse(
            documents=[
                document_response(document)
                for document in documents
            ],
        ),
    }


@router.get(
    "/{document_id}",
    response_model=dict[str, DocumentResponse],
)
async def get_document(
    session_id: str,
    document_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: DocumentService = Depends(get_document_service),
) -> dict[str, DocumentResponse]:
    document = await service.get_document(document_id)

    if document is None or document.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {
        "data": document_response(document),
    }


@router.get(
    "/{document_id}/file",
)
async def get_document_file(
    session_id: str,
    document_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: DocumentService = Depends(get_document_service),
) -> FileResponse:
    document = await service.get_document(document_id)

    if document is None or document.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    path = Path(document.storage_reference)

    if not path.exists() or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original document file is unavailable",
        )

    return FileResponse(
        path=path,
        media_type=document.content_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.get(
    "/{document_id}/extraction",
    response_model=dict[str, DocumentExtractionResponse | None],
)
async def get_document_extraction(
    session_id: str,
    document_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: DocumentService = Depends(get_document_service),
) -> dict[str, DocumentExtractionResponse | None]:
    document = await service.get_document(document_id)

    if document is None or document.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    extraction = await service.get_extraction(document_id)

    return {
        "data": (
            extraction_response(extraction)
            if extraction is not None
            else None
        ),
    }
