from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid

from db import sessions_collection
from auth.dependencies import require_role

router = APIRouter()


async def get_owned_session(session_id: str, user: dict) -> dict:
    session = await sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["login_id"] != user["sub"]:
        raise HTTPException(
            status_code=403, detail="You do not own this session")
    return session


@router.post("")
async def create_session(user: dict = Depends(require_role("patient"))):
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "login_id": user["sub"],
        "status": "in_progress",
        "red_flag": False,
        "conversation": [
            {
                "role": "ai",
                "text": "What brings you in today?",
                "turn": 1,
            }
        ],
    }
    await sessions_collection.insert_one(session)
    return {"session_id": session_id, "status": "in_progress", "first_question": session["conversation"][0]}


@router.get("/{session_id}")
async def get_session(session_id: str, user: dict = Depends(require_role("patient"))):
    session = await get_owned_session(session_id, user)
    return session


class ConverseRequest(BaseModel):
    text: str
    input_mode: str = "text"


@router.get("/{session_id}/converse")
async def converse(session_id: str, req: ConverseRequest, user: dict = Depends(require_role("patient"))):
    session = await get_owned_session(session_id, user)
    if session["status"] != "in_progress":
        raise HTTPException(status_code=409, detail=f"Session is already {
                            session['status']}")

    # TODO: call llm_service for the next adaptive question + red_flag check
    # TODO: append patient's answer + AI's next question to session["conversation"], persist via update_one
    return {
        "next_question": "Can you describe where exactly it hurts?",
        "turn": len(session["conversation"]) + 1,
        "red_flag": False,
        "red_flag_reason": None,
        "status": "in_progress",
    }


class SkipRequest(BaseModel):
    reason: str = "dont_know"


@router.post("/{session_id}/skip")
async def skip(session_id: str, req: SkipRequest, user: dict = Depends(require_role("patient"))):
    session = await get_owned_session(session_id, user)

    if session["status"] != "in_progress":
        raise HTTPException(status_code=409, detail=f"Session is already {
                            session['status']}")

    # TODO: same advance-the-conversation logic as /converse, just skipping the current question
    return {
        "next_question": "Can you describe where exactly it hurts?",
        "turn": len(session["conversation"]) + 1,
        "red_flag": False,
        "red_flag_reason": None,
        "status": "in_progress",
    }
