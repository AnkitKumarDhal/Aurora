from typing import Generic, TypeVar
from backend.database.connection import get_database_instance
from backend.models.common import PersistenceModel


ModelT = TypeVar("ModelT", bound=PersistenceModel)


class BaseRepository(Generic[ModelT]):
    collection_name: str
    model: type[ModelT]

    def __init__(self) -> None:
        database = get_database_instance()
        self.collection = database[self.collection_name]

    async def get_one(self, filter_query: dict) -> ModelT | None:
        document = await self.collection.find_one(filter_query)

        if document is None:
            return None

        return self.model.from_mongo(document)

    async def create(self, model: ModelT) -> ModelT:
        await self.collection.insert_one(model.to_mongo())
        return model

    async def update_one(self, filter_query: dict, updates: dict,) -> ModelT | None:
        await self.collection.update_one(filter_query, {"$set": updates},)
        return await self.get_one(filter_query)
