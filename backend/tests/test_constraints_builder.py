"""
Unit tests for deriving default TripConstraints from a TripRequest.
"""
from datetime import date

from models.budget import Budget
from models.enums import HotelTier, TravelStyle
from models.traveler import TravelerProfile
from models.trip_request import TripRequest
from services.constraints_builder import build_default_constraints


def make_request(per_person=False, travelers=2, interests=None):
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 5),
        travelers=travelers,
        budget=Budget(total={"amount": 30000.0, "currency": "INR"}, per_person=per_person),
        profile=TravelerProfile(
            interests=interests or [],
            travel_style=TravelStyle.PACKED,
            hotel_preference=HotelTier.LUXURY,
        ),
    )


def test_build_default_constraints_basic():
    constraints = build_default_constraints(make_request())
    assert constraints.max_budget_amount == 30000.0
    assert constraints.pace == TravelStyle.PACKED
    assert constraints.hotel_tier == HotelTier.LUXURY


def test_build_default_constraints_per_person_multiplies_budget():
    constraints = build_default_constraints(make_request(per_person=True, travelers=3))
    assert constraints.max_budget_amount == 90000.0


def test_build_default_constraints_distributes_interest_weights():
    constraints = build_default_constraints(make_request(interests=["history", "food"]))
    assert constraints.priority_weights == {"history": 0.5, "food": 0.5}


def test_build_default_constraints_no_interests_gives_empty_weights():
    constraints = build_default_constraints(make_request(interests=[]))
    assert constraints.priority_weights == {}