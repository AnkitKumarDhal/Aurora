from fastapi import APIRouter
from pydantic import BaseModel
import uuid
from db import sessions_collection

router = APIRouter()


class NewSession(BaseModel):
    patient_id: str


@router.post("")
async def create_session(req: NewSession):
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "patient_id": req.patient_id,
        "status": "in_progress",
        "red_flag": False,
        "conversation": [
            {
                "role": "ai",
                "text": "What brings you in today?",
                "turn": 1
            }
        ]
    }
    await sessions_collection.insert_one(session)
    return {"session_id": session_id, "first_question": session["conversation"][0]}


class ConverseRequest(BaseModel):
    text: str
    input_mode: str = "text"


@router.post("/{session_id}/converse")
async def converse(session_id: str, req: ConverseRequest):
    # TODO: call llm_service to get next adaptive question + red_flag check
    return {
        "next_question": "Can you describe where exactly it hurts?",
        "red_flag": False
    }
