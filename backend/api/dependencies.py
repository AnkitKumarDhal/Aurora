from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.services.clinical_session import ClinicalSessionService


def get_clinical_session_service() -> ClinicalSessionService:
    repository = ClinicalSessionRepository()
    return ClinicalSessionService(repository)
