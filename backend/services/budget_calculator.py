"""
Deterministic budget arithmetic. Takes verified priced data (flights,
hotels, and optional food/activity/transport estimates) and produces a
BudgetBreakdown. No LLM is involved in any of this math.
"""
from models.budget import Budget, BudgetBreakdown, BudgetLineItem
from models.enums import BudgetCategory, DataSource
from models.flight import FlightOption
from models.hotel import HotelOption
from models.trip_request import TripRequest


class BudgetError(Exception):
    """Raised when budget inputs are inconsistent (e.g. mismatched currencies)."""


def _sum_amounts(amounts: list[float]) -> float:
    return round(sum(amounts), 2)


def calculate_budget(
    trip_request: TripRequest,
    selected_flights: list[FlightOption],
    selected_hotels: list[HotelOption],
    estimated_food_per_person_per_day: float = 0.0,
    estimated_activities_per_person_per_day: float = 0.0,
    estimated_transport_total: float = 0.0,
    buffer_ratio: float = 0.10,
) -> BudgetBreakdown:
    """
    Computes a full BudgetBreakdown from verified inputs.

    `estimated_food_per_person_per_day`, `estimated_activities_per_person_per_day`,
    and `estimated_transport_total` should themselves be derived from real
    Place/Restaurant price_level data or user input upstream — this
    function only does the arithmetic, it does not invent these numbers.

    `buffer_ratio` reserves a fraction of the total budget as a safety
    buffer line item (deterministic, not a guess).
    """
    currency = trip_request.budget.total.currency

    flight_currencies = {f.price.currency for f in selected_flights}
    hotel_currencies = {h.total_price.currency for h in selected_hotels}
    if flight_currencies - {currency} or hotel_currencies - {currency}:
        raise BudgetError(
            f"All prices must be in {currency}; got flights={flight_currencies}, "
            f"hotels={hotel_currencies}"
        )

    travelers = trip_request.travelers
    duration_days = trip_request.duration_days

    flights_total = _sum_amounts([f.price.amount for f in selected_flights])
    hotels_total = _sum_amounts([h.total_price.amount for h in selected_hotels])
    food_total = round(
        estimated_food_per_person_per_day * travelers * duration_days, 2
    )
    activities_total = round(
        estimated_activities_per_person_per_day * travelers * duration_days, 2
    )
    transport_total = round(estimated_transport_total, 2)

    total_budget_amount = trip_request.budget.total.amount
    if trip_request.budget.per_person:
        total_budget_amount = round(total_budget_amount * travelers, 2)

    subtotal = _sum_amounts(
        [flights_total, hotels_total, food_total, activities_total, transport_total]
    )
    buffer_amount = round(total_budget_amount * buffer_ratio, 2)

    spent = _sum_amounts([subtotal, buffer_amount])
    remaining = round(total_budget_amount - spent, 2)

    line_items = [
        BudgetLineItem(
            category=BudgetCategory.FLIGHTS,
            amount={"amount": flights_total, "currency": currency},
            source=DataSource.SERPAPI_GOOGLE_FLIGHTS if selected_flights else DataSource.COMPUTED,
        ),
        BudgetLineItem(
            category=BudgetCategory.HOTELS,
            amount={"amount": hotels_total, "currency": currency},
            source=DataSource.SERPAPI_GOOGLE_HOTELS if selected_hotels else DataSource.COMPUTED,
        ),
        BudgetLineItem(
            category=BudgetCategory.FOOD,
            amount={"amount": food_total, "currency": currency},
            source=DataSource.COMPUTED,
        ),
        BudgetLineItem(
            category=BudgetCategory.ACTIVITIES,
            amount={"amount": activities_total, "currency": currency},
            source=DataSource.COMPUTED,
        ),
        BudgetLineItem(
            category=BudgetCategory.TRANSPORT,
            amount={"amount": transport_total, "currency": currency},
            source=DataSource.COMPUTED,
        ),
        BudgetLineItem(
            category=BudgetCategory.BUFFER,
            amount={"amount": buffer_amount, "currency": currency},
            source=DataSource.COMPUTED,
        ),
    ]

    per_person_per_day_amount = (
        round(spent / (travelers * duration_days), 2)
        if travelers > 0 and duration_days > 0
        else 0.0
    )

    return BudgetBreakdown(
        total_budget={"amount": total_budget_amount, "currency": currency},
        line_items=line_items,
        spent={"amount": spent, "currency": currency},
        remaining={"amount": remaining, "currency": currency},
        per_person_per_day={"amount": per_person_per_day_amount, "currency": currency},
    )


def is_over_budget(breakdown: BudgetBreakdown) -> bool:
    return breakdown.remaining.amount < 0