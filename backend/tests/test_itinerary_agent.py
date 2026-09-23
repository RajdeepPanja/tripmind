from datetime import date

import pytest

from agents.itinerary_agent import (
    ItineraryGenerationError,
    LLMActivityItem,
    LLMDayPlan,
    LLMItineraryOutput,
    run_itinerary_agent,
)
from models.budget import Budget, BudgetBreakdown
from models.common import GeoPoint, SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource, PlaceCategory
from models.place import Place
from models.route import RouteDay, RoutePlan, RouteStop
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from tests.fakes import FakeItineraryLLM


def make_place(id_, name="Amber Fort"):
    return Place(
        id=id_,
        name=name,
        category=PlaceCategory.ATTRACTION,
        location=GeoPoint(latitude=26.98, longitude=75.85),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS),
        typical_visit_minutes=90,
    )


def make_route_plan(place_id):
    return RoutePlan(
        days=[
            RouteDay(
                day_number=1,
                stops=[
                    RouteStop(
                        place_id=place_id,
                        order=0,
                        location=GeoPoint(latitude=26.98, longitude=75.85),
                        distance_from_previous_km=2.0,
                        travel_minutes_from_previous=10,
                    )
                ],
                total_distance_km=2.0,
                total_travel_minutes=10,
            )
        ],
        total_distance_km=2.0,
    )


def make_trip_request():
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 2),
        travelers=2,
        budget=Budget(total={"amount": 50000, "currency": "INR"}),
        profile=TravelerProfile(),
    )


def make_constraints():
    return TripConstraints(max_budget_amount=50000)


def make_budget():
    return BudgetBreakdown(
        total_budget={"amount": 50000, "currency": "INR"},
        line_items=[],
        spent={"amount": 10000, "currency": "INR"},
        remaining={"amount": 40000, "currency": "INR"},
    )


@pytest.mark.asyncio
async def test_run_itinerary_agent_success():
    place = make_place("p1")
    route_plan = make_route_plan("p1")
    fake_llm = FakeItineraryLLM()

    itinerary = await run_itinerary_agent(
        route_plan=route_plan,
        budget=make_budget(),
        places=[place],
        hotel=None,
        constraints=make_constraints(),
        trip_request=make_trip_request(),
        llm=fake_llm,
    )

    assert len(itinerary.days) == 1
    assert itinerary.days[0].activities[0].place_id == "p1"
    assert itinerary.days[0].activities[0].duration_minutes == 90  # from place.typical_visit_minutes


@pytest.mark.asyncio
async def test_run_itinerary_agent_rejects_unknown_place_id():
    place = make_place("p1")
    route_plan = make_route_plan("p1")
    fake_llm = FakeItineraryLLM(
        bad_response=None
    )
    # Override with a hand-built response referencing an ID not in `places`.
    fake_llm._bad_response = None

    class BadIdLLM:
        async def ainvoke(self, messages):
            return LLMItineraryOutput(
                days=[LLMDayPlan(day_number=1, activities=[
                    LLMActivityItem(time="09:00", place_id="unknown-id", title="Mystery")
                ])],
                reasoning="...",
            )

    with pytest.raises(ItineraryGenerationError):
        await run_itinerary_agent(
            route_plan=route_plan,
            budget=make_budget(),
            places=[place],
            hotel=None,
            constraints=make_constraints(),
            trip_request=make_trip_request(),
            llm=BadIdLLM(),
        )


@pytest.mark.asyncio
async def test_run_itinerary_agent_malformed_output_raises():
    place = make_place("p1")
    route_plan = make_route_plan("p1")
    fake_llm = FakeItineraryLLM(bad_response={"not": "the right shape"})

    with pytest.raises(ItineraryGenerationError):
        await run_itinerary_agent(
            route_plan=route_plan,
            budget=make_budget(),
            places=[place],
            hotel=None,
            constraints=make_constraints(),
            trip_request=make_trip_request(),
            llm=fake_llm,
        )


@pytest.mark.asyncio
async def test_run_itinerary_agent_llm_call_failure_raises():
    place = make_place("p1")
    route_plan = make_route_plan("p1")
    fake_llm = FakeItineraryLLM(raise_error=RuntimeError("groq down"))

    with pytest.raises(ItineraryGenerationError):
        await run_itinerary_agent(
            route_plan=route_plan,
            budget=make_budget(),
            places=[place],
            hotel=None,
            constraints=make_constraints(),
            trip_request=make_trip_request(),
            llm=fake_llm,
        )