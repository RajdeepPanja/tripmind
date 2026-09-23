"""
Test doubles for SerpApi and Groq/LLM calls — lets agent and workflow
tests run fully offline with no SERPAPI_KEY or GROQ_API_KEY required.
"""
import json
from typing import Any


class FakeSerpApiClient:
    """Duck-types SerpApiClient's `search` method."""

    def __init__(self, response: dict[str, Any] | None = None, error: Exception | None = None):
        self._response = response or {}
        self._error = error
        self.last_params: dict[str, Any] | None = None

    async def search(self, params: dict[str, Any]) -> dict[str, Any]:
        self.last_params = params
        if self._error:
            raise self._error
        return self._response


class FakeItineraryLLM:
    """
    Duck-types the `.ainvoke(messages) -> LLMItineraryOutput` interface the
    Itinerary Agent expects.

    By default, auto-generates a well-formed response by echoing back
    whatever place_ids it's given in the prompt — this lets workflow tests
    avoid predicting randomly generated place IDs ahead of time. Pass
    `raise_error` or `bad_response` to simulate failure modes instead.
    """

    def __init__(self, raise_error: Exception | None = None, bad_response: Any = None):
        self._raise_error = raise_error
        self._bad_response = bad_response
        self.last_messages: list[dict] | None = None

    async def ainvoke(self, messages: list[dict]):
        self.last_messages = messages

        if self._raise_error:
            raise self._raise_error
        if self._bad_response is not None:
            return self._bad_response

        from agents.itinerary_agent import LLMActivityItem, LLMDayPlan, LLMItineraryOutput

        user_content = json.loads(messages[1]["content"])
        days = []
        for day in user_content["days"]:
            activities = [
                LLMActivityItem(time=f"{9 + i}:00", place_id=p["place_id"], title=p["name"])
                for i, p in enumerate(day["places"])
            ]
            days.append(LLMDayPlan(day_number=day["day_number"], activities=activities))

        return LLMItineraryOutput(days=days, reasoning="Auto-generated test itinerary.")