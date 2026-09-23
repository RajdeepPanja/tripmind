"""
Tests for Haversine distance and travel-time estimation.
"""
import pytest

from models.common import GeoPoint
from models.enums import TransportMode
from services.distance_calculator import (
    estimate_travel_minutes,
    haversine_distance_km,
    total_route_distance_km,
)

# Kolkata and New Delhi — known real-world distance is roughly 1300-1310 km
KOLKATA = GeoPoint(latitude=22.5726, longitude=88.3639)
NEW_DELHI = GeoPoint(latitude=28.6139, longitude=77.2090)


def test_haversine_distance_known_cities():
    distance = haversine_distance_km(KOLKATA, NEW_DELHI)
    assert 1250 < distance < 1350


def test_haversine_distance_same_point_is_zero():
    distance = haversine_distance_km(KOLKATA, KOLKATA)
    assert distance == 0.0


def test_haversine_distance_symmetric():
    d1 = haversine_distance_km(KOLKATA, NEW_DELHI)
    d2 = haversine_distance_km(NEW_DELHI, KOLKATA)
    assert d1 == d2


def test_estimate_travel_minutes_walk_short_distance():
    a = GeoPoint(latitude=22.5726, longitude=88.3639)
    b = GeoPoint(latitude=22.5750, longitude=88.3650)  # ~300m away
    minutes = estimate_travel_minutes(a, b, mode=TransportMode.WALK)
    assert 1 <= minutes <= 15


def test_estimate_travel_minutes_flight_long_distance():
    minutes = estimate_travel_minutes(KOLKATA, NEW_DELHI, mode=TransportMode.FLIGHT)
    # ~1300km at 700km/h is well under 2 hours
    assert 100 < minutes < 150


def test_estimate_travel_minutes_faster_mode_is_quicker():
    walk_minutes = estimate_travel_minutes(KOLKATA, NEW_DELHI, mode=TransportMode.WALK)
    flight_minutes = estimate_travel_minutes(KOLKATA, NEW_DELHI, mode=TransportMode.FLIGHT)
    assert flight_minutes < walk_minutes


def test_total_route_distance_multiple_points():
    points = [KOLKATA, NEW_DELHI, KOLKATA]
    total = total_route_distance_km(points)
    single_leg = haversine_distance_km(KOLKATA, NEW_DELHI)
    assert total == pytest.approx(single_leg * 2, rel=0.01)


def test_total_route_distance_single_point_is_zero():
    assert total_route_distance_km([KOLKATA]) == 0.0