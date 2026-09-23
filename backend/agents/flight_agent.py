"""
Flight Agent: turns a FlightSearchRequest into verified FlightOption
results via SerpApi (google_flights). Never invents data — SerpApi
failures become AgentError, malformed results are skipped and counted.
"""
from agents.errors import AgentError
from models.search import FlightSearchRequest, FlightSearchResult
from serpapi.client import SerpApiClient, SerpApiError
from serpapi.flights import normalize_flight_response, search_flights_raw


async def run_flight_agent(
    request: FlightSearchRequest, client: SerpApiClient | None = None
) -> FlightSearchResult:
    active_client = client or SerpApiClient()

    try:
        raw = await search_flights_raw(request, active_client)
    except SerpApiError as exc:
        raise AgentError(f"Flight Agent: SerpApi request failed — {exc}") from exc

    flights, skipped = normalize_flight_response(raw, request.currency)

    return FlightSearchResult(
        results=flights,
        skipped_count=skipped,
        query_used=f"{request.origin}->{request.destination} on {request.departure_date.isoformat()}",
    )