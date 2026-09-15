from typing import Any, Generic, TypeVar

from backend.database.connection import get_database_instance
from backend.models.common import PersistenceModel


ModelT = TypeVar("ModelT", bound=PersistenceModel)


class BaseRepository(Generic[ModelT]):
    collection_name: str
    model: type[ModelT]

    def __init__(self) -> None:
        self.collection: Any | None = None

    def _get_collection(self) -> Any:
        if self.collection is None:
            database = get_database_instance()
            self.collection = database[self.collection_name]

        return self.collection

    async def get_one(self, filter_query: dict) -> ModelT | None:
        collection = self._get_collection()
        document = await collection.find_one(filter_query)

        if document is None:
            return None

        return self.model.from_mongo(document)

    async def create(self, model: ModelT) -> ModelT:
        collection = self._get_collection()
        await collection.insert_one(model.to_mongo())
        return model

    async def update_one(
        self,
        filter_query: dict,
        updates: dict,
    ) -> ModelT | None:
        collection = self._get_collection()
        await collection.update_one(
            filter_query,
            {"$set": updates},
        )
        return await self.get_one(filter_query)
