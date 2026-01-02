from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import (
    auth_router,
    agencies_router,
    cases_router,
    evidence_router,
    analysis_router,
    reports_router,
    bootstrap_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ID SHIELD™",
    description="Global3 Technology & Intelligence - Forensic Intelligence Platform",
    version="1.0.0-MVP",
    lifespan=lifespan
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router)
app.include_router(agencies_router)
app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(bootstrap_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "name": "ID SHIELD™",
        "version": "1.0.0-MVP",
        "description": "Global3 Technology & Intelligence - Forensic Intelligence Platform",
        "status": "operational"
    }
