"""
Request/response shapes for the standalone agent search endpoints
(/api/search/flights, /api/search/hotels, /api/search/places). Distinct
from TripRequest — these are the simpler, direct inputs each agent needs
for independent testing outside the full trip-planning flow.
"""
from datetime import date as date_type

from pydantic import BaseModel, Field, model_validator

from models.flight import FlightOption
from models.hotel import HotelOption
from models.place import Place


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date_type
    return_date: date_type | None = None
    travelers: int = Field(default=1, ge=1)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @model_validator(mode="after")
    def return_after_departure(self) -> "FlightSearchRequest":
        if self.return_date and self.return_date <= self.departure_date:
            raise ValueError("return_date must be after departure_date")
        return self


class FlightSearchResult(BaseModel):
    results: list[FlightOption] = Field(default_factory=list)
    skipped_count: int = 0
    query_used: str | None = None


class HotelSearchRequest(BaseModel):
    destination: str
    check_in_date: date_type
    check_out_date: date_type
    travelers: int = Field(default=1, ge=1)
    rooms: int = Field(default=1, ge=1)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @model_validator(mode="after")
    def checkout_after_checkin(self) -> "HotelSearchRequest":
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must be after check_in_date")
        return self


class HotelSearchResult(BaseModel):
    results: list[HotelOption] = Field(default_factory=list)
    skipped_count: int = 0
    query_used: str | None = None


class PlacesSearchRequest(BaseModel):
    destination: str
    categories: list[str] = Field(default_factory=lambda: ["attractions", "restaurants"])
    max_results_per_category: int = Field(default=10, ge=1, le=20)


class PlacesSearchResult(BaseModel):
    results: list[Place] = Field(default_factory=list)
    skipped_count: int = 0
    queries_used: list[str] = Field(default_factory=list)