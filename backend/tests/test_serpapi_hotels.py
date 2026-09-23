from datetime import date

from models.search import HotelSearchRequest
from serpapi.hotels import build_hotel_search_params, normalize_hotel_response


def make_request():
    return HotelSearchRequest(
        destination="Jaipur",
        check_in_date=date(2026, 12, 1),
        check_out_date=date(2026, 12, 6),
        travelers=2,
    )


def test_build_hotel_params():
    params = build_hotel_search_params(make_request())
    assert params["q"] == "Jaipur"
    assert params["check_in_date"] == "2026-12-01"
    assert params["check_out_date"] == "2026-12-06"


VALID_RAW = {
    "properties": [
        {
            "name": "Hotel Rajasthan",
            "gps_coordinates": {"latitude": 26.9124, "longitude": 75.7873},
            "overall_rating": 4.2,
            "reviews": 1200,
            "rate_per_night": {"extracted_lowest": 3000},
            "total_rate": {"extracted_lowest": 15000},
            "amenities": ["Free Wi-Fi", "Pool"],
        }
    ]
}


def test_normalize_valid_hotel():
    hotels, skipped = normalize_hotel_response(VALID_RAW, "INR", "2026-12-01", "2026-12-06")
    assert len(hotels) == 1
    assert skipped == 0
    assert hotels[0].name == "Hotel Rajasthan"
    assert hotels[0].nights == 5
    assert hotels[0].price_per_night.amount == 3000
    assert hotels[0].total_price.amount == 15000


def test_normalize_derives_total_when_missing():
    raw = {
        "properties": [
            {
                "name": "Budget Inn",
                "gps_coordinates": {"latitude": 26.9, "longitude": 75.8},
                "rate_per_night": {"extracted_lowest": 1000},
            }
        ]
    }
    hotels, skipped = normalize_hotel_response(raw, "INR", "2026-12-01", "2026-12-06")
    assert len(hotels) == 1
    assert hotels[0].total_price.amount == 5000


def test_normalize_skips_missing_name():
    raw = {
        "properties": [
            {
                "gps_coordinates": {"latitude": 26.9, "longitude": 75.8},
                "rate_per_night": {"extracted_lowest": 1000},
            }
        ]
    }
    hotels, skipped = normalize_hotel_response(raw, "INR", "2026-12-01", "2026-12-06")
    assert len(hotels) == 0
    assert skipped == 1


def test_normalize_skips_missing_coordinates():
    raw = {
        "properties": [
            {"name": "No Location Hotel", "rate_per_night": {"extracted_lowest": 1000}}
        ]
    }
    hotels, skipped = normalize_hotel_response(raw, "INR", "2026-12-01", "2026-12-06")
    assert len(hotels) == 0
    assert skipped == 1


def test_normalize_empty_properties():
    hotels, skipped = normalize_hotel_response({}, "INR", "2026-12-01", "2026-12-06")
    assert hotels == []
    assert skipped == 0


def test_normalize_multiple_hotels():
    raw = {
        "properties": [
            {
                "name": "Hotel A",
                "gps_coordinates": {"latitude": 26.9, "longitude": 75.8},
                "rate_per_night": {"extracted_lowest": 1000},
            },
            {
                "name": "Hotel B",
                "gps_coordinates": {"latitude": 26.91, "longitude": 75.81},
                "rate_per_night": {"extracted_lowest": 5000},
            },
        ]
    }
    hotels, skipped = normalize_hotel_response(raw, "INR", "2026-12-01", "2026-12-06")
    assert len(hotels) == 2
    assert skipped == 0