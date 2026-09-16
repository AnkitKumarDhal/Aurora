from backend.models.document import DocumentDocument, DocumentExtractionDocument
from .base import BaseRepository


class DocumentRepository(BaseRepository[DocumentDocument]):
    collection_name = DocumentDocument.collection_name
    model = DocumentDocument

    async def get_document(self, document_id: str,) -> DocumentDocument | None:
        return await self.get_one({"document_id": document_id})

    async def get_session_documents(self, session_id: str,) -> list[DocumentDocument]:
        cursor = self.collection.find(
            {"session_id": session_id},
            sort=[("created_at", 1)],
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_document(self, document: DocumentDocument,) -> DocumentDocument:
        return await self.create(document)

    async def update_document(self, document_id: str, updates: dict,) -> DocumentDocument | None:
        return await self.update_one({"document_id": document_id}, updates,)


class DocumentExtractionRepository(BaseRepository[DocumentExtractionDocument]):
    collection_name = DocumentExtractionDocument.collection_name
    model = DocumentExtractionDocument

    async def get_extraction(self, extraction_id: str,) -> DocumentExtractionDocument | None:
        return await self.get_one({"extraction_id": extraction_id})

    async def get_document_extraction(self, document_id: str,) -> DocumentExtractionDocument | None:
        return await self.get_one({"document_id": document_id})

    async def create_extraction(self, extraction: DocumentExtractionDocument,) -> DocumentExtractionDocument:
        return await self.create(extraction)

    async def update_extraction(self, extraction_id: str, updates: dict,) -> DocumentExtractionDocument | None:
        return await self.update_one({"extraction_id": extraction_id}, updates,)
