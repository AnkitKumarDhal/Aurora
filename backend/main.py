from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from database import close_database, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    yield
    await close_database()

app = FastAPI(
    title="Aurora",
    description="AI-assisted clinical intake platform for hospital OPDs.",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "aurora-backend"
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Aurora",
        "environment": settings.environment
    }
