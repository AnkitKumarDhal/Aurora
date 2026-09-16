from backend.models.conversation import ConversationTurnDocument
from .base import BaseRepository


class ConversationRepository(BaseRepository[ConversationTurnDocument]):
    collection_name = ConversationTurnDocument.collection_name
    model = ConversationTurnDocument

    async def get_turn(self, turn_id: str,) -> ConversationTurnDocument | None:
        return await self.get_one({"turn_id": turn_id})

    async def get_session_turns(self, session_id: str,) -> list[ConversationTurnDocument]:
        cursor = self.collection.find(
            {"session_id": session_id},
            sort=[("created_at", 1)],
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_turn(self, turn: ConversationTurnDocument,) -> ConversationTurnDocument:
        return await self.create(turn)
