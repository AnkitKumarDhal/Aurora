from collections.abc import AsyncGenerator
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from backend.config import settings

client: AsyncMongoClient | None = None
database: AsyncDatabase | None = None


async def initialize_database_connection() -> None:
    global client, database
    if client is not None:
        return
    client = AsyncMongoClient(settings.mongo_uri)
    database = client[settings.mongo_database]
    await client.admin.command("ping")


def get_database_instance() -> AsyncDatabase:
    if database is None:
        raise RuntimeError("Database connection has not been initialized")
    return database


async def get_database() -> AsyncGenerator[AsyncDatabase, None]:
    yield get_database_instance()


async def close_database() -> None:
    global client, database
    if client is not None:
        await client.close()
    client = None
    database = None
