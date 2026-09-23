from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from api.main import app
from models.search import FlightSearchResult, HotelSearchResult, PlacesSearchResult

client = TestClient(app)


def test_search_flights_endpoint_success(monkeypatch):
    mock_result = FlightSearchResult(results=[], skipped_count=0, query_used="CCU->JAI")
    monkeypatch.setattr("api.routes.search.run_flight_agent", AsyncMock(return_value=mock_result))
    response = client.post(
        "/api/search/flights",
        json={"origin": "CCU", "destination": "JAI", "departure_date": "2026-12-01", "travelers": 2},
    )
    assert response.status_code == 200
    assert response.json()["query_used"] == "CCU->JAI"


def test_search_flights_endpoint_invalid_dates():
    response = client.post(
        "/api/search/flights",
        json={
            "origin": "CCU",
            "destination": "JAI",
            "departure_date": "2026-12-01",
            "return_date": "2026-11-01",
            "travelers": 2,
        },
    )
    assert response.status_code == 422


def test_search_hotels_endpoint_success(monkeypatch):
    mock_result = HotelSearchResult(results=[], skipped_count=0, query_used="Jaipur")
    monkeypatch.setattr("api.routes.search.run_hotel_agent", AsyncMock(return_value=mock_result))
    response = client.post(
        "/api/search/hotels",
        json={
            "destination": "Jaipur",
            "check_in_date": "2026-12-01",
            "check_out_date": "2026-12-06",
            "travelers": 2,
        },
    )
    assert response.status_code == 200


def test_search_places_endpoint_success(monkeypatch):
    mock_result = PlacesSearchResult(results=[], skipped_count=0, queries_used=["attractions"])
    monkeypatch.setattr("api.routes.search.run_places_agent", AsyncMock(return_value=mock_result))
    response = client.post("/api/search/places", json={"destination": "Jaipur", "categories": ["attractions"]})
    assert response.status_code == 200


def test_search_flights_endpoint_agent_error(monkeypatch):
    from agents.errors import AgentError

    async def raise_error(*args, **kwargs):
        raise AgentError("upstream down")

    monkeypatch.setattr("api.routes.search.run_flight_agent", raise_error)
    response = client.post(
        "/api/search/flights",
        json={"origin": "CCU", "destination": "JAI", "departure_date": "2026-12-01", "travelers": 2},
    )
    assert response.status_code == 502