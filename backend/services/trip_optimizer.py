"""
Budget-aware joint selection of a flight and hotel combination.

Independent ranking (each of flight/hotel picked on its own) can produce
a combination that exceeds the user's budget even though each option
looked reasonable alone. This service evaluates flight+hotel combinations
jointly against the budget left over after the buffer AND estimated
food/activities/transport costs (services/cost_estimator.py) — not just
the buffer alone, which previously allowed a combo that technically fit
the total budget but left nothing for the rest of the trip. It only
falls back to the cheapest available combination — honestly flagged by
verification as OVER_BUDGET — if nothing fits. It never hides or fakes a
shortfall.
"""
from models.constraints import TripConstraints
from models.flight import FlightOption
from models.hotel import HotelOption
from models.place import Place
from models.trip_request import TripRequest
from services.cost_estimator import (
    estimate_activities_cost,
    estimate_food_cost,
    estimate_transport_cost,
)
from services.scoring import score_flight, score_hotel


def _available_for_booking(
    trip_request: TripRequest,
    constraints: TripConstraints,
    places: list[Place] | None = None,
    buffer_ratio: float = 0.10,
) -> float:
    """
    Total budget minus the buffer reservation AND estimated food,
    activities, and local transport costs.
    """
    places = places or []

    total_budget_amount = trip_request.budget.total.amount

    if trip_request.budget.per_person:
        total_budget_amount = round(
            total_budget_amount * trip_request.travelers, 2
        )

    buffer_amount = round(total_budget_amount * buffer_ratio, 2)

    food = estimate_food_cost(
        trip_request.travelers,
        trip_request.duration_days,
        constraints.hotel_tier,
    )

    activities = estimate_activities_cost(
        places,
        trip_request.travelers,
        trip_request.duration_days,
        constraints.max_daily_activities,
    )

    transport = estimate_transport_cost(
        trip_request.travelers,
        trip_request.duration_days,
    )

    return total_budget_amount - buffer_amount - food - activities - transport


def select_budget_aware_combo(
    flights: list[FlightOption],
    hotels: list[HotelOption],
    constraints: TripConstraints,
    trip_request: TripRequest,
    places: list[Place] | None = None,
) -> tuple[
    FlightOption | None,
    HotelOption | None,
    dict[str, str],
    bool,
]:
    """
    Returns:
        (
            selected_flight,
            selected_hotel,
            selection_reasons,
            budget_feasible,
        )

    Scans every flight x hotel combination, keeps only those whose
    combined price fits the budget left after buffer + estimated
    food/activities/transport, and picks the highest-scoring valid one.

    If nothing fits, falls back to the single cheapest combination and
    returns budget_feasible=False.
    """
    reasons: dict[str, str] = {}
    places = places or []

    if not flights and not hotels:
        return None, None, reasons, False

    if flights and not hotels:
        best_flight = max(
            flights,
            key=lambda f: score_flight(f, constraints),
        )

        reasons["flight"] = (
            "Best available option (no hotel results to jointly "
            "optimize against)"
        )

        return best_flight, None, reasons, False

    if hotels and not flights:
        best_hotel = max(
            hotels,
            key=lambda h: score_hotel(h, constraints),
        )

        reasons["hotel"] = (
            "Best available option (no flight results to jointly "
            "optimize against)"
        )

        return None, best_hotel, reasons, False

    available = _available_for_booking(
        trip_request,
        constraints,
        places,
    )

    all_combos = []
    valid_combos = []

    for flight in flights:
        for hotel in hotels:
            combined_price = (
                flight.price.amount + hotel.total_price.amount
            )

            combined_score = (
                score_flight(flight, constraints)
                + score_hotel(hotel, constraints)
            )

            entry = (
                flight,
                hotel,
                combined_price,
                combined_score,
            )

            all_combos.append(entry)

            if combined_price <= available:
                valid_combos.append(entry)

    # A valid combination exists within the available budget.
    if valid_combos:
        best_flight, best_hotel, _, _ = max(
            valid_combos,
            key=lambda c: c[3],
        )

        reasons["flight"] = (
            "Selected jointly with the hotel to fit within the trip's "
            "total budget (after reserving for food, activities, and "
            "local transport) while minimizing price and stops"
        )

        reasons["hotel"] = (
            "Selected jointly with the flight to fit within the trip's "
            "total budget (after reserving for food, activities, and "
            "local transport) while balancing price and rating"
        )

        return best_flight, best_hotel, reasons, True

    # Nothing fits — choose the cheapest available combination honestly.
    best_flight, best_hotel, cheapest_total, _ = min(
        all_combos,
        key=lambda c: c[2],
    )

    shortfall = cheapest_total - available

    reasons["flight"] = (
        "Cheapest available option — no flight+hotel combination fits "
        "the budget left after estimated food, activities, and transport"
    )

    reasons["hotel"] = (
        "Cheapest available option — no flight+hotel combination fits "
        "the budget left after estimated food, activities, and transport"
    )

    reasons["budget"] = (
        f"Cheapest flight+hotel combination is {cheapest_total:.0f} INR, "
        f"which is {shortfall:.0f} INR above the available booking budget. "
        "Showing the cheapest available combination as a fallback."
    )

    return best_flight, best_hotel, reasons, False