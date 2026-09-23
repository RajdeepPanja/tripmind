"""
Tests for deterministic scoring/ranking services.
"""
from models.common import SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource, HotelTier
from models.flight import FlightOption
from models.hotel import HotelOption
from models.place import Place
from services.scoring import (
    rank_flights,
    rank_hotels,
    rank_places,
    score_flight,
    score_hotel,
    score_place_against_interests,
)
from datetime import datetime


def make_constraints(**overrides):
    defaults = dict(max_budget_amount=50000.0, hotel_tier=HotelTier.MIDRANGE)
    defaults.update(overrides)
    return TripConstraints(**defaults)


def make_flight(price, stops=0, duration=120):
    return FlightOption(
        id=f"fl-{price}-{stops}",
        airline="Test Air",
        origin_airport="CCU",
        destination_airport="JAI",
        departure_time=datetime(2026, 12, 1, 6, 0),
        arrival_time=datetime(2026, 12, 1, 6, 0 + duration // 60 or 1),
        duration_minutes=duration,
        stops=stops,
        price={"amount": price, "currency": "INR"},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_FLIGHTS),
    )


def make_hotel(price_per_night, rating):
    return HotelOption(
        id=f"ho-{price_per_night}-{rating}",
        name="Test Hotel",
        rating=rating,
        price_per_night={"amount": price_per_night, "currency": "INR"},
        total_price={"amount": price_per_night, "currency": "INR"},
        nights=1,
        location={"latitude": 26.9124, "longitude": 75.7873},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_HOTELS),
    )


def make_place(name, category="attraction", rating=4.0):
    return Place(
        id=f"pl-{name}",
        name=name,
        category=category,
        rating=rating,
        location={"latitude": 26.9124, "longitude": 75.7873},
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS),
    )


def test_score_flight_cheaper_scores_higher():
    constraints = make_constraints()
    cheap = make_flight(price=5000)
    expensive = make_flight(price=20000)
    assert score_flight(cheap, constraints) > score_flight(expensive, constraints)


def test_score_flight_fewer_stops_scores_higher():
    constraints = make_constraints()
    direct = make_flight(price=8000, stops=0)
    one_stop = make_flight(price=8000, stops=1)
    assert score_flight(direct, constraints) > score_flight(one_stop, constraints)


def test_rank_flights_orders_best_first():
    constraints = make_constraints()
    flights = [make_flight(20000, stops=2), make_flight(5000, stops=0)]
    ranked = rank_flights(flights, constraints)
    assert ranked[0].price.amount == 5000


def test_score_hotel_higher_rating_scores_higher_at_same_price():
    constraints = make_constraints(hotel_tier=HotelTier.MIDRANGE)
    good = make_hotel(price_per_night=6000, rating=4.8)
    bad = make_hotel(price_per_night=6000, rating=2.5)
    assert score_hotel(good, constraints) > score_hotel(bad, constraints)


def test_rank_hotels_orders_best_first():
    constraints = make_constraints(hotel_tier=HotelTier.MIDRANGE)
    hotels = [make_hotel(6000, 2.0), make_hotel(6000, 4.9)]
    ranked = rank_hotels(hotels, constraints)
    assert ranked[0].rating == 4.9


def test_score_place_matches_interest_tag():
    constraints = make_constraints()
    constraints.priority_weights = {"history": 0.5}
    history_place = make_place("Amber Fort History Museum", rating=4.0)
    random_place = make_place("Generic Shop", rating=4.0)
    assert score_place_against_interests(
        history_place, constraints
    ) > score_place_against_interests(random_place, constraints)


def test_rank_places_orders_best_first():
    constraints = make_constraints()
    constraints.priority_weights = {"food": 0.5}
    places = [make_place("Random Spot"), make_place("Best Food Market")]
    ranked = rank_places(places, constraints)
    assert ranked[0].name == "Best Food Market"