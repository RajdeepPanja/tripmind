"""
Google Flights search via SerpApi, plus normalization into FlightOption.
Never invents price, timing, or availability — malformed groups are
skipped and counted, not patched with guessed values.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from models.common import Money, SourceRef
from models.enums import DataSource
from models.flight import FlightOption
from models.search import FlightSearchRequest
from serpapi.client import SerpApiClient


def build_flight_search_params(request: FlightSearchRequest) -> dict:
    params: dict = {
        "engine": "google_flights",
        "departure_id": request.origin,
        "arrival_id": request.destination,
        "outbound_date": request.departure_date.isoformat(),
        "adults": request.travelers,
        "currency": request.currency,
        "hl": "en",
    }
    if request.return_date:
        params["return_date"] = request.return_date.isoformat()
        params["type"] = "1"  # round trip
    else:
        params["type"] = "2"  # one way
    return params


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None


def _normalize_single_flight_group(group: dict, currency: str) -> FlightOption | None:
    """
    One bookable itinerary from SerpApi, which may contain multiple legs
    (connections) under `flights`. Returns None (skip) if required fields
    are missing or malformed rather than fabricating them.
    """
    legs = group.get("flights")
    if not legs or not isinstance(legs, list):
        return None

    first_leg = legs[0]
    last_leg = legs[-1]

    departure_airport = first_leg.get("departure_airport") or {}
    arrival_airport = last_leg.get("arrival_airport") or {}

    origin_code = departure_airport.get("id")
    destination_code = arrival_airport.get("id")
    departure_time = _parse_datetime(departure_airport.get("time"))
    arrival_time = _parse_datetime(arrival_airport.get("time"))
    duration_minutes = group.get("total_duration")
    price = group.get("price")

    if not all(
        [origin_code, destination_code, departure_time, arrival_time, duration_minutes, price]
    ):
        return None

    airline = first_leg.get("airline") or "Unknown"
    flight_number = first_leg.get("flight_number")
    stops = max(0, len(legs) - 1)

    try:
        return FlightOption(
            id=str(uuid.uuid4()),
            airline=airline,
            flight_number=flight_number,
            origin_airport=origin_code,
            destination_airport=destination_code,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_minutes=int(duration_minutes),
            stops=stops,
            price=Money(amount=float(price), currency=currency),
            source_ref=SourceRef(
                source=DataSource.SERPAPI_GOOGLE_FLIGHTS,
                query=f"{origin_code}->{destination_code}",
            ),
        )
    except (ValueError, TypeError):
        return None


def normalize_flight_response(raw: dict, currency: str) -> tuple[list[FlightOption], int]:
    """Returns (normalized_flights, skipped_count)."""
    groups = list(raw.get("best_flights") or []) + list(raw.get("other_flights") or [])

    normalized: list[FlightOption] = []
    skipped = 0

    for group in groups:
        flight = _normalize_single_flight_group(group, currency)
        if flight is None:
            skipped += 1
        else:
            normalized.append(flight)

    return normalized, skipped


async def search_flights_raw(request: FlightSearchRequest, client: SerpApiClient) -> dict:
    return await client.search(build_flight_search_params(request))