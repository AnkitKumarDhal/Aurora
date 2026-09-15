from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_document_service
from backend.api.schemas.documents import (
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentResponse,
)
from backend.services.document import DocumentService

router = APIRouter(
    prefix="/sessions/{session_id}/documents",
    tags=["documents"],
)


def document_response(document) -> DocumentResponse:
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


def extraction_response(extraction) -> DocumentExtractionResponse:
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


@router.get(
    "",
    response_model=dict[str, DocumentListResponse],
)
async def get_session_documents(
    session_id: str,
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
    "/{document_id}/extraction",
    response_model=dict[str, DocumentExtractionResponse | None],
)
async def get_document_extraction(
    session_id: str,
    document_id: str,
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
