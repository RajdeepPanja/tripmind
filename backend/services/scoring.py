"""
Deterministic scoring for comparing/ranking candidate options (flights,
hotels, or full itinerary candidates) against TripConstraints and
TravelerProfile priority weights. Used by the Optimize workflow so
"make it cheaper" etc. re-rank real options rather than asking the LLM to
rewrite text.
"""
from models.constraints import TripConstraints
from models.flight import FlightOption
from models.hotel import HotelOption
from models.place import Place


def score_flight(flight: FlightOption, constraints: TripConstraints) -> float:
    """
    Lower price and fewer stops score higher. Returns a 0-100 score;
    relative ranking matters more than absolute value.
    """
    price_score = max(0.0, 100.0 - (flight.price.amount / max(constraints.max_budget_amount, 1)) * 100)
    stops_penalty = flight.stops * 15.0
    duration_penalty = min(30.0, flight.duration_minutes / 60.0)

    score = price_score - stops_penalty - duration_penalty
    return round(max(0.0, min(100.0, score)), 2)


def score_hotel(hotel: HotelOption, constraints: TripConstraints) -> float:
    """
    Balances price against rating, weighted toward the requested hotel
    tier's typical price band. Simple linear scoring — no ML involved.
    """
    rating_score = (hotel.rating or 3.0) * 20.0  # 0-100 scale from a 0-5 rating

    tier_price_targets = {
        "budget": 2000.0,
        "midrange": 6000.0,
        "luxury": 15000.0,
    }
    target = tier_price_targets.get(constraints.hotel_tier.value, 6000.0)
    price_diff_ratio = abs(hotel.price_per_night.amount - target) / target
    price_fit_score = max(0.0, 100.0 - price_diff_ratio * 100.0)

    score = (rating_score * 0.5) + (price_fit_score * 0.5)
    return round(max(0.0, min(100.0, score)), 2)


def score_place_against_interests(
    place: Place, constraints: TripConstraints
) -> float:
    """
    Scores a place by how well its category/name overlaps with the
    traveler's priority_weights (e.g. {"history": 0.4, "food": 0.3}).
    This is a simple keyword-overlap heuristic, not semantic matching —
    appropriate for a hackathon MVP.
    """
    if not constraints.priority_weights:
        return (place.rating or 3.0) * 20.0

    name_lower = place.name.lower()
    matched_weight = 0.0
    for tag, weight in constraints.priority_weights.items():
        if tag.lower() in name_lower or tag.lower() == place.category.value:
            matched_weight += weight

    interest_score = min(100.0, matched_weight * 100.0)
    rating_score = (place.rating or 3.0) * 20.0

    score = (interest_score * 0.6) + (rating_score * 0.4)
    return round(max(0.0, min(100.0, score)), 2)


def rank_flights(
    flights: list[FlightOption], constraints: TripConstraints
) -> list[FlightOption]:
    return sorted(
        flights, key=lambda f: score_flight(f, constraints), reverse=True
    )


def rank_hotels(
    hotels: list[HotelOption], constraints: TripConstraints
) -> list[HotelOption]:
    return sorted(
        hotels, key=lambda h: score_hotel(h, constraints), reverse=True
    )


def rank_places(
    places: list[Place], constraints: TripConstraints
) -> list[Place]:
    return sorted(
        places,
        key=lambda p: score_place_against_interests(p, constraints),
        reverse=True,
    )