from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

patients_collection = db["patients"]
sessions_collection = db["sessions"]
documents_collection = db["documents"]
summaries_collection = db["summaries"]
