"""
End-to-end tests for the LangGraph TripMind planning workflow. Fully
offline — SerpApi and Groq are replaced with fakes; no network calls.
"""
from datetime import date

import pytest

from graph.state import build_initial_state
from graph.workflow import build_graph
from models.budget import Budget
from models.constraints import TripConstraints
from models.enums import WorkflowStatus
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from serpapi.client import SerpApiError
from tests.fakes import FakeItineraryLLM, FakeSerpApiClient

VALID_FLIGHT_RAW = {
    "best_flights": [
        {
            "flights": [
                {
                    "departure_airport": {"id": "CCU", "time": "2026-12-01 06:00"},
                    "arrival_airport": {"id": "JAI", "time": "2026-12-01 09:00"},
                    "airline": "IndiGo",
                }
            ],
            "total_duration": 180,
            "price": 8000,
        }
    ]
}

VALID_HOTEL_RAW = {
    "properties": [
        {
            "name": "Hotel Rajasthan",
            "gps_coordinates": {"latitude": 26.9124, "longitude": 75.7873},
            "overall_rating": 4.2,
            "rate_per_night": {"extracted_lowest": 3000},
        }
    ]
}

VALID_PLACES_RAW = {
    "local_results": [
        {"title": "Amber Fort", "gps_coordinates": {"latitude": 26.98, "longitude": 75.85}, "rating": 4.6},
        {"title": "City Palace", "gps_coordinates": {"latitude": 26.93, "longitude": 75.82}, "rating": 4.4},
    ]
}

EMPTY_RAW = {}


def make_request():
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 3),  # 2-day trip
        travelers=2,
        budget=Budget(total={"amount": 50000.0, "currency": "INR"}),
        profile=TravelerProfile(interests=["history"]),
    )


def make_constraints(**overrides):
    defaults = dict(max_budget_amount=50000.0, max_daily_activities=5)
    defaults.update(overrides)
    return TripConstraints(**defaults)


@pytest.mark.asyncio
async def test_happy_path_completes():
    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(response=VALID_HOTEL_RAW),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=FakeItineraryLLM(),
    )
    state = build_initial_state(make_request(), make_constraints())
    final_state = await graph.ainvoke(state)

    assert final_state["status"] == WorkflowStatus.COMPLETED
    assert final_state["itinerary"] is not None
    assert final_state["verification"].passed is True
    assert final_state["selected_flight"] is not None
    assert final_state["selected_hotel"] is not None
    assert "flight" in final_state["selection_reasons"]
    assert "hotel" in final_state["selection_reasons"]
    assert final_state["revision_count"] == 0


@pytest.mark.asyncio
async def test_partial_search_zero_results_still_completes():
    """Places search returns zero results; flights/hotel succeed — trip still plans."""
    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(response=VALID_HOTEL_RAW),
        places_client=FakeSerpApiClient(response=EMPTY_RAW),
        llm=FakeItineraryLLM(),
    )
    state = build_initial_state(make_request(), make_constraints())
    final_state = await graph.ainvoke(state)

    assert final_state["status"] in (
        WorkflowStatus.COMPLETED,
        WorkflowStatus.COMPLETED_WITH_WARNINGS,
    )
    assert final_state["places"] == []


@pytest.mark.asyncio
async def test_zero_flights_and_hotels_hard_fails():
    graph = build_graph(
        flight_client=FakeSerpApiClient(response=EMPTY_RAW),
        hotel_client=FakeSerpApiClient(response=EMPTY_RAW),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=FakeItineraryLLM(),
    )
    state = build_initial_state(make_request(), make_constraints())
    final_state = await graph.ainvoke(state)

    assert final_state["status"] == WorkflowStatus.FAILED
    assert final_state["itinerary"] is None
    assert any("No flights or hotels" in e for e in final_state["errors"])


@pytest.mark.asyncio
async def test_verification_failure_triggers_revision():
    """
    First LLM response crams both places into day 1, violating
    max_daily_activities=1 — a valid but non-compliant itinerary, which is
    what should trigger a revision (as opposed to an unknown place_id,
    which the agent itself rejects before verification ever runs).
    """
    call_count = {"n": 0}

    class FlakyLLM:
        async def ainvoke(self, messages):
            import json as _json
            from agents.itinerary_agent import LLMActivityItem, LLMDayPlan, LLMItineraryOutput

            call_count["n"] += 1
            user_content = _json.loads(messages[1]["content"])
            all_places = [p for day in user_content["days"] for p in day["places"]]

            if call_count["n"] == 1:
                activities = [
                    LLMActivityItem(time=f"{9+i}:00", place_id=p["place_id"], title=p["name"])
                    for i, p in enumerate(all_places)
                ]
                return LLMItineraryOutput(
                    days=[LLMDayPlan(day_number=1, activities=activities)],
                    reasoning="Overloaded first attempt.",
                )

            days = []
            for day in user_content["days"]:
                activities = [
                    LLMActivityItem(time=f"{9+i}:00", place_id=p["place_id"], title=p["name"])
                    for i, p in enumerate(day["places"])
                ]
                days.append(LLMDayPlan(day_number=day["day_number"], activities=activities))
            return LLMItineraryOutput(days=days, reasoning="Balanced revision.")

    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(response=VALID_HOTEL_RAW),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=FlakyLLM(),
    )
    state = build_initial_state(make_request(), make_constraints(max_daily_activities=1))
    final_state = await graph.ainvoke(state)

    assert final_state["status"] == WorkflowStatus.COMPLETED
    assert final_state["revision_count"] == 1
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_max_revision_exhaustion_returns_completed_with_warnings():
    """LLM always crams everything into day 1 — verification never passes."""

    class AlwaysOverloadedLLM:
        async def ainvoke(self, messages):
            import json as _json
            from agents.itinerary_agent import LLMActivityItem, LLMDayPlan, LLMItineraryOutput

            user_content = _json.loads(messages[1]["content"])
            all_places = [p for day in user_content["days"] for p in day["places"]]
            activities = [
                LLMActivityItem(time=f"{9+i}:00", place_id=p["place_id"], title=p["name"])
                for i, p in enumerate(all_places)
            ]
            return LLMItineraryOutput(
                days=[LLMDayPlan(day_number=1, activities=activities)],
                reasoning="Always overloaded.",
            )

    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(response=VALID_HOTEL_RAW),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=AlwaysOverloadedLLM(),
    )
    state = build_initial_state(make_request(), make_constraints(max_daily_activities=1))
    final_state = await graph.ainvoke(state)

    assert final_state["status"] == WorkflowStatus.COMPLETED_WITH_WARNINGS
    assert final_state["revision_count"] == 2  # max_revisions default
    assert final_state["verification"].passed is False


@pytest.mark.asyncio
async def test_malformed_itinerary_output_hard_fails():
    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(response=VALID_HOTEL_RAW),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=FakeItineraryLLM(bad_response={"totally": "wrong shape"}),
    )
    state = build_initial_state(make_request(), make_constraints())
    final_state = await graph.ainvoke(state)

    assert final_state["status"] == WorkflowStatus.FAILED
    assert final_state["itinerary"] is None
    assert any("Itinerary generation failed" in e for e in final_state["errors"])


@pytest.mark.asyncio
async def test_parallel_search_fan_out_fan_in_preserves_all_results():
    """
    Flights, hotels, and places run concurrently. Hotel search fails with a
    real SerpApiError while flights and places succeed — confirms all
    three branches' writes land in the final state without one clobbering
    another, and that the hotel branch's error is preserved rather than
    overwritten by the other two branches' (empty) error lists.
    """
    graph = build_graph(
        flight_client=FakeSerpApiClient(response=VALID_FLIGHT_RAW),
        hotel_client=FakeSerpApiClient(error=SerpApiError("boom")),
        places_client=FakeSerpApiClient(response=VALID_PLACES_RAW),
        llm=FakeItineraryLLM(),
    )
    state = build_initial_state(make_request(), make_constraints())
    final_state = await graph.ainvoke(state)

    assert len(final_state["flights"]) == 1
    assert final_state["hotels"] == []
    assert len(final_state["places"]) >= 1
    assert final_state["selected_flight"] is not None
    assert final_state["selected_hotel"] is None
    assert any("Hotel search failed" in e for e in final_state["errors"])