"""
Tests for deterministic budget arithmetic.
"""
import pytest

from models.budget import Budget
from models.common import SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource
from models.flight import FlightOption
from models.hotel import HotelOption
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from services.budget_calculator import (
    BudgetError,
    calculate_budget,
    is_over_budget,
)
from datetime import date, datetime


def make_trip_request(total_amount=50000.0, per_person=False, travelers=2):
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 6),
        travelers=travelers,
        budget=Budget(total={"amount": total_amount, "currency": "INR"}, per_person=per_person),
        profile=TravelerProfile(interests=["history", "food"]),
    )


def make_flight(price=8000.0):
    return FlightOption(
        id="fl1",
        airline="IndiGo",
        origin_airport="CCU",
        destination_airport="JAI",
        departure_time=datetime(2026, 12, 1, 6, 0),
        arrival_time=datetime(2026, 12, 1, 9, 0),
        duration_minutes=180,
        stops=0,
        price={"amount": price, "currency": "INR"},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_FLIGHTS),
    )


def make_hotel(price_per_night=3000.0, nights=5):
    return HotelOption(
        id="ho1",
        name="Hotel Rajasthan",
        rating=4.2,
        price_per_night={"amount": price_per_night, "currency": "INR"},
        total_price={"amount": price_per_night * nights, "currency": "INR"},
        nights=nights,
        location={"latitude": 26.9124, "longitude": 75.7873},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_HOTELS),
    )


def test_calculate_budget_basic_totals():
    trip = make_trip_request(total_amount=50000.0)
    flights = [make_flight(8000.0), make_flight(8000.0)]
    hotels = [make_hotel(3000.0, nights=5)]

    breakdown = calculate_budget(
        trip_request=trip,
        selected_flights=flights,
        selected_hotels=hotels,
        estimated_food_per_person_per_day=500.0,
        estimated_activities_per_person_per_day=300.0,
        estimated_transport_total=1000.0,
        buffer_ratio=0.10,
    )

    flights_total = 16000.0
    hotels_total = 15000.0
    food_total = 500.0 * 2 * 5
    activities_total = 300.0 * 2 * 5
    transport_total = 1000.0
    buffer = 50000.0 * 0.10

    expected_spent = round(
        flights_total + hotels_total + food_total + activities_total + transport_total + buffer,
        2,
    )

    assert breakdown.spent.amount == expected_spent
    assert breakdown.remaining.amount == round(50000.0 - expected_spent, 2)
    assert breakdown.total_budget.amount == 50000.0
    assert len(breakdown.line_items) == 6


def test_calculate_budget_per_person_multiplies_total():
    trip = make_trip_request(total_amount=25000.0, per_person=True, travelers=2)
    breakdown = calculate_budget(
        trip_request=trip,
        selected_flights=[],
        selected_hotels=[],
    )
    assert breakdown.total_budget.amount == 50000.0


def test_calculate_budget_currency_mismatch_raises():
    trip = make_trip_request()
    bad_flight = make_flight(8000.0)
    bad_flight.price.currency = "USD"

    with pytest.raises(BudgetError):
        calculate_budget(
            trip_request=trip,
            selected_flights=[bad_flight],
            selected_hotels=[],
        )


def test_is_over_budget_true_when_negative_remaining():
    trip = make_trip_request(total_amount=1000.0)
    flights = [make_flight(8000.0)]
    breakdown = calculate_budget(
        trip_request=trip,
        selected_flights=flights,
        selected_hotels=[],
    )
    assert is_over_budget(breakdown) is True


def test_is_over_budget_false_when_within_budget():
    trip = make_trip_request(total_amount=100000.0)
    flights = [make_flight(8000.0)]
    breakdown = calculate_budget(
        trip_request=trip,
        selected_flights=flights,
        selected_hotels=[],
    )
    assert is_over_budget(breakdown) is False