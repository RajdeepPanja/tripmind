"""
Flight option model. Every field describing price, timing, or availability
must be sourced from SerpApi (google_flights engine) — never fabricated.
"""
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from models.common import Money, SourceRef
from models.enums import DataSource


class FlightOption(BaseModel):
    id: str
    airline: str
    flight_number: str | None = None
    origin_airport: str
    destination_airport: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int = Field(..., ge=0)
    stops: int = Field(default=0, ge=0)
    price: Money
    source_ref: SourceRef

    @model_validator(mode="after")
    def arrival_after_departure(self) -> "FlightOption":
        if self.arrival_time <= self.departure_time:
            raise ValueError("arrival_time must be after departure_time")
        return self

    @model_validator(mode="after")
    def must_be_live_sourced(self) -> "FlightOption":
        if self.source_ref.source == DataSource.LLM_GENERATED:
            raise ValueError(
                "FlightOption price/availability cannot be LLM_GENERATED — "
                "must come from SerpApi google_flights"
            )
        return self