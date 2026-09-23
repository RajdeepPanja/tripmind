"""
LangGraph node functions for the TripMind planning workflow. Each node
reads what it needs from TripState and returns a partial dict of updates
— LangGraph merges these into the running state. Nodes never mutate
`state` in place, and never perform deterministic math inline — they call
the existing services in services/ and just shuttle results into state.
"""
from __future__ import annotations

from agents.errors import AgentError
from agents.flight_agent import run_flight_agent
from agents.hotel_agent import run_hotel_agent
from agents.itinerary_agent import ItineraryGenerationError, run_itinerary_agent
from agents.places_agent import run_places_agent
from agents.verification_agent import run_verification
from graph.state import TripState
from models.enums import WorkflowStatus
from models.search import FlightSearchRequest, HotelSearchRequest, PlacesSearchRequest
from services.airport_lookup import UnknownAirportCityError, resolve_airport_code
from services.budget_calculator import calculate_budget
from services.cost_estimator import (
    estimate_activities_cost,
    estimate_food_cost,
    estimate_transport_cost,
)
from services.route_builder import build_route_plan
from services.trip_optimizer import select_budget_aware_combo


def validate_request(state: TripState) -> dict:
    request = state["request"]
    errors: list[str] = []

    if request.travelers < 1:
        errors.append("travelers must be at least 1")
    if request.duration_days < 1:
        errors.append("trip must be at least 1 day")
    if request.budget.total.amount <= 0:
        errors.append("budget must be greater than 0")

    return {"errors": errors, "status": WorkflowStatus.SEARCHING}


async def search_flights_node(state: TripState, client=None) -> dict:
    request = state["request"]

    try:
        origin_code = resolve_airport_code(request.origin)
        destination_code = resolve_airport_code(request.destination)
    except UnknownAirportCityError as exc:
        return {"flights": [], "errors": [f"Flight search skipped: {exc}"]}

    search_request = FlightSearchRequest(
        origin=origin_code,
        destination=destination_code,
        departure_date=request.start_date,
        return_date=request.end_date,
        travelers=request.travelers,
        currency=request.budget.total.currency,
    )
    try:
        result = await run_flight_agent(search_request, client=client)
        return {"flights": result.results}
    except AgentError as exc:
        return {"flights": [], "errors": [f"Flight search failed: {exc}"]}


async def search_hotels_node(state: TripState, client=None) -> dict:
    request = state["request"]
    search_request = HotelSearchRequest(
        destination=request.destination,
        check_in_date=request.start_date,
        check_out_date=request.end_date,
        travelers=request.travelers,
        currency=request.budget.total.currency,
    )
    try:
        result = await run_hotel_agent(search_request, client=client)
        return {"hotels": result.results}
    except AgentError as exc:
        return {"hotels": [], "errors": [f"Hotel search failed: {exc}"]}


async def search_places_node(state: TripState, client=None) -> dict:
    request = state["request"]
    search_request = PlacesSearchRequest(destination=request.destination)
    try:
        result = await run_places_agent(search_request, client=client)
        return {"places": result.results}
    except AgentError as exc:
        return {"places": [], "errors": [f"Places search failed: {exc}"]}


def select_options(state: TripState) -> dict:
    """
    Fan-in point: runs once all three parallel search branches have
    completed. Jointly selects a flight+hotel combination that fits the
    budget left after buffer + estimated food/activities/transport
    (services/trip_optimizer.py), using the places already searched in
    the parallel fan-out so the reservation reflects real attraction
    pricing where available.
    """
    constraints = state["constraints"]
    request = state["request"]
    flights = state.get("flights") or []
    hotels = state.get("hotels") or []
    places = state.get("places") or []

    if not flights and not hotels:
        return {
            "errors": ["No flights or hotels found — cannot plan trip"],
            "status": WorkflowStatus.FAILED,
        }

    selected_flight, selected_hotel, reasons, budget_feasible = select_budget_aware_combo(
    flights, hotels, constraints, request, places
)

    return {
        "selected_flight": selected_flight,
        "selected_hotel": selected_hotel,
        "selection_reasons": reasons,
        "budget_feasible": budget_feasible,
        "status": WorkflowStatus.PLANNING,
    }


def calculate_budget_node(state: TripState) -> dict:
    """
    Uses the same food/activities/transport estimates the optimizer used
    during selection, so the final displayed budget breakdown never
    drifts from what selection actually reserved room for.
    """
    request = state["request"]
    constraints = state["constraints"]
    places = state.get("places") or []
    selected_flight = state.get("selected_flight")
    selected_hotel = state.get("selected_hotel")

    travelers = request.travelers
    duration_days = request.duration_days

    food_total = estimate_food_cost(travelers, duration_days, constraints.hotel_tier)
    activities_total = estimate_activities_cost(
        places, travelers, duration_days, constraints.max_daily_activities
    )
    transport_total = estimate_transport_cost(travelers, duration_days)

    denom = travelers * duration_days
    food_per_person_per_day = round(food_total / denom, 2) if denom else 0.0
    activities_per_person_per_day = round(activities_total / denom, 2) if denom else 0.0

    breakdown = calculate_budget(
        trip_request=request,
        selected_flights=[selected_flight] if selected_flight else [],
        selected_hotels=[selected_hotel] if selected_hotel else [],
        estimated_food_per_person_per_day=food_per_person_per_day,
        estimated_activities_per_person_per_day=activities_per_person_per_day,
        estimated_transport_total=transport_total,
    )
    return {"budget": breakdown}


def build_route_node(state: TripState) -> dict:
    places = state.get("places") or []
    hotel = state.get("selected_hotel")
    constraints = state["constraints"]
    request = state["request"]

    route_plan = build_route_plan(
        places=places,
        hotel=hotel,
        duration_days=request.duration_days,
        constraints=constraints,
    )
    return {"route_plan": route_plan}


async def generate_itinerary_node(state: TripState, llm=None) -> dict:
    try:
        itinerary = await run_itinerary_agent(
            route_plan=state["route_plan"],
            budget=state["budget"],
            places=state.get("places") or [],
            hotel=state.get("selected_hotel"),
            constraints=state["constraints"],
            trip_request=state["request"],
            revision_feedback=state.get("revision_feedback") or [],
            llm=llm,
        )
        return {"itinerary": itinerary, "status": WorkflowStatus.VERIFYING}
    except ItineraryGenerationError as exc:
        return {
            "errors": [f"Itinerary generation failed: {exc}"],
            "status": WorkflowStatus.FAILED,
        }


def verify_itinerary_node(state: TripState) -> dict:
    verification = run_verification(
        itinerary=state["itinerary"],
        constraints=state["constraints"],
        breakdown=state["budget"],
        places=state.get("places") or [],
        hotels=state.get("hotels") or [],
        flights=state.get("flights") or [],
    )
    return {"verification": verification}


def prepare_revision_node(state: TripState) -> dict:
    verification = state["verification"]
    feedback = [
        issue.message
        for issue in (verification.violations + verification.unsupported_claims)
    ]
    return {
        "revision_feedback": feedback,
        "revision_count": state.get("revision_count", 0) + 1,
        "status": WorkflowStatus.REVISING,
    }


def finalize_node(state: TripState) -> dict:
    return {"status": WorkflowStatus.COMPLETED}


def finalize_with_warnings_node(state: TripState) -> dict:
    return {"status": WorkflowStatus.COMPLETED_WITH_WARNINGS}


def fail_gracefully_node(state: TripState) -> dict:
    return {"status": WorkflowStatus.FAILED}