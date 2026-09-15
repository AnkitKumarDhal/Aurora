from .connection import database
from .indexes import create_indexes


COLLECTIONS = (
    "patients",
    "doctors",
    "departments",
    "clinical_sessions",
    "conversation_turns",
    "clinical_signals",
    "documents",
    "document_extractions",
    "clinical_summaries",
    "triage_results",
    "queue_entries",
    "doctor_assignments",
    "promotion_requests",
)


async def initialize_database() -> None:
    existing_collections = set(await database.list_collection_names())

    missing_collections = [
        collection
        for collection in COLLECTIONS
        if collection not in existing_collections
    ]

    for collection in missing_collections:
        await database.create_collection(collection)

    await create_indexes()
