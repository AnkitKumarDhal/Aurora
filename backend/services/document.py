from datetime import datetime, timezone

from backend.database.repositories.document import (
    DocumentExtractionRepository,
    DocumentRepository,
)
from backend.domain.document import Document, DocumentExtraction
from backend.domain.enums import DocumentStatus
from backend.models.document import (
    DocumentDocument,
    DocumentExtractionDocument,
)


class DocumentService:
    def __init__(self, document_repository: DocumentRepository, extraction_repository: DocumentExtractionRepository,) -> None:
        self.document_repository = document_repository
        self.extraction_repository = extraction_repository

    async def get_document(self, document_id: str,) -> Document | None:
        document = await self.document_repository.get_document(document_id)
        if document is None:
            return None
        return self._document_to_domain(document)

    async def get_session_documents(self, session_id: str,) -> list[Document]:
        documents = await self.document_repository.get_session_documents(session_id,)
        return [
            self._document_to_domain(document)
            for document in documents
        ]

    async def create_document(self, document: Document,) -> Document:
        persistence_document = self._document_to_persistence(document)
        await self.document_repository.create_document(persistence_document,)
        return document

    async def update_document(self, document_id: str, updates: dict,) -> Document | None:
        document = await self.document_repository.update_document(document_id, updates,)
        if document is None:
            return None
        return self._document_to_domain(document)

    async def mark_processing(self, document_id: str,) -> Document | None:
        return await self.update_document(document_id, {
            "status": DocumentStatus.PROCESSING,
        },
        )

    async def mark_processed(self, document_id: str,) -> Document | None:
        return await self.update_document(document_id, {
            "status": DocumentStatus.PROCESSED,
        },
        )

    async def mark_failed(self, document_id: str,) -> Document | None:
        return await self.update_document(document_id, {
            "status": DocumentStatus.FAILED,
        },
        )

    async def get_extraction(self, document_id: str,) -> DocumentExtraction | None:
        extraction = await self.extraction_repository.get_document_extraction(document_id,)
        if extraction is None:
            return None
        return self._extraction_to_domain(extraction)

    async def create_extraction(self, extraction: DocumentExtraction,) -> DocumentExtraction:
        persistence_extraction = self._extraction_to_persistence(extraction,)
        await self.extraction_repository.create_extraction(persistence_extraction,)
        return extraction

    async def update_extraction(self, extraction_id: str, updates: dict,) -> DocumentExtraction | None:
        extraction = await self.extraction_repository.update_extraction(extraction_id, updates,)
        if extraction is None:
            return None
        return self._extraction_to_domain(extraction)

    async def mark_extraction_processing(self, extraction_id: str,) -> DocumentExtraction | None:
        return await self.update_extraction(extraction_id, {
            "status": DocumentStatus.PROCESSING,
        },
        )

    async def complete_extraction(
        self,
        extraction_id: str,
        extracted_text: str | None = None,
        structured_data: dict[str, object] | None = None,
    ) -> DocumentExtraction | None:
        return await self.update_extraction(extraction_id, {
            "status": DocumentStatus.PROCESSED,
            "extracted_text": extracted_text,
            "structured_data": structured_data,
            "processed_at": datetime.now(timezone.utc),
        },
        )

    async def fail_extraction(self, extraction_id: str,) -> DocumentExtraction | None:
        return await self.update_extraction(extraction_id, {
            "status": DocumentStatus.FAILED,
        },
        )

    @staticmethod
    def _document_to_domain(document: DocumentDocument,) -> Document:
        return Document(
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

    @staticmethod
    def _document_to_persistence(document: Document,) -> DocumentDocument:
        return DocumentDocument(
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

    @staticmethod
    def _extraction_to_domain(extraction: DocumentExtractionDocument,) -> DocumentExtraction:
        return DocumentExtraction(
            extraction_id=extraction.extraction_id,
            document_id=extraction.document_id,
            status=extraction.status,
            extracted_text=extraction.extracted_text,
            structured_data=extraction.structured_data,
            processed_at=extraction.processed_at,
            created_at=extraction.created_at,
            updated_at=extraction.updated_at,
        )

    @staticmethod
    def _extraction_to_persistence(extraction: DocumentExtraction,) -> DocumentExtractionDocument:
        return DocumentExtractionDocument(
            extraction_id=extraction.extraction_id,
            document_id=extraction.document_id,
            status=extraction.status,
            extracted_text=extraction.extracted_text,
            structured_data=extraction.structured_data,
            processed_at=extraction.processed_at,
            created_at=extraction.created_at,
            updated_at=extraction.updated_at,
        )
