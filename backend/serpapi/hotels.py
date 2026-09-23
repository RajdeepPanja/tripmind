"""
Google Hotels search via SerpApi, plus normalization into HotelOption.
"""
from __future__ import annotations

import uuid
from datetime import date

from models.common import GeoPoint, Money, SourceRef
from models.enums import DataSource
from models.hotel import HotelOption
from models.search import HotelSearchRequest
from serpapi.client import SerpApiClient


def build_hotel_search_params(request: HotelSearchRequest) -> dict:
    return {
        "engine": "google_hotels",
        "q": request.destination,
        "check_in_date": request.check_in_date.isoformat(),
        "check_out_date": request.check_out_date.isoformat(),
        "adults": request.travelers,
        "currency": request.currency,
        "hl": "en",
    }


def _extract_nights(check_in: str, check_out: str) -> int | None:
    try:
        nights = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
        return nights if nights > 0 else None
    except (ValueError, TypeError):
        return None


def _normalize_single_hotel(item: dict, currency: str, nights: int) -> HotelOption | None:
    name = item.get("name")
    gps = item.get("gps_coordinates") or {}
    latitude = gps.get("latitude")
    longitude = gps.get("longitude")

    rate = item.get("rate_per_night") or {}
    price_per_night = rate.get("extracted_lowest")

    total = item.get("total_rate") or {}
    total_price = total.get("extracted_lowest")

    if not all([name, latitude is not None, longitude is not None, price_per_night]):
        return None

    if total_price is None:
        # Exact arithmetic on a verified nightly rate — not fabrication.
        total_price = round(price_per_night * nights, 2)

    try:
        return HotelOption(
            id=str(uuid.uuid4()),
            name=name,
            rating=item.get("overall_rating"),
            review_count=item.get("reviews"),
            price_per_night=Money(amount=float(price_per_night), currency=currency),
            total_price=Money(amount=float(total_price), currency=currency),
            nights=nights,
            location=GeoPoint(latitude=float(latitude), longitude=float(longitude)),
            amenities=item.get("amenities") or [],
            source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_HOTELS, query=name),
        )
    except (ValueError, TypeError):
        return None


def normalize_hotel_response(
    raw: dict, currency: str, check_in_date: str, check_out_date: str
) -> tuple[list[HotelOption], int]:
    nights = _extract_nights(check_in_date, check_out_date) or 1
    properties = raw.get("properties") or []

    normalized: list[HotelOption] = []
    skipped = 0

    for item in properties:
        hotel = _normalize_single_hotel(item, currency, nights)
        if hotel is None:
            skipped += 1
        else:
            normalized.append(hotel)

    return normalized, skipped


async def search_hotels_raw(request: HotelSearchRequest, client: SerpApiClient) -> dict:
    return await client.search(build_hotel_search_params(request))