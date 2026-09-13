from motor.motor_asyncio import AsynIOMotorClient
from config import MONGO_URI, DB_NAME

client = AsynIOMotorClient(MONGO_URI)
db = client[DB_NAME]

patients_collection = db["patients"]
sessions_collection = db["sessions"]
documents_colelction = db["documents"]
summaries_collection = db["summaries"]
