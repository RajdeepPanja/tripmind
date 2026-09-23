"""
Deterministic estimation of food, activity, and local-transport costs.

These are the categories in TripMind's budget with no directly reliable
priced SerpApi field to sum (unlike flights/hotels). Where real
price_level data exists on searched attraction Place results it's used;
otherwise a fixed per-person-per-day rate applies. Every value here is
recorded as `computed` (never `serpapi_*`) in the resulting
BudgetLineItem — these are estimates, not live prices, and are never
presented as anything else.
"""
from models.enums import HotelTier, PlaceCategory
from models.place import Place

# Flat per-person-per-day food estimate, keyed by requested hotel tier as
# a simple proxy for spending level — there's no reliable per-meal live
# price across all restaurant search results to sum instead.
FOOD_PER_PERSON_PER_DAY = {
    HotelTier.BUDGET: 800.0,
    HotelTier.MIDRANGE: 1500.0,
    HotelTier.LUXURY: 3000.0,
}

# Maps SerpApi's price_level strings ("$" .. "$$$$") to an estimated
# per-person attraction/ticket cost in INR when available.
PRICE_LEVEL_TO_ACTIVITY_COST = {
    "$": 200.0,
    "$$": 500.0,
    "$$$": 1000.0,
    "$$$$": 2000.0,
}
DEFAULT_ACTIVITY_COST_PER_PERSON = 400.0

# Flat local-transport estimate (taxis/rideshare between stops), per
# traveler per day.
TRANSPORT_PER_PERSON_PER_DAY = 300.0


def estimate_food_cost(travelers: int, duration_days: int, hotel_tier: HotelTier) -> float:
    daily_rate = FOOD_PER_PERSON_PER_DAY.get(hotel_tier, FOOD_PER_PERSON_PER_DAY[HotelTier.MIDRANGE])
    return round(daily_rate * travelers * duration_days, 2)


def estimate_activities_cost(
    places: list[Place],
    travelers: int,
    duration_days: int,
    max_daily_activities: int,
) -> float:
    """
    Averages the estimated per-person cost across searched attractions
    (using real price_level where SerpApi provided it, a default
    otherwise), then multiplies by how many attractions the trip's pace
    is expected to actually visit.
    """
    attractions = [p for p in places if p.category == PlaceCategory.ATTRACTION]
    if not attractions:
        return 0.0

    per_person_costs = [
        PRICE_LEVEL_TO_ACTIVITY_COST.get(p.price_level, DEFAULT_ACTIVITY_COST_PER_PERSON)
        for p in attractions
    ]
    average_cost = sum(per_person_costs) / len(per_person_costs)

    expected_visits_per_day = min(
        max_daily_activities, max(1, len(attractions) // max(duration_days, 1))
    )
    total_visits = expected_visits_per_day * duration_days

    return round(average_cost * total_visits * travelers, 2)


def estimate_transport_cost(travelers: int, duration_days: int) -> float:
    return round(TRANSPORT_PER_PERSON_PER_DAY * travelers * duration_days, 2)