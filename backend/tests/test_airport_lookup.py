"""
Unit tests for the city-name -> IATA airport code lookup — added after
the live smoke test showed SerpApi's Google Flights engine rejects bare
city names for departure_id/arrival_id.
"""
import pytest

from services.airport_lookup import UnknownAirportCityError, resolve_airport_code


def test_resolve_known_city_lowercase():
    assert resolve_airport_code("kolkata") == "CCU"


def test_resolve_known_city_mixed_case():
    assert resolve_airport_code("Jaipur") == "JAI"


def test_resolve_passthrough_airport_code():
    assert resolve_airport_code("ccu") == "CCU"
    assert resolve_airport_code("JAI") == "JAI"


def test_resolve_unknown_city_raises():
    with pytest.raises(UnknownAirportCityError):
        resolve_airport_code("Atlantis")


def test_resolve_strips_whitespace():
    assert resolve_airport_code("  Kolkata  ") == "CCU"