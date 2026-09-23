"""
Google Maps / Places search via SerpApi, plus normalization into Place
and Restaurant models.
"""
from __future__ import annotations

import uuid

from models.common import GeoPoint, SourceRef
from models.enums import DataSource, PlaceCategory
from models.place import Place, Restaurant
from serpapi.client import SerpApiClient

CATEGORY_QUERY_TEMPLATES = {
    "attractions": "top attractions in {destination}",
    "restaurants": "best restaurants in {destination}",
}


def build_places_search_params(destination: str, category: str) -> dict:
    template = CATEGORY_QUERY_TEMPLATES.get(category, f"{category} in {{destination}}")
    return {
        "engine": "google_maps",
        "q": template.format(destination=destination),
        "type": "search",
        "hl": "en",
    }


def _normalize_single_place(item: dict, category: str) -> Place | None:
    name = item.get("title")
    gps = item.get("gps_coordinates") or {}
    latitude = gps.get("latitude")
    longitude = gps.get("longitude")

    if not all([name, latitude is not None, longitude is not None]):
        return None

    place_category = (
        PlaceCategory.RESTAURANT if category == "restaurants" else PlaceCategory.ATTRACTION
    )

    common_kwargs = dict(
        id=str(uuid.uuid4()),
        name=name,
        category=place_category,
        rating=item.get("rating"),
        review_count=item.get("reviews"),
        opening_hours=item.get("hours"),
        price_level=item.get("price"),
        address=item.get("address"),
        location=GeoPoint(latitude=float(latitude), longitude=float(longitude)),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS, query=name),
    )

    try:
        if place_category == PlaceCategory.RESTAURANT:
            place_type = item.get("type") or ""
            return Restaurant(**common_kwargs, cuisine_types=[place_type] if place_type else [])
        return Place(**common_kwargs)
    except (ValueError, TypeError):
        return None


def normalize_places_response(raw: dict, category: str) -> tuple[list[Place], int]:
    results = raw.get("local_results") or []

    normalized: list[Place] = []
    skipped = 0

    for item in results:
        place = _normalize_single_place(item, category)
        if place is None:
            skipped += 1
        else:
            normalized.append(place)

    return normalized, skipped


async def search_places_raw(destination: str, category: str, client: SerpApiClient) -> dict:
    return await client.search(build_places_search_params(destination, category))