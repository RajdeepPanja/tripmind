"""
Route planning models — geographic ordering of places into daily route
segments. Built deterministically by services/route_builder.py using
Haversine distance; no live routing API, no LLM involvement.
"""
from pydantic import BaseModel, Field

from models.common import GeoPoint
from models.enums import TransportMode


class RouteStop(BaseModel):
    place_id: str
    order: int = Field(..., ge=0)
    location: GeoPoint
    distance_from_previous_km: float | None = Field(default=None, ge=0)
    travel_minutes_from_previous: int | None = Field(default=None, ge=0)
    travel_mode_from_previous: TransportMode | None = None


class RouteDay(BaseModel):
    day_number: int = Field(..., ge=1)
    stops: list[RouteStop] = Field(default_factory=list)
    total_distance_km: float = Field(default=0.0, ge=0)
    total_travel_minutes: int = Field(default=0, ge=0)


class RoutePlan(BaseModel):
    days: list[RouteDay] = Field(default_factory=list)
    total_distance_km: float = Field(default=0.0, ge=0)