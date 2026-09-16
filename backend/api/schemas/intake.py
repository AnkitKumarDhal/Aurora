from datetime import datetime
from pydantic import BaseModel
from backend.domain.enums import SessionStatus


class IntakeFinalizeResponse(BaseModel):
    session_id: str
    status: SessionStatus
    updated_at: datetime
