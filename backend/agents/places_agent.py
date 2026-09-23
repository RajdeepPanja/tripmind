"""
Places Agent: searches Google Maps via SerpApi for attractions and
restaurants across the requested categories, normalizing into
Place/Restaurant models.
"""
from agents.errors import AgentError
from models.search import PlacesSearchRequest, PlacesSearchResult
from serpapi.client import SerpApiClient, SerpApiError
from serpapi.places import normalize_places_response, search_places_raw


async def run_places_agent(
    request: PlacesSearchRequest, client: SerpApiClient | None = None
) -> PlacesSearchResult:
    active_client = client or SerpApiClient()

    all_places = []
    total_skipped = 0
    queries_used: list[str] = []

    for category in request.categories:
        try:
            raw = await search_places_raw(request.destination, category, active_client)
        except SerpApiError as exc:
            raise AgentError(
                f"Places Agent: SerpApi request failed for category '{category}' — {exc}"
            ) from exc

        places, skipped = normalize_places_response(raw, category)
        all_places.extend(places[: request.max_results_per_category])
        total_skipped += skipped
        queries_used.append(category)

    return PlacesSearchResult(
        results=all_places,
        skipped_count=total_skipped,
        queries_used=queries_used,
    )