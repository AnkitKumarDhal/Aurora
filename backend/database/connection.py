from collections.abc import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
database = client[settings.mongo_database]


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield database


async def close_databse() -> None:
    client.close()
