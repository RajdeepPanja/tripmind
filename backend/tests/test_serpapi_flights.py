from datetime import date

from models.search import FlightSearchRequest
from serpapi.flights import build_flight_search_params, normalize_flight_response


def make_request(return_date=None):
    return FlightSearchRequest(
        origin="CCU",
        destination="JAI",
        departure_date=date(2026, 12, 1),
        return_date=return_date,
        travelers=2,
        currency="INR",
    )


def test_build_params_one_way():
    params = build_flight_search_params(make_request())
    assert params["type"] == "2"
    assert params["departure_id"] == "CCU"
    assert params["arrival_id"] == "JAI"
    assert "return_date" not in params


def test_build_params_round_trip():
    params = build_flight_search_params(make_request(return_date=date(2026, 12, 6)))
    assert params["type"] == "1"
    assert params["return_date"] == "2026-12-06"


VALID_RAW_RESPONSE = {
    "best_flights": [
        {
            "flights": [
                {
                    "departure_airport": {"id": "CCU", "time": "2026-12-01 06:00"},
                    "arrival_airport": {"id": "JAI", "time": "2026-12-01 09:00"},
                    "airline": "IndiGo",
                    "flight_number": "6E 123",
                }
            ],
            "total_duration": 180,
            "price": 8000,
        }
    ],
    "other_flights": [],
}


def test_normalize_valid_response():
    flights, skipped = normalize_flight_response(VALID_RAW_RESPONSE, "INR")
    assert len(flights) == 1
    assert skipped == 0
    flight = flights[0]
    assert flight.airline == "IndiGo"
    assert flight.origin_airport == "CCU"
    assert flight.destination_airport == "JAI"
    assert flight.price.amount == 8000
    assert flight.stops == 0


def test_normalize_skips_missing_price():
    raw = {
        "best_flights": [
            {
                "flights": [
                    {
                        "departure_airport": {"id": "CCU", "time": "2026-12-01 06:00"},
                        "arrival_airport": {"id": "JAI", "time": "2026-12-01 09:00"},
                        "airline": "IndiGo",
                    }
                ],
                "total_duration": 180,
            }
        ]
    }
    flights, skipped = normalize_flight_response(raw, "INR")
    assert len(flights) == 0
    assert skipped == 1


def test_normalize_skips_malformed_flight_list():
    raw = {"best_flights": [{"flights": []}]}
    flights, skipped = normalize_flight_response(raw, "INR")
    assert len(flights) == 0
    assert skipped == 1


def test_normalize_empty_response():
    flights, skipped = normalize_flight_response({}, "INR")
    assert flights == []
    assert skipped == 0


def test_normalize_multi_leg_counts_stops():
    raw = {
        "best_flights": [
            {
                "flights": [
                    {
                        "departure_airport": {"id": "CCU", "time": "2026-12-01 06:00"},
                        "arrival_airport": {"id": "BOM", "time": "2026-12-01 08:00"},
                        "airline": "IndiGo",
                    },
                    {
                        "departure_airport": {"id": "BOM", "time": "2026-12-01 09:00"},
                        "arrival_airport": {"id": "JAI", "time": "2026-12-01 10:30"},
                        "airline": "IndiGo",
                    },
                ],
                "total_duration": 270,
                "price": 9500,
            }
        ]
    }
    flights, skipped = normalize_flight_response(raw, "INR")
    assert len(flights) == 1
    assert flights[0].stops == 1
    assert flights[0].origin_airport == "CCU"
    assert flights[0].destination_airport == "JAI"