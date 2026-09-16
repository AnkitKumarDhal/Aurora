from backend.models.user import UserDocument
from .base import BaseRepository


class UserRepository(BaseRepository[UserDocument]):
    collection_name = UserDocument.collection_name
    model = UserDocument

    async def get_user(self, user_id: str,) -> UserDocument | None:
        return await self.get_one({"user_id": user_id, })

    async def get_by_username(self, username: str,) -> UserDocument | None:
        return await self.get_one({"username": username, })

    async def create_user(self, user: UserDocument,) -> UserDocument:
        return await self.create(user)

    async def update_user(self, user_id: str, updates: dict,) -> UserDocument | None:
        return await self.update_one(
            {
                "user_id": user_id,
            },
            updates,
        )
