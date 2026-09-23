"""
Derives default TripConstraints from a TripRequest's stated budget and
traveler profile — used by POST /api/trips so the frontend only has to
submit a TripRequest, not construct TripConstraints by hand. Pure
arithmetic/mapping, no LLM, consistent with the rest of services/.
"""
from models.constraints import TripConstraints
from models.trip_request import TripRequest


def build_default_constraints(request: TripRequest) -> TripConstraints:
    max_budget_amount = request.budget.total.amount
    if request.budget.per_person:
        max_budget_amount = round(max_budget_amount * request.travelers, 2)

    interests = request.profile.interests
    priority_weights = (
        {tag: round(1.0 / len(interests), 3) for tag in interests}
        if interests
        else {}
    )

    return TripConstraints(
        max_budget_amount=max_budget_amount,
        pace=request.profile.travel_style,
        hotel_tier=request.profile.hotel_preference,
        priority_weights=priority_weights,
    )