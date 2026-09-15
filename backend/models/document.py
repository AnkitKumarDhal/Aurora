from datetime import datetime
from pydantic import Field
from domain.enums import DocumentStatus, DocumentType
from .common import PersistenceModel


class DocumentDocument(PersistenceModel):
    document_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    document_type: DocumentType
    filename: str
    storage_reference: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    mime_type: str | None = None
    created_at: datetime
    updated_at: datetime
    collection_name = "documents"


class DocumentExtractionDocument(PersistenceModel):
    extraction_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    extracted_text: str | None = None
    structured_data: dict = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime
    collection_name = "document_extractions"
