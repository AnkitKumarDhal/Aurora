from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from database import close_databse


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_databse()

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
