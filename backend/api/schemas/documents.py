from datetime import datetime
from pydantic import BaseModel
from backend.domain.enums import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    document_id: str
    session_id: str
    filename: str
    document_type: DocumentType
    content_type: str
    size_bytes: int
    storage_reference: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentExtractionResponse(BaseModel):
    extraction_id: str
    document_id: str
    status: DocumentStatus
    extracted_text: str | None = None
    structured_data: dict[str, object] | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
