from collections.abc import AsyncGenerator
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from config import settings

client = AsyncMongoClient(settings.mongo_uri)
database = client[settings.mongo_database]


async def get_database() -> AsyncGenerator[AsyncDatabase, None]:
    yield database


async def close_database() -> None:
    await client.close()
