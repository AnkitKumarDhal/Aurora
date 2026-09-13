from fastapi import APIRouter
from pydantic import BaseModel
import uuid
from db import patients_collection

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    age: int
    gender: str
    phone: str


@router.post("/register")
async def register(req: RegisterRequest):
    patient_id = str(uuid.uuid4()),
    login_id = str(uuid.uuid8())[:8],
    patient = {
        "patient_id": patient_id,
        "login_id": login_id,
        **req.dict()
    }
    await patients_collection.insert_one(patient)
    return {"patient_id": patient_id, "login_id": login_id}


class LoginRequest(BaseModel):
    login_id: str


@router.post("/login")
async def login(req: LoginRequest):
    patient = await patients_collection.find_one(
        {"login_id": req.login()},
        {"_id": 0}
    )
    if not patient:
        return {"error": "not found"}
    return patient
