from backend.domain.enums import PromotionStatus
from backend.models.promotion import PromotionRequestDocument
from .base import BaseRepository


class PromotionRepository(BaseRepository[PromotionRequestDocument]):
    collection_name = PromotionRequestDocument.collection_name
    model = PromotionRequestDocument

    async def get_request(self, promotion_request_id: str,) -> PromotionRequestDocument | None:
        return await self.get_one({
            "promotion_request_id": promotion_request_id,
        })

    async def get_queue_request(self, queue_entry_id: str,) -> PromotionRequestDocument | None:
        return await self.get_one({
            "queue_entry_id": queue_entry_id,
            "status": PromotionStatus.PENDING,
        })

    async def get_pending_requests(self,) -> list[PromotionRequestDocument]:
        collection = self._get_collection()
        cursor = collection.find(
            {"status": PromotionStatus.PENDING},
            sort=[("decision_deadline", 1)],
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_request(self, request: PromotionRequestDocument,) -> PromotionRequestDocument:
        return await self.create(request)

    async def update_request(self, promotion_request_id: str, updates: dict,) -> PromotionRequestDocument | None:
        return await self.update_one({
            "promotion_request_id": promotion_request_id,
        }, updates,)
