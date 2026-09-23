"""
Itinerary structure: TravelLeg (movement between two points),
DailyActivity (a single scheduled item), DayPlan (one day), and Itinerary
(the whole trip). Built by the Itinerary Agent from verified Flight/Hotel/
Place data only — `generated_reasoning` is the one field allowed to hold
free-text LLM output, and it must never carry numeric facts that aren't
duplicated elsewhere with a source.
"""
from datetime import date as date_type

from pydantic import BaseModel, Field

from models.common import Money
from models.enums import TransportMode


class TravelLeg(BaseModel):
    from_place_id: str | None = None
    to_place_id: str | None = None
    mode: TransportMode
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=0)
    estimated_cost: Money | None = None


class DailyActivity(BaseModel):
    time: str  # "HH:MM" — kept as string for simple frontend rendering
    place_id: str | None = None  # references a Place.id / Restaurant.id / HotelOption.id
    title: str
    duration_minutes: int = Field(..., ge=0)
    notes: str | None = None
    travel_to_next: TravelLeg | None = None


class DayPlan(BaseModel):
    day_number: int = Field(..., ge=1)
    date: date_type
    activities: list[DailyActivity] = Field(default_factory=list)
    estimated_travel_minutes: int = Field(default=0, ge=0)
    hotel_id: str | None = None


class Itinerary(BaseModel):
    days: list[DayPlan] = Field(default_factory=list)
    generated_reasoning: str | None = None