"""
Distance and rough travel-time estimation using the Haversine formula.

No live routing API is used (per architecture doc — real routing is
overkill for a hackathon). Distances are straight-line ("as the crow
flies"), and travel time is estimated with a fixed average speed per
transport mode. Callers should treat these as estimates, not ground truth,
and the frontend/itinerary should label them as such.
"""
import math

from models.common import GeoPoint
from models.enums import TransportMode

# Average speed in km/h per mode — deliberately simple, fixed assumptions.
AVERAGE_SPEED_KMH: dict[TransportMode, float] = {
    TransportMode.WALK: 4.5,
    TransportMode.TAXI: 30.0,
    TransportMode.RIDESHARE: 30.0,
    TransportMode.PUBLIC_TRANSPORT: 22.0,
    TransportMode.BUS: 25.0,
    TransportMode.TRAIN: 60.0,
    TransportMode.FLIGHT: 700.0,
}

EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(point_a: GeoPoint, point_b: GeoPoint) -> float:
    """
    Great-circle distance between two GeoPoints, in kilometers.
    """
    lat1, lon1 = math.radians(point_a.latitude), math.radians(point_a.longitude)
    lat2, lon2 = math.radians(point_b.latitude), math.radians(point_b.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return round(EARTH_RADIUS_KM * c, 3)


def estimate_travel_minutes(
    point_a: GeoPoint,
    point_b: GeoPoint,
    mode: TransportMode = TransportMode.TAXI,
) -> int:
    """
    Rough travel time in minutes between two points for a given mode,
    based on straight-line distance and a fixed average speed. Includes no
    traffic, terrain, or routing detail — clearly an estimate.
    """
    distance_km = haversine_distance_km(point_a, point_b)
    speed_kmh = AVERAGE_SPEED_KMH.get(mode, AVERAGE_SPEED_KMH[TransportMode.TAXI])

    if speed_kmh <= 0:
        raise ValueError(f"Invalid average speed for mode {mode}: {speed_kmh}")

    hours = distance_km / speed_kmh
    minutes = hours * 60

    # Small fixed overhead for boarding/waiting on non-walking modes,
    # so estimates aren't unrealistically optimistic for short hops.
    overhead_minutes = 0 if mode == TransportMode.WALK else 5

    return max(1, round(minutes) + overhead_minutes)


def total_route_distance_km(points: list[GeoPoint]) -> float:
    """
    Sum of consecutive Haversine distances across an ordered list of
    points — e.g. the total distance covered by a day's stops in order.
    """
    if len(points) < 2:
        return 0.0

    total = 0.0
    for i in range(len(points) - 1):
        total += haversine_distance_km(points[i], points[i + 1])

    return round(total, 3)