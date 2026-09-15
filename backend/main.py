from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api.routes.consent import router as consent_router
from backend.api.routes.conversation import router as conversation_router
from backend.api.routes.documents import router as documents_router
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.verification import router as verification_router
from backend.config import settings
from backend.database import close_database, initialize_database
from backend.database.connection import initialize_database_connection


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database_connection()
    await initialize_database()
    yield
    await close_database()


app = FastAPI(
    title="Aurora Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(sessions_router, prefix="/api/v1")
app.include_router(verification_router, prefix="/api/v1")
app.include_router(consent_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Aurora Backend",
        "environment": settings.environment,
    }
