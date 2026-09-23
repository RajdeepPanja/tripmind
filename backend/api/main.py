"""
FastAPI application entrypoint.

Run from inside `backend/` with:
    uvicorn api.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health_router, search_router, trips_router
from core.config import settings

app = FastAPI(
    title="TripMind API",
    description="AI travel operating system — planning, optimization, and disruption recovery.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(search_router)
app.include_router(trips_router)


@app.get("/")
def root() -> dict:
    return {"service": "tripmind-api", "status": "running"}