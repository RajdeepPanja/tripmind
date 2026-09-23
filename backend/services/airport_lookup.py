"""
Minimal city-name -> IATA airport code lookup for the Flight Agent.
Google Flights (via SerpApi) requires departure_id/arrival_id to be an
uppercase 3-letter IATA code (or a Google Place ID) — a bare city name
like "Kolkata" is rejected with a 400. This is a small, explicit lookup
table rather than a geocoding API call, to keep SerpApi usage (and cost)
minimal; unknown cities raise a clear error instead of guessing.
"""

CITY_TO_AIRPORT_CODE: dict[str, str] = {
    "kolkata": "CCU",
    "jaipur": "JAI",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bengaluru": "BLR",
    "bangalore": "BLR",
    "chennai": "MAA",
    "hyderabad": "HYD",
    "pune": "PNQ",
    "goa": "GOI",
    "kochi": "COK",
    "ahmedabad": "AMD",
    "lucknow": "LKO",
    "jodhpur": "JDH",
    "udaipur": "UDR",
    "varanasi": "VNS",
    "amritsar": "ATQ",
    "guwahati": "GAU",
    "bhubaneswar": "BBI",
}


class UnknownAirportCityError(Exception):
    """Raised when a city name has no known IATA airport code mapping."""


def resolve_airport_code(city_or_code: str) -> str:
    """
    Returns an uppercase 3-letter IATA code. If `city_or_code` is already a
    3-letter code, it's returned as-is (uppercased). Otherwise it's looked
    up by lowercased city name; unknown cities raise
    UnknownAirportCityError rather than guessing or fabricating a code.
    """
    stripped = city_or_code.strip()

    if len(stripped) == 3 and stripped.isalpha():
        return stripped.upper()

    code = CITY_TO_AIRPORT_CODE.get(stripped.lower())
    if code is None:
        raise UnknownAirportCityError(
            f"No known airport code for '{city_or_code}'. Add it to "
            f"CITY_TO_AIRPORT_CODE in services/airport_lookup.py, or pass "
            f"an IATA code directly."
        )
    return code