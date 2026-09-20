from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes.assignment import router as assignment_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.admin_dashboard import router as admin_dashboard_router
from backend.api.routes.clinical_intelligence import router as clinical_intelligence_router
from backend.api.routes.clinical_summary import router as clinical_summary_router
from backend.api.routes.consent import router as consent_router
from backend.api.routes.consent_information import router as consent_information_router
from backend.api.routes.conversation import router as conversation_router
from backend.api.routes.documents import router as documents_router
from backend.api.routes.doctor_case import router as doctor_case_router
from backend.api.routes.doctor_queue import router as doctor_queue_router
from backend.api.routes.intake import router as intake_router
from backend.api.routes.interview import router as interview_router
from backend.api.routes.interview_session import router as interview_session_router
from backend.api.routes.patient_registration import router as patient_registration_router
from backend.api.routes.patient_verification import router as patient_verification_router
from backend.api.routes.promotion import router as promotion_router
from backend.api.routes.queue import router as queue_router
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.triage import router as triage_router
from backend.api.routes.verification import router as verification_router
from backend.api.routes.workflow import router as workflow_router
from backend.config import settings
from backend.database import close_database, initialize_database
from backend.database.connection import initialize_database_connection


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment == "test":
        yield
        return

    await initialize_database_connection()
    await initialize_database()

    yield

    await close_database()


app = FastAPI(
    title="Aurora Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_dashboard_router, prefix="/api/v1")
app.include_router(assignment_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(verification_router, prefix="/api/v1")
app.include_router(consent_router, prefix="/api/v1")
app.include_router(consent_information_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(interview_session_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(clinical_intelligence_router, prefix="/api/v1")
app.include_router(doctor_case_router, prefix="/api/v1")
app.include_router(patient_verification_router, prefix="/api/v1")
app.include_router(patient_registration_router, prefix="/api/v1")
app.include_router(doctor_queue_router, prefix="/api/v1")
app.include_router(clinical_summary_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(triage_router, prefix="/api/v1")
app.include_router(queue_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(promotion_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Aurora Backend",
        "environment": settings.environment,
    }
