from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, sessions, documents, doctor

app = FastAPI(title="Aurora API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(doctor.router, prefix="/doctor", tags=["doctor"])


@app.get("/health")
def health():
    return {"status": "ok"}
