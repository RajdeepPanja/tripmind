"""
Offline tests for POST /api/trips. Mocks run_trip_planning() entirely —
no real SerpApi/Groq calls are ever made here.
backend/scripts/smoke_test_trip.py remains the manual real-world check.
"""
from datetime import date
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from api.main import app
from models.budget import BudgetBreakdown
from models.common import GeoPoint, SourceRef
from models.enums import DataSource, WorkflowStatus
from models.flight import FlightOption
from models.hotel import HotelOption
from models.itinerary import DailyActivity, DayPlan, Itinerary
from models.route import RouteDay, RoutePlan, RouteStop
from models.verification import VerificationResult

client = TestClient(app)


def make_valid_request_body():
    return {
        "origin": "Kolkata",
        "destination": "Jaipur",
        "start_date": "2026-12-10",
        "end_date": "2026-12-14",
        "travelers": 2,
        "budget": {"total": {"amount": 60000.0, "currency": "INR"}},
        "profile": {
            "interests": ["history", "food"],
            "travel_style": "balanced",
            "hotel_preference": "midrange",
        },
    }


def make_completed_final_state():
    flight = FlightOption(
        id="fl1",
        airline="IndiGo",
        origin_airport="CCU",
        destination_airport="JAI",
        departure_time="2026-12-10T23:15:00",
        arrival_time="2026-12-11T01:15:00",
        duration_minutes=120,
        stops=0,
        price={"amount": 8000, "currency": "INR"},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_FLIGHTS),
    )
    hotel = HotelOption(
        id="ho1",
        name="Hotel Rajasthan",
        rating=4.5,
        price_per_night={"amount": 3000, "currency": "INR"},
        total_price={"amount": 12000, "currency": "INR"},
        nights=4,
        location=GeoPoint(latitude=26.9, longitude=75.8),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_HOTELS),
    )
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 10),
                activities=[
                    DailyActivity(time="09:00", place_id="p1", title="City Palace", duration_minutes=60)
                ],
                hotel_id="ho1",
            )
        ],
        generated_reasoning="Test reasoning.",
    )
    budget = BudgetBreakdown(
        total_budget={"amount": 60000, "currency": "INR"},
        line_items=[],
        spent={"amount": 20000, "currency": "INR"},
        remaining={"amount": 40000, "currency": "INR"},
    )
    route_plan = RoutePlan(
        days=[
            RouteDay(
                day_number=1,
                stops=[RouteStop(place_id="p1", order=0, location=GeoPoint(latitude=26.9, longitude=75.8))],
                total_distance_km=1.0,
                total_travel_minutes=10,
            )
        ],
        total_distance_km=1.0,
    )
    verification = VerificationResult(passed=True, violations=[], unsupported_claims=[])

    return {
        "status": WorkflowStatus.COMPLETED,
        "flights": [flight],
        "hotels": [hotel],
        "places": [],
        "selected_flight": flight,
        "selected_hotel": hotel,
        "selection_reasons": {"flight": "Lowest price", "hotel": "Best rating"},
        "budget": budget,
        "route_plan": route_plan,
        "itinerary": itinerary,
        "verification": verification,
        "revision_count": 0,
        "errors": [],
    }


def test_create_trip_success(monkeypatch):
    monkeypatch.setattr(
        "api.routes.trips.run_trip_planning",
        AsyncMock(return_value=make_completed_final_state()),
    )
    response = client.post("/api/trips", json=make_valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["selected_flight_id"] == "fl1"
    assert body["selected_flight"]["airline"] == "IndiGo"
    assert body["selected_hotel"]["name"] == "Hotel Rajasthan"
    assert body["selected_hotel_id"] == "ho1"
    assert body["itinerary"]["days"][0]["activities"][0]["title"] == "City Palace"
    assert body["sources"]["flights_considered"] == 1
    assert body["sources"]["hotels_considered"] == 1
    assert body["revision_count"] == 0
    assert body["errors"] == []
    assert "trip_id" in body


def test_create_trip_invalid_request_returns_422():
    bad_body = make_valid_request_body()
    bad_body["end_date"] = "2026-12-01"  # before start_date
    response = client.post("/api/trips", json=bad_body)
    assert response.status_code == 422


def test_create_trip_missing_required_field_returns_422():
    bad_body = make_valid_request_body()
    del bad_body["origin"]
    response = client.post("/api/trips", json=bad_body)
    assert response.status_code == 422


def test_create_trip_planning_failure_returns_200_with_failed_status(monkeypatch):
    """
    A clean planning failure (e.g. no flights or hotels found) is valid
    domain data, not an HTTP-level error — the client reads `status` and
    `errors` from a normal 200 response. See the design note in
    api/routes/trips.py if this should instead be a non-200 status.
    """
    failed_state = {
        "status": WorkflowStatus.FAILED,
        "flights": [],
        "hotels": [],
        "places": [],
        "selected_flight": None,
        "selected_hotel": None,
        "selection_reasons": {},
        "budget": None,
        "route_plan": None,
        "itinerary": None,
        "verification": None,
        "revision_count": 0,
        "errors": ["No flights or hotels found — cannot plan trip"],
    }
    monkeypatch.setattr(
        "api.routes.trips.run_trip_planning",
        AsyncMock(return_value=failed_state),
    )
    response = client.post("/api/trips", json=make_valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["itinerary"] is None
    assert "No flights or hotels found" in body["errors"][0]


def test_create_trip_unexpected_exception_returns_500_without_leaking_details(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("SECRET_LEAK_TOKEN_should_never_appear_in_response")

    monkeypatch.setattr("api.routes.trips.run_trip_planning", boom)
    response = client.post("/api/trips", json=make_valid_request_body())

    assert response.status_code == 500
    assert "SECRET_LEAK_TOKEN_should_never_appear_in_response" not in response.text
    assert "internal error" in response.json()["detail"].lower()


def test_create_trip_response_never_contains_configured_secrets(monkeypatch):
    from core.config import settings

    monkeypatch.setattr(
        "api.routes.trips.run_trip_planning",
        AsyncMock(return_value=make_completed_final_state()),
    )
    response = client.post("/api/trips", json=make_valid_request_body())

    text = response.text
    if settings.groq_api_key:
        assert settings.groq_api_key not in text
    if settings.serpapi_key:
        assert settings.serpapi_key not in text
    assert "groq_api_key" not in text
    assert "serpapi_key" not in text