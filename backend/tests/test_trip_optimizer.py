"""
Tests for budget-aware joint flight+hotel selection.

test_joint_selection_avoids_independently_best_but_over_budget_combo
proves this is genuine joint optimization, not just re-ranking.

test_reserves_room_for_food_and_transport_not_just_buffer is the
regression test for the fix flagged after the first live run: selection
must reserve room for estimated food/activities/transport, not just
the buffer — a combo that fit under buffer-only logic must now be
correctly rejected if it doesn't leave room for the rest of the trip.
"""
from datetime import date, datetime

from models.budget import Budget
from models.common import GeoPoint, SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource, HotelTier
from models.flight import FlightOption
from models.hotel import HotelOption
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from services.trip_optimizer import select_budget_aware_combo


def make_flight(id_, price, stops, duration_minutes=120):
    return FlightOption(
        id=id_,
        airline="Test Air",
        origin_airport="CCU",
        destination_airport="JAI",
        departure_time=datetime(2026, 12, 1, 6, 0),
        arrival_time=datetime(
            2026,
            12,
            1,
            6 + duration_minutes // 60,
            duration_minutes % 60,
        ),
        duration_minutes=duration_minutes,
        stops=stops,
        price={"amount": price, "currency": "INR"},
        source_ref=SourceRef(
            source=DataSource.SERPAPI_GOOGLE_FLIGHTS
        ),
    )


def make_hotel(id_, price, rating):
    return HotelOption(
        id=id_,
        name=f"Hotel {id_}",
        rating=rating,
        price_per_night={"amount": price, "currency": "INR"},
        total_price={"amount": price, "currency": "INR"},
        nights=1,
        location=GeoPoint(latitude=26.9, longitude=75.8),
        source_ref=SourceRef(
            source=DataSource.SERPAPI_GOOGLE_HOTELS
        ),
    )


def make_trip_request(budget_amount=50000.0):
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 3),
        travelers=1,
        budget=Budget(
            total={
                "amount": budget_amount,
                "currency": "INR",
            }
        ),
        profile=TravelerProfile(),
    )


def test_joint_selection_avoids_independently_best_but_over_budget_combo():
    f1 = make_flight(
        "f1",
        price=35000,
        stops=0,
        duration_minutes=120,
    )
    f2 = make_flight(
        "f2",
        price=10000,
        stops=5,
        duration_minutes=180,
    )
    h1 = make_hotel(
        "h1",
        price=20000,
        rating=5.0,
    )
    h2 = make_hotel(
        "h2",
        price=8000,
        rating=3.0,
    )

    constraints = TripConstraints(
        max_budget_amount=50000.0,
        hotel_tier=HotelTier.LUXURY,
    )
    trip_request = make_trip_request(
        budget_amount=50000.0
    )

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [f1, f2],
            [h1, h2],
            constraints,
            trip_request,
        )
    )

    assert flight.id == "f2"
    assert hotel.id == "h1"
    assert "flight" in reasons
    assert "hotel" in reasons
    assert budget_feasible is True


def test_falls_back_to_cheapest_when_nothing_fits_budget():
    f1 = make_flight(
        "f1",
        price=40000,
        stops=0,
    )
    h1 = make_hotel(
        "h1",
        price=30000,
        rating=5.0,
    )
    f2 = make_flight(
        "f2",
        price=38000,
        stops=0,
    )
    h2 = make_hotel(
        "h2",
        price=29000,
        rating=4.5,
    )

    constraints = TripConstraints(
        max_budget_amount=10000.0,
        hotel_tier=HotelTier.LUXURY,
    )
    trip_request = make_trip_request(
        budget_amount=10000.0
    )

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [f1, f2],
            [h1, h2],
            constraints,
            trip_request,
        )
    )

    assert flight.id == "f2"
    assert hotel.id == "h2"
    assert budget_feasible is False
    assert "no flight+hotel combination fits" in reasons["flight"]


def test_only_flights_present_picks_best_flight_alone():
    f1 = make_flight(
        "f1",
        price=10000,
        stops=0,
    )
    f2 = make_flight(
        "f2",
        price=8000,
        stops=2,
    )

    constraints = TripConstraints(
        max_budget_amount=50000.0
    )
    trip_request = make_trip_request()

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [f1, f2],
            [],
            constraints,
            trip_request,
        )
    )

    assert hotel is None
    assert flight is not None
    assert "hotel" not in reasons
    assert budget_feasible is False


def test_only_hotels_present_picks_best_hotel_alone():
    h1 = make_hotel(
        "h1",
        price=5000,
        rating=4.0,
    )

    constraints = TripConstraints(
        max_budget_amount=50000.0
    )
    trip_request = make_trip_request()

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [],
            [h1],
            constraints,
            trip_request,
        )
    )

    assert flight is None
    assert hotel is not None
    assert "flight" not in reasons
    assert budget_feasible is False


def test_no_flights_or_hotels_returns_none():
    constraints = TripConstraints(
        max_budget_amount=50000.0
    )
    trip_request = make_trip_request()

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [],
            [],
            constraints,
            trip_request,
        )
    )

    assert flight is None
    assert hotel is None
    assert reasons == {}
    assert budget_feasible is False


def test_reserves_room_for_food_and_transport_not_just_buffer():
    """
    f1+h1 = 45000, which fit exactly under the OLD buffer-only threshold
    (50000 - 10% buffer = 45000). Under the new threshold, which also
    reserves for food (LUXURY: 3000/day * 1 traveler * 2 days = 6000)
    and transport (300/day * 1 * 2 = 600), available =
    50000-5000-6000-600 = 38400 — so f1+h1 (45000) must now be
    correctly rejected in favor of f1+h2 (35000), even though h1
    scores higher alone (rating 4.8 vs 4.0).
    """
    f1 = make_flight(
        "f1",
        price=20000,
        stops=0,
    )
    h1 = make_hotel(
        "h1",
        price=25000,
        rating=4.8,
    )
    h2 = make_hotel(
        "h2",
        price=15000,
        rating=4.0,
    )

    constraints = TripConstraints(
        max_budget_amount=50000.0,
        hotel_tier=HotelTier.LUXURY,
    )
    trip_request = make_trip_request(
        budget_amount=50000.0
    )

    flight, hotel, reasons, budget_feasible = (
        select_budget_aware_combo(
            [f1],
            [h1, h2],
            constraints,
            trip_request,
        )
    )

    assert hotel.id == "h2"
    assert flight.price.amount + hotel.total_price.amount <= 38400
    assert budget_feasible is True