from datetime import date

import pytest

from agents.errors import AgentError
from agents.hotel_agent import run_hotel_agent
from models.search import HotelSearchRequest
from serpapi.client import SerpApiError
from tests.fakes import FakeSerpApiClient


def make_request():
    return HotelSearchRequest(
        destination="Jaipur",
        check_in_date=date(2026, 12, 1),
        check_out_date=date(2026, 12, 6),
        travelers=2,
    )


VALID_RAW = {
    "properties": [
        {
            "name": "Hotel Rajasthan",
            "gps_coordinates": {"latitude": 26.9124, "longitude": 75.7873},
            "rate_per_night": {"extracted_lowest": 3000},
        }
    ]
}


@pytest.mark.asyncio
async def test_run_hotel_agent_success():
    client = FakeSerpApiClient(response=VALID_RAW)
    result = await run_hotel_agent(make_request(), client=client)
    assert len(result.results) == 1
    assert result.results[0].nights == 5


@pytest.mark.asyncio
async def test_run_hotel_agent_raises_on_failure():
    client = FakeSerpApiClient(error=SerpApiError("boom"))
    with pytest.raises(AgentError):
        await run_hotel_agent(make_request(), client=client)