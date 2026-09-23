"""
Hotel option model. Same sourcing rule as flights: price/availability must
trace back to SerpApi (google_hotels engine), never invented.
"""
from pydantic import BaseModel, Field, model_validator

from models.common import GeoPoint, Money, SourceRef
from models.enums import DataSource


class HotelOption(BaseModel):
    id: str
    name: str
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    price_per_night: Money
    total_price: Money
    nights: int = Field(..., ge=1)
    location: GeoPoint
    amenities: list[str] = Field(default_factory=list)
    source_ref: SourceRef

    @model_validator(mode="after")
    def total_matches_nightly_rate(self) -> "HotelOption":
        if self.price_per_night.currency != self.total_price.currency:
            raise ValueError(
                "price_per_night and total_price must use the same currency"
            )
        expected = round(self.price_per_night.amount * self.nights, 2)
        actual = round(self.total_price.amount, 2)
        # Allow small rounding/tax variance from the live source rather than
        # silently recomputing — flag anything wildly inconsistent instead.
        if abs(expected - actual) > max(1.0, expected * 0.15):
            raise ValueError(
                f"total_price ({actual}) is inconsistent with "
                f"price_per_night * nights ({expected}); check the source data"
            )
        return self

    @model_validator(mode="after")
    def must_be_live_sourced(self) -> "HotelOption":
        if self.source_ref.source == DataSource.LLM_GENERATED:
            raise ValueError(
                "HotelOption price/availability cannot be LLM_GENERATED — "
                "must come from SerpApi google_hotels"
            )
        return self