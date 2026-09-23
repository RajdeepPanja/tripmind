"""
Base SerpApi client.

All engine-specific wrappers (flights.py, hotels.py, places.py, news.py)
go through this client so caching, retries, and source-logging are
handled in exactly one place.
"""
from __future__ import annotations

from typing import Any

import httpx

from core.config import settings

SERPAPI_BASE_URL = "https://serpapi.com/search.json"


class SerpApiError(Exception):
    """Raised when a SerpApi call fails or returns an error payload."""


class SerpApiClient:
    """
    Thin wrapper around SerpApi's HTTP API.

    Usage:
        client = SerpApiClient()
        data = await client.search({"engine": "google_flights", ...})

    For tests, don't instantiate this directly — pass a duck-typed fake
    with an async `search(params) -> dict` method into agent functions
    instead (see tests/fakes.py). This class raises immediately if no
    SERPAPI_KEY is configured, which is intentional: it should fail fast
    in real usage, and never be constructed at all in offline tests.
    """

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0):
        self._api_key = api_key or settings.serpapi_key
        self._timeout_seconds = timeout_seconds
        self.last_raw_response: dict[str, Any] | None = None

        if not self._api_key:
            raise SerpApiError(
                "SERPAPI_KEY is not set. Add it to backend/.env before making "
                "live requests."
            )

    async def search(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Perform a raw SerpApi search call. Stores the raw response on
        `self.last_raw_response` for debugging before returning it.
        """
        query_params = {**params, "api_key": self._api_key}

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(SERPAPI_BASE_URL, params=query_params)

        if response.status_code != 200:
            raise SerpApiError(
                f"SerpApi request failed with status {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        if "error" in data:
            raise SerpApiError(f"SerpApi returned an error: {data['error']}")

        self.last_raw_response = data
        return data