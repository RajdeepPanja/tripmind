"""
Standalone search endpoints for testing the Flight/Hotel/Places agents
directly, independent of LangGraph orchestration (added in a later phase).
"""
from fastapi import APIRouter, HTTPException

from agents.errors import AgentError
from agents.flight_agent import run_flight_agent
from agents.hotel_agent import run_hotel_agent
from agents.places_agent import run_places_agent
from models.search import (
    FlightSearchRequest,
    FlightSearchResult,
    HotelSearchRequest,
    HotelSearchResult,
    PlacesSearchRequest,
    PlacesSearchResult,
)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/flights", response_model=FlightSearchResult)
async def search_flights(request: FlightSearchRequest) -> FlightSearchResult:
    try:
        return await run_flight_agent(request)
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/hotels", response_model=HotelSearchResult)
async def search_hotels(request: HotelSearchRequest) -> HotelSearchResult:
    try:
        return await run_hotel_agent(request)
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/places", response_model=PlacesSearchResult)
async def search_places(request: PlacesSearchRequest) -> PlacesSearchResult:
    try:
        return await run_places_agent(request)
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc