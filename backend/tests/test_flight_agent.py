from datetime import date

import pytest

from agents.errors import AgentError
from agents.flight_agent import run_flight_agent
from models.search import FlightSearchRequest
from serpapi.client import SerpApiError
from tests.fakes import FakeSerpApiClient


def make_request():
    return FlightSearchRequest(
        origin="CCU", destination="JAI", departure_date=date(2026, 12, 1), travelers=2
    )


VALID_RAW = {
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


@pytest.mark.asyncio
async def test_run_flight_agent_success():
    client = FakeSerpApiClient(response=VALID_RAW)
    result = await run_flight_agent(make_request(), client=client)
    assert len(result.results) == 1
    assert result.skipped_count == 0
    assert client.last_params["departure_id"] == "CCU"


@pytest.mark.asyncio
async def test_run_flight_agent_empty_results():
    client = FakeSerpApiClient(response={})
    result = await run_flight_agent(make_request(), client=client)
    assert result.results == []


@pytest.mark.asyncio
async def test_run_flight_agent_raises_agent_error_on_serpapi_failure():
    client = FakeSerpApiClient(error=SerpApiError("upstream failure"))
    with pytest.raises(AgentError):
        await run_flight_agent(make_request(), client=client)