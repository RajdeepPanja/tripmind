from serpapi.places import build_places_search_params, normalize_places_response


def test_build_places_params_attractions():
    params = build_places_search_params("Jaipur", "attractions")
    assert "Jaipur" in params["q"]
    assert params["engine"] == "google_maps"


VALID_RAW = {
    "local_results": [
        {
            "title": "Amber Fort",
            "gps_coordinates": {"latitude": 26.9855, "longitude": 75.8513},
            "rating": 4.6,
            "reviews": 5000,
            "address": "Amber, Jaipur",
            "hours": "8AM-6PM",
        }
    ]
}


def test_normalize_valid_attraction():
    places, skipped = normalize_places_response(VALID_RAW, "attractions")
    assert len(places) == 1
    assert skipped == 0
    assert places[0].name == "Amber Fort"
    assert places[0].category.value == "attraction"


def test_normalize_valid_restaurant():
    raw = {
        "local_results": [
            {
                "title": "Local Thali House",
                "gps_coordinates": {"latitude": 26.91, "longitude": 75.79},
                "rating": 4.3,
                "type": "North Indian Restaurant",
            }
        ]
    }
    places, skipped = normalize_places_response(raw, "restaurants")
    assert len(places) == 1
    assert places[0].category.value == "restaurant"
    assert "North Indian Restaurant" in places[0].cuisine_types


def test_normalize_skips_missing_coordinates():
    raw = {"local_results": [{"title": "Mystery Place"}]}
    places, skipped = normalize_places_response(raw, "attractions")
    assert len(places) == 0
    assert skipped == 1


def test_normalize_skips_missing_title():
    raw = {"local_results": [{"gps_coordinates": {"latitude": 26.9, "longitude": 75.8}}]}
    places, skipped = normalize_places_response(raw, "attractions")
    assert len(places) == 0
    assert skipped == 1


def test_normalize_empty_results():
    places, skipped = normalize_places_response({}, "attractions")
    assert places == []
    assert skipped == 0


def test_normalize_multiple_places():
    raw = {
        "local_results": [
            {"title": "Place A", "gps_coordinates": {"latitude": 1, "longitude": 1}},
            {"title": "Place B", "gps_coordinates": {"latitude": 2, "longitude": 2}},
        ]
    }
    places, skipped = normalize_places_response(raw, "attractions")
    assert len(places) == 2