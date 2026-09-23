"""
Itinerary Agent — arranges verified, already-priced travel data (flights,
hotel, places, route plan) into a day-by-day schedule using Groq.

Hard rule: the LLM may choose scheduling — which supplied place_id goes in
which time slot, in what order, with what short descriptive title/notes —
but it must NEVER invent factual travel data: no prices, distances, travel
durations, opening hours, ratings, availability, or source information.
The LLM only ever receives and returns place_id references; every factual
field in the final Itinerary (duration, travel time/distance, hotel_id) is
resolved from TripState data in Python afterward, never taken from the
LLM's output directly.
"""
from __future__ import annotations

import json
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field

from core.llm import LLMError, get_groq_llm
from models.budget import BudgetBreakdown
from models.constraints import TripConstraints
from models.enums import TransportMode
from models.hotel import HotelOption
from models.itinerary import DailyActivity, DayPlan, Itinerary, TravelLeg
from models.place import Place
from models.route import RoutePlan
from models.trip_request import TripRequest


class ItineraryGenerationError(Exception):
    """Raised when the LLM call fails or its output cannot be trusted."""


class LLMActivityItem(BaseModel):
    """One scheduled slot proposed by the LLM."""

    time: str
    place_id: str = Field(..., min_length=1)
    title: str
    notes: str | None = None


class LLMDayPlan(BaseModel):
    day_number: int
    activities: list[LLMActivityItem] = Field(default_factory=list)


class LLMItineraryOutput(BaseModel):
    """Contract the LLM's structured output must conform to."""

    model_config = ConfigDict(extra="forbid")

    days: list[LLMDayPlan] = Field(default_factory=list)
    reasoning: str = ""


ITINERARY_SYSTEM_PROMPT = """You are scheduling a day-by-day trip itinerary.

IMPORTANT OUTPUT RULES:

1. Every activity MUST use an exact place_id copied from the input.
2. NEVER create, modify, abbreviate, normalize, or guess a place_id.
3. NEVER use an empty string for place_id.
4. Every activity must correspond to one of the places supplied for that same day.
5. If a place is supplied, use its exact place_id character-for-character.
6. Do not create activities that do not correspond to a supplied place.
7. The place name is for understanding only. The place_id is the authoritative identifier.
8. You may choose only scheduling information:
   - time
   - ordering
   - title
   - short notes
9. NEVER invent factual travel data such as prices, distances, travel durations,
   opening hours, ratings, availability, or source information.
10. If revision_feedback is provided, fix only the described scheduling issues.

The input contains verified places grouped by day.

For every activity you output, place_id MUST be copied directly from one of the
place_id values appearing in that day's input.

Example:

Input:
{
  "day_number": 1,
  "places": [
    {"place_id": "abc123", "name": "Amber Fort"},
    {"place_id": "xyz789", "name": "City Palace"}
  ]
}

Valid:
{
  "time": "10:00",
  "place_id": "abc123",
  "title": "Explore Amber Fort"
}

Valid:
{
  "time": "15:00",
  "place_id": "xyz789",
  "title": "Visit City Palace"
}

Invalid:
{
  "time": "10:00",
  "place_id": "",
  "title": "Explore Amber Fort"
}

Invalid:
{
  "time": "10:00",
  "place_id": "Amber Fort",
  "title": "Explore Amber Fort"
}

Invalid:
{
  "time": "10:00",
  "place_id": "invented-id",
  "title": "Explore Amber Fort"
}
"""


def _build_itinerary_from_llm_output(
    llm_output: LLMItineraryOutput,
    route_plan: RoutePlan,
    places_by_id: dict[str, Place],
    hotel: HotelOption | None,
    trip_request: TripRequest,
) -> Itinerary:
    known_ids = set(places_by_id.keys())
    route_days_by_number = {d.day_number: d for d in route_plan.days}

    days: list[DayPlan] = []

    for llm_day in llm_output.days:
        route_day = route_days_by_number.get(llm_day.day_number)
        activities: list[DailyActivity] = []

        for item in llm_day.activities:
            if item.place_id not in known_ids:
                raise ItineraryGenerationError(
                    f"LLM referenced unknown place_id '{item.place_id}' on "
                    f"day {llm_day.day_number}"
                )

            place = places_by_id[item.place_id]
            duration = place.typical_visit_minutes or 60

            travel_leg = None
            if route_day:
                matching_stop = next(
                    (s for s in route_day.stops if s.place_id == item.place_id), None
                )
                if matching_stop:
                    travel_leg = TravelLeg(
                        to_place_id=item.place_id,
                        mode=matching_stop.travel_mode_from_previous or TransportMode.TAXI,
                        distance_km=matching_stop.distance_from_previous_km,
                        duration_minutes=matching_stop.travel_minutes_from_previous,
                    )

            activities.append(
                DailyActivity(
                    time=item.time,
                    place_id=item.place_id,
                    title=item.title or place.name,
                    duration_minutes=duration,
                    notes=item.notes,
                    travel_to_next=travel_leg,
                )
            )

        estimated_travel_minutes = route_day.total_travel_minutes if route_day else 0
        day_date = trip_request.start_date + timedelta(days=llm_day.day_number - 1)

        days.append(
            DayPlan(
                day_number=llm_day.day_number,
                date=day_date,
                activities=activities,
                estimated_travel_minutes=estimated_travel_minutes,
                hotel_id=hotel.id if hotel else None,
            )
        )

    return Itinerary(days=days, generated_reasoning=llm_output.reasoning)


async def run_itinerary_agent(
    route_plan: RoutePlan,
    budget: BudgetBreakdown,
    places: list[Place],
    hotel: HotelOption | None,
    constraints: TripConstraints,
    trip_request: TripRequest,
    revision_feedback: list[str] | None = None,
    llm=None,
) -> Itinerary:
    """
    `llm` is any object exposing an async `ainvoke(messages) -> LLMItineraryOutput`
    method. Production code (when `llm` is None) uses a real Groq chat
    model bound with `.with_structured_output(LLMItineraryOutput)`; tests
    inject a fake so no network call is ever made offline.
    """
    places_by_id = {p.id: p for p in places}

    day_candidates = [
        {
            "day_number": route_day.day_number,
            "places": [
                {
                    "place_id": stop.place_id,
                    "name": places_by_id[stop.place_id].name,
                    "category": places_by_id[stop.place_id].category.value,
                }
                for stop in route_day.stops
                if stop.place_id in places_by_id
            ],
        }
        for route_day in route_plan.days
    ]

    user_content = {
        "trip_pace": constraints.pace.value,
        "days": day_candidates,
        "revision_feedback": revision_feedback or [],
    }

    if llm is not None:
        active_llm = llm
    else:
        try:
            active_llm = get_groq_llm().with_structured_output(LLMItineraryOutput)
        except LLMError as exc:
            raise ItineraryGenerationError(str(exc)) from exc

    try:
        print("\n=== ITINERARY INPUT TO LLM ===")
        print(json.dumps(user_content, indent=2))
        print("================================\n")
        raw_output = await active_llm.ainvoke(
            [
                {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content)},
            ]
        )
    except Exception as exc:
        raise ItineraryGenerationError(f"LLM call failed: {exc}") from exc

    if not isinstance(raw_output, LLMItineraryOutput):
        try:
            raw_output = LLMItineraryOutput.model_validate(raw_output)
        except Exception as exc:
            raise ItineraryGenerationError(
                f"LLM returned output that does not match the expected structure: {exc}"
            ) from exc

    try:
        return _build_itinerary_from_llm_output(
            raw_output, route_plan, places_by_id, hotel, trip_request
        )
    except ItineraryGenerationError:
        raise
    except Exception as exc:
        raise ItineraryGenerationError(
            f"Failed to build itinerary from LLM output: {exc}"
        ) from exc