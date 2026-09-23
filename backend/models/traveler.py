"""
Traveler-facing preference model — distinct from TripRequest so the same
profile shape could later be reused (e.g. saved profiles) without dragging
in trip-specific fields like dates or origin/destination.
"""
from pydantic import BaseModel, Field

from models.enums import HotelTier, TravelStyle


class TravelerProfile(BaseModel):
    interests: list[str] = Field(default_factory=list)
    travel_style: TravelStyle = TravelStyle.BALANCED
    hotel_preference: HotelTier = HotelTier.MIDRANGE
    food_preferences: list[str] = Field(default_factory=list)
    activity_preferences: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    mobility_notes: str | None = None