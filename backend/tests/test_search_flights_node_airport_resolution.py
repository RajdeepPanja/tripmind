"""
Regression test for the city-name -> airport-code fix found by the live
smoke test. Fully offline — uses FakeSerpApiClient, no real SerpApi calls.
"""
from datetime import date

import pytest

from graph.nodes import search_flights_node
from graph.state import build_initial_state
from models.budget import Budget
from models.constraints import TripConstraints
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from tests.fakes import FakeSerpApiClient

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


def make_request(origin="Kolkata", destination="Jaipur"):
    return TripRequest(
        origin=origin,
        destination=destination,
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 3),
        travelers=2,
        budget=Budget(total={"amount": 50000.0, "currency": "INR"}),
        profile=TravelerProfile(),
    )


def make_constraints():
    return TripConstraints(max_budget_amount=50000.0)


@pytest.mark.asyncio
async def test_search_flights_node_resolves_city_names_to_airport_codes():
    client = FakeSerpApiClient(response=VALID_FLIGHT_RAW)
    state = build_initial_state(make_request("Kolkata", "Jaipur"), make_constraints())

    result = await search_flights_node(state, client=client)

    assert len(result["flights"]) == 1
    # Confirms SerpApi actually received resolved IATA codes, not raw city
    # names — this is exactly what SerpApi rejected with a 400 live.
    assert client.last_params["departure_id"] == "CCU"
    assert client.last_params["arrival_id"] == "JAI"


@pytest.mark.asyncio
async def test_search_flights_node_accepts_airport_codes_directly():
    client = FakeSerpApiClient(response=VALID_FLIGHT_RAW)
    state = build_initial_state(make_request("CCU", "JAI"), make_constraints())

    result = await search_flights_node(state, client=client)

    assert len(result["flights"]) == 1
    assert client.last_params["departure_id"] == "CCU"


@pytest.mark.asyncio
async def test_search_flights_node_unknown_city_fails_gracefully_without_calling_serpapi():
    client = FakeSerpApiClient(response=VALID_FLIGHT_RAW)
    state = build_initial_state(make_request("Atlantis", "Jaipur"), make_constraints())

    result = await search_flights_node(state, client=client)

    assert result["flights"] == []
    assert any("Flight search skipped" in e for e in result["errors"])
    # No SerpApi call should have been made for an unresolvable city.
    assert client.last_params is None