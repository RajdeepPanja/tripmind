"""
Basic health/readiness endpoint.

This does NOT call SerpApi or Groq — it only checks that required
credentials are present, so the demo can fail fast with a clear message
instead of a confusing error mid-planning.
"""
from fastapi import APIRouter, Depends

from core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "environment": settings.environment,
        "serpapi_key_configured": bool(settings.serpapi_key),
        "groq_key_configured": bool(settings.groq_api_key),
    }