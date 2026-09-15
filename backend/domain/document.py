from datetime import datetime
from .common import TimestampedModel
from .enums import DocumentStatus, DocumentType


class Document(TimestampedModel):
    document_id: str
    session_id: str
    filename: str
    document_type: DocumentType
    content_type: str
    size_bytes: int
    storage_reference: str
    status: DocumentStatus = DocumentStatus.UPLOADED


class DocumentExtraction(TimestampedModel):
    extraction_id: str
    document_id: str
    status: DocumentStatus
    extracted_text: str | None = None
    structured_data: dict[str, object] | None = None
    processed_at: datetime | None = None
