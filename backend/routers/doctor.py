from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import sessions_collection, users_collection, documents_collection
from auth.dependencies import require_role

router = APIRouter()


@router.get("/queue")
async def get_queue(user: dict = Depends(require_role("doctor"))):
    sessions = await sessions_collection.find(
        {"status": {"$in": ["in_progress", "summarized"]}},
        {"_id": 0}
    ).to_list(length=None)

    items = []
    for s in sessions:
        patient = await users_collection.find_one({"login_id": s["login_id"]}, {"_id": 0})
        items.append({
            "session_id": s["session_id"],
            "patient_login_id": s["login_id"],
            "patient_name": patient["name"] if patient else "Unknown",
            "patient_age": patient.get("age") if patient else None,
            "status": s["status"],
            "red_flag": s.get("red_flag", False),
            "waiting_since": s.get("created_at"),
        })

    items.sort(key=lambda x: (not x["red_flag"], x["waiting_since"] or ""))
    return {"items": items, "count": len(items)}


@router.get("/patients/{session_id}")
async def get_patient_case(session_id: str, user: dict = Depends(require_role("doctor"))):
    session = await sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    patient = await users_collection.find_one({"login_id": session["login_id"]}, {"_id": 0})
    docs = await documents_collection.find(
        {"session_id": session_id},
        {"_id": 0}
    ).to_list(length=None)

    return {
        "session_id": session_id,
        "patient": {
            "login_id": patient["login_id"],
            "name": patient["name"],
            "age": patient.get("age"),
            "gender": patient.get("gender"),
        } if patient else None,
        "summary": None,
        "documents": docs,
        "conversation": session.get("conversation", [])
    }


class ApproveRequest(BaseModel):
    edits: list[dict] = []


@router.post("/patients/{session_id}/approve")
async def approve_case(session_id: str, req: ApproveRequest, user: dict = Depends(require_role("doctor"))):
    session = await sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # TODO: apply req.edits to the actual summary document once summaries exist
    # TODO: append to doctor_edits log with old_text/new_text/edited_at

    await sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"status": "approved"}},
    )

    return {
        "session_id": session_id,
        "status": "approved",
        "doctor_edits": req.edits,
    }
