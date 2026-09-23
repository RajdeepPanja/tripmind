"""
Deterministic route-building service.

Distributes verified Place objects across the trip while respecting:
- maximum daily activities
- maximum daily travel time

Uses Haversine distance + fixed travel-time estimates.
No live routing API and no LLM are used.
"""

from models.common import GeoPoint
from models.constraints import TripConstraints
from models.enums import TransportMode
from models.hotel import HotelOption
from models.place import Place
from models.route import RouteDay, RoutePlan, RouteStop
from services.distance_calculator import (
    estimate_travel_minutes,
    haversine_distance_km,
)


def _nearest_neighbor_order(
    start: GeoPoint,
    places: list[Place],
) -> list[Place]:
    """Greedy nearest-neighbor ordering starting from start."""
    remaining = list(places)
    ordered: list[Place] = []
    current = start

    while remaining:
        nearest = min(
            remaining,
            key=lambda p: haversine_distance_km(current, p.location),
        )
        ordered.append(nearest)
        remaining.remove(nearest)
        current = nearest.location

    return ordered


def _travel_minutes(
    start: GeoPoint,
    place: Place,
) -> int:
    """Estimate taxi travel time from start to place."""
    return estimate_travel_minutes(
        start,
        place.location,
        TransportMode.TAXI,
    )


def _build_day(
    start_point: GeoPoint,
    candidates: list[Place],
    constraints: TripConstraints,
) -> tuple[list[Place], int, float]:
    """
    Build one geographically compact day.

    A place is added only if doing so keeps both:
    - activity count <= max_daily_activities
    - travel time <= max_daily_travel_minutes

    Among feasible candidates, choose the nearest one.
    """

    selected: list[Place] = []
    remaining = list(candidates)

    current_point = start_point
    total_minutes = 0
    total_distance = 0.0

    while remaining:
        if len(selected) >= constraints.max_daily_activities:
            break

        feasible: list[tuple[Place, int, float]] = []

        for place in remaining:
            distance = haversine_distance_km(
                current_point,
                place.location,
            )

            minutes = estimate_travel_minutes(
                current_point,
                place.location,
                TransportMode.TAXI,
            )

            projected_minutes = total_minutes + minutes

            if projected_minutes <= constraints.max_daily_travel_minutes:
                feasible.append(
                    (place, minutes, distance)
                )

        if not feasible:
            break

        # Pick the closest feasible place.
        next_place, minutes, distance = min(
            feasible,
            key=lambda item: item[2],
        )

        selected.append(next_place)
        remaining.remove(next_place)

        total_minutes += minutes
        total_distance += distance
        current_point = next_place.location

    return selected, total_minutes, total_distance


def build_route_plan(
    places: list[Place],
    hotel: HotelOption | None,
    duration_days: int,
    constraints: TripConstraints,
) -> RoutePlan:
    """
    Build a daily route while respecting the configured travel limit.

    Places that cannot fit within the daily travel/activity constraints
    are left unscheduled rather than creating an invalid route.

    The itinerary agent receives only the places selected by this route
    plan, so the final itinerary cannot intentionally exceed the route
    constraints.
    """

    if not places or duration_days <= 0:
        return RoutePlan(
            days=[],
            total_distance_km=0.0,
        )

    start_point = (
        hotel.location
        if hotel
        else places[0].location
    )

    remaining_places = list(places)

    days: list[RouteDay] = []
    grand_total_distance = 0.0

    for day_number in range(1, duration_days + 1):
        if not remaining_places:
            days.append(
                RouteDay(
                    day_number=day_number,
                    stops=[],
                    total_distance_km=0.0,
                    total_travel_minutes=0,
                )
            )
            continue

        selected, day_minutes, day_distance = _build_day(
            start_point=start_point,
            candidates=remaining_places,
            constraints=constraints,
        )

        # Safety fallback: if even the nearest place cannot fit within
        # the daily travel limit, leave the day empty rather than
        # generating an invalid route.
        if not selected:
            days.append(
                RouteDay(
                    day_number=day_number,
                    stops=[],
                    total_distance_km=0.0,
                    total_travel_minutes=0,
                )
            )
            continue

        ordered = _nearest_neighbor_order(
            start_point,
            selected,
        )

        stops: list[RouteStop] = []

        previous_point = start_point
        actual_day_distance = 0.0
        actual_day_minutes = 0

        for order, place in enumerate(ordered):
            distance = haversine_distance_km(
                previous_point,
                place.location,
            )

            minutes = estimate_travel_minutes(
                previous_point,
                place.location,
                TransportMode.TAXI,
            )

            stops.append(
                RouteStop(
                    place_id=place.id,
                    order=order,
                    location=place.location,
                    distance_from_previous_km=distance,
                    travel_minutes_from_previous=minutes,
                    travel_mode_from_previous=TransportMode.TAXI,
                )
            )

            actual_day_distance += distance
            actual_day_minutes += minutes
            previous_point = place.location

        days.append(
            RouteDay(
                day_number=day_number,
                stops=stops,
                total_distance_km=round(
                    actual_day_distance,
                    3,
                ),
                total_travel_minutes=actual_day_minutes,
            )
        )

        grand_total_distance += actual_day_distance

        for place in selected:
            if place in remaining_places:
                remaining_places.remove(place)

    return RoutePlan(
        days=days,
        total_distance_km=round(
            grand_total_distance,
            3,
        ),
    )