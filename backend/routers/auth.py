from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid

from db import users_collection
from auth.security import hash_password, verify_password, create_access_token

router = APIRouter()


class UserRole(str, Enum):
    patient = "patient"
    doctor = "doctor"


class RegisterRequest(BaseModel):
    name: str
    role: UserRole
    password: str

    # Patient-only fields
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None

    # Doctor-only fields
    specialization: Optional[str] = None


@router.post("/register")
async def register(req: RegisterRequest):
    login_id = str(uuid.uuid4())[:8]
    hashed_pw = hash_password(req.password)

    user_doc = {
        "login_id": login_id,
        "name": req.name,
        "role": req.role,
        "hashed_password": hashed_pw,
        "age": req.age,
        "gender": req.gender,
        "phone": req.phone,
        "specialization": req.specialization,
    }
    await users_collection.insert_one(user_doc)
    token = create_access_token(user_id=login_id, role=req.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": req.role.value,
        "login_id": login_id,
    }


class LoginRequest(BaseModel):
    login_id: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    user = await users_collection.find_one({"login_id": req.login_id})
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401, detail="Invalid Login ID or password")

    token = create_access_token(user_id=user["login_id"], role=user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "login_id": user["login_id"],
    }
