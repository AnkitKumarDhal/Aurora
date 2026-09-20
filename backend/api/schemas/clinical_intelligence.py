from typing import Any

from pydantic import BaseModel


class ClinicalIntelligenceResponse(BaseModel):
    session_id: str
    session_status: str
    summary: dict[str, Any] | None
    documents: list[dict[str, Any]]
    intelligence: dict[str, Any]
