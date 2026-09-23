"""
Hotel Agent: turns a HotelSearchRequest into verified HotelOption results
via SerpApi (google_hotels).
"""
from agents.errors import AgentError
from models.search import HotelSearchRequest, HotelSearchResult
from serpapi.client import SerpApiClient, SerpApiError
from serpapi.hotels import normalize_hotel_response, search_hotels_raw


async def run_hotel_agent(
    request: HotelSearchRequest, client: SerpApiClient | None = None
) -> HotelSearchResult:
    active_client = client or SerpApiClient()

    try:
        raw = await search_hotels_raw(request, active_client)
    except SerpApiError as exc:
        raise AgentError(f"Hotel Agent: SerpApi request failed — {exc}") from exc

    hotels, skipped = normalize_hotel_response(
        raw,
        request.currency,
        request.check_in_date.isoformat(),
        request.check_out_date.isoformat(),
    )

    return HotelSearchResult(
        results=hotels,
        skipped_count=skipped,
        query_used=request.destination,
    )