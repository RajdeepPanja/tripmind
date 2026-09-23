"""
Main trip-planning endpoint — a thin HTTP wrapper around the existing
LangGraph workflow (run_trip_planning). No new planning logic lives here.
"""
import logging
import uuid

from fastapi import APIRouter, HTTPException

from graph.workflow import run_trip_planning
from models.enums import WorkflowStatus
from models.trip_request import TripRequest
from models.trip_response import SourceCounts, TripPlanResponse
from services.constraints_builder import build_default_constraints

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("", response_model=TripPlanResponse)
async def create_trip(request: TripRequest) -> TripPlanResponse:
    constraints = build_default_constraints(request)

    try:
        final_state = await run_trip_planning(request, constraints, max_revisions=2)
    except Exception as exc:
        logger.exception("Trip planning failed with an unhandled exception")
        raise HTTPException(
            status_code=500,
            detail="Trip planning failed due to an internal error.",
        ) from exc

    selected_flight = final_state.get("selected_flight")
    selected_hotel = final_state.get("selected_hotel")

    return TripPlanResponse(
            trip_id=str(uuid.uuid4()),
            status=final_state.get("status", WorkflowStatus.FAILED),
            itinerary=final_state.get("itinerary"),
            budget=final_state.get("budget"),
            route_plan=final_state.get("route_plan"),
            verification=final_state.get("verification"),
            selected_flight=selected_flight,
            selected_hotel=selected_hotel,
            selected_flight_id=selected_flight.id if selected_flight else None,
            selected_hotel_id=selected_hotel.id if selected_hotel else None,
            selection_reasons=final_state.get("selection_reasons") or {},
            budget_feasible=final_state.get("budget_feasible", True),
            revision_count=final_state.get("revision_count", 0),
            errors=final_state.get("errors") or [],
            sources=SourceCounts(
               flights_considered=len(final_state.get("flights") or []),
                hotels_considered=len(final_state.get("hotels") or []),
               places_considered=len(final_state.get("places") or []),
            ),
    )