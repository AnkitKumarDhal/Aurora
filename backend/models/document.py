from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import DocumentStatus, DocumentType
from .common import PersistenceModel


class DocumentDocument(PersistenceModel):
    document_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    document_type: DocumentType
    filename: str
    storage_reference: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    content_type: str
    size_bytes: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "documents"


class DocumentExtractionDocument(PersistenceModel):
    extraction_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    status: DocumentStatus
    extracted_text: str | None = None
    structured_data: dict[str, object] | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "document_extractions"
