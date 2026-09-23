import pytest

from agents.errors import AgentError
from agents.places_agent import run_places_agent
from models.search import PlacesSearchRequest
from serpapi.client import SerpApiError
from tests.fakes import FakeSerpApiClient

VALID_RAW = {
    "local_results": [
        {"title": "Amber Fort", "gps_coordinates": {"latitude": 26.98, "longitude": 75.85}}
    ]
}


@pytest.mark.asyncio
async def test_run_places_agent_success():
    client = FakeSerpApiClient(response=VALID_RAW)
    request = PlacesSearchRequest(destination="Jaipur", categories=["attractions"])
    result = await run_places_agent(request, client=client)
    assert len(result.results) == 1
    assert result.queries_used == ["attractions"]


@pytest.mark.asyncio
async def test_run_places_agent_multiple_categories():
    client = FakeSerpApiClient(response=VALID_RAW)
    request = PlacesSearchRequest(destination="Jaipur", categories=["attractions", "restaurants"])
    result = await run_places_agent(request, client=client)
    assert len(result.results) == 2
    assert result.queries_used == ["attractions", "restaurants"]


@pytest.mark.asyncio
async def test_run_places_agent_raises_on_failure():
    client = FakeSerpApiClient(error=SerpApiError("boom"))
    request = PlacesSearchRequest(destination="Jaipur")
    with pytest.raises(AgentError):
        await run_places_agent(request, client=client)