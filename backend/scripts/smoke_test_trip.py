"""
One-time live smoke test: runs the full LangGraph workflow against REAL
SerpApi and Groq APIs (loaded from backend/.env) with a realistic trip
request. Not part of the test suite — this is a manual diagnostic script,
safe to delete after use.

Run from inside backend/ so the relative .env path resolves correctly:
    cd D:\\tripmind\\backend
    .venv\\Scripts\\Activate.ps1
    python scripts/smoke_test_trip.py
"""
import asyncio
import sys
import traceback
from datetime import date
from pathlib import Path

# Make sure `backend/` is importable when running this script directly
# from inside backend/scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings  # noqa: E402
from graph.workflow import run_trip_planning  # noqa: E402
from models.budget import Budget  # noqa: E402
from models.constraints import TripConstraints  # noqa: E402
from models.enums import HotelTier, TravelStyle  # noqa: E402
from models.traveler import TravelerProfile  # noqa: E402
from models.trip_request import TripRequest  # noqa: E402


def check_keys_configured() -> bool:
    print("=" * 70)
    print("KEY CONFIGURATION CHECK (values are never printed)")
    print("=" * 70)
    groq_ok = bool(settings.groq_api_key)
    serpapi_ok = bool(settings.serpapi_key)
    print(f"GROQ_API_KEY configured:    {groq_ok}")
    print(f"SERPAPI_KEY configured:     {serpapi_ok}")
    print()
    if not groq_ok or not serpapi_ok:
        print("Missing a required key in backend/.env — stopping before any "
              "API calls are made.")
        return False
    return True


def make_trip_request() -> TripRequest:
    return TripRequest(
        origin="Kolkata",
        destination="Jaipur",
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 14),  # 4-day trip
        travelers=2,
        budget=Budget(total={"amount": 60000.0, "currency": "INR"}),
        profile=TravelerProfile(
            interests=["history", "food", "photography"],
            travel_style=TravelStyle.BALANCED,
            hotel_preference=HotelTier.MIDRANGE,
        ),
    )


def make_constraints() -> TripConstraints:
    return TripConstraints(
        max_budget_amount=60000.0,
        pace=TravelStyle.BALANCED,
        hotel_tier=HotelTier.MIDRANGE,
        priority_weights={"history": 0.4, "food": 0.35, "photography": 0.25},
        max_daily_activities=5,
    )


def print_summary(final_state: dict) -> None:
    print("=" * 70)
    print("WORKFLOW RESULT SUMMARY")
    print("=" * 70)

    print(f"status:            {final_state.get('status')}")
    print(f"revision_count:    {final_state.get('revision_count')}")
    print()

    flights = final_state.get("flights") or []
    hotels = final_state.get("hotels") or []
    places = final_state.get("places") or []
    print(f"flights found:     {len(flights)}")
    print(f"hotels found:      {len(hotels)}")
    print(f"places found:      {len(places)}")
    print()

    selected_flight = final_state.get("selected_flight")
    if selected_flight:
        print("selected flight:")
        print(f"  airline:   {selected_flight.airline}")
        print(f"  route:     {selected_flight.origin_airport} -> {selected_flight.destination_airport}")
        print(f"  departure: {selected_flight.departure_time}")
        print(f"  price:     {selected_flight.price.amount} {selected_flight.price.currency}")
        print(f"  stops:     {selected_flight.stops}")
    else:
        print("selected flight:   None")
    print()

    selected_hotel = final_state.get("selected_hotel")
    if selected_hotel:
        print("selected hotel:")
        print(f"  name:      {selected_hotel.name}")
        print(f"  rating:    {selected_hotel.rating}")
        print(f"  price/night: {selected_hotel.price_per_night.amount} {selected_hotel.price_per_night.currency}")
        print(f"  total:     {selected_hotel.total_price.amount} {selected_hotel.total_price.currency}")
    else:
        print("selected hotel:    None")
    print()

    print("selection_reasons:", final_state.get("selection_reasons"))
    print()

    budget = final_state.get("budget")
    if budget:
        print("budget:")
        print(f"  total:     {budget.total_budget.amount} {budget.total_budget.currency}")
        print(f"  spent:     {budget.spent.amount} {budget.spent.currency}")
        print(f"  remaining: {budget.remaining.amount} {budget.remaining.currency}")
        for item in budget.line_items:
            print(f"    - {item.category.value}: {item.amount.amount} ({item.source.value})")
    else:
        print("budget:            None")
    print()

    route_plan = final_state.get("route_plan")
    if route_plan:
        print(f"route_plan:        {len(route_plan.days)} day(s), "
              f"{route_plan.total_distance_km} km total")
        for day in route_plan.days:
            print(f"    day {day.day_number}: {len(day.stops)} stop(s), "
                  f"{day.total_travel_minutes} min travel")
    else:
        print("route_plan:        None")
    print()

    itinerary = final_state.get("itinerary")
    if itinerary:
        print(f"itinerary:         {len(itinerary.days)} day(s)")
        for day in itinerary.days:
            print(f"    day {day.day_number} ({day.date}): {len(day.activities)} activities")
            for activity in day.activities:
                print(f"        {activity.time}  {activity.title}  "
                      f"(place_id={activity.place_id}, {activity.duration_minutes}min)")
        print()
        print(f"    reasoning: {itinerary.generated_reasoning}")
    else:
        print("itinerary:         None")
    print()

    verification = final_state.get("verification")
    if verification:
        print(f"verification:      passed={verification.passed}")
        for v in verification.violations:
            print(f"    VIOLATION: [{v.code}] {v.message}")
        for u in verification.unsupported_claims:
            print(f"    UNSUPPORTED: [{u.code}] {u.message}")
    else:
        print("verification:      None")
    print()

    errors = final_state.get("errors") or []
    print(f"errors/warnings ({len(errors)}):")
    for e in errors:
        print(f"    - {e}")


async def main() -> None:
    if not check_keys_configured():
        return

    request = make_trip_request()
    constraints = make_constraints()

    print("=" * 70)
    print(f"Running trip planning: {request.origin} -> {request.destination}, "
          f"{request.duration_days} days, {request.travelers} travelers")
    print("=" * 70)
    print("(No client/llm overrides passed — this uses REAL SerpApi and REAL Groq.)")
    print()

    try:
        final_state = await run_trip_planning(request, constraints, max_revisions=2)
    except Exception:
        print("=" * 70)
        print("UNHANDLED EXCEPTION — the workflow raised instead of completing.")
        print("The traceback below shows which node/function was executing —")
        print("that's the layer to look at first.")
        print("=" * 70)
        traceback.print_exc()
        return

    print_summary(final_state)


if __name__ == "__main__":
    asyncio.run(main())
    