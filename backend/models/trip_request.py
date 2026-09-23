"""
TripRequest is the top-level input the user submits from the trip
configuration screen. TripState (in graph/state.py) will wrap this plus
everything the graph accumulates during planning.
"""
from datetime import date as date_type

from pydantic import BaseModel, Field, model_validator

from models.budget import Budget
from models.traveler import TravelerProfile


class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: date_type
    end_date: date_type
    travelers: int = Field(..., ge=1)
    budget: Budget
    profile: TravelerProfile

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "TripRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days