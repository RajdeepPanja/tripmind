"""
Place model covers both attractions and restaurants (distinguished by
`category`), plus a thin Restaurant subclass for restaurant-specific
fields. Kept in one file since they share nearly all fields.
"""
from pydantic import BaseModel, Field, model_validator

from models.common import GeoPoint, SourceRef
from models.enums import DataSource, PlaceCategory


class Place(BaseModel):
    id: str
    name: str
    category: PlaceCategory
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    opening_hours: str | None = None
    price_level: str | None = None  # e.g. "$", "$$", "$$$" as returned by SerpApi
    location: GeoPoint
    address: str | None = None
    typical_visit_minutes: int | None = Field(default=None, ge=0)
    source_ref: SourceRef

    @model_validator(mode="after")
    def must_be_live_sourced(self) -> "Place":
        if self.source_ref.source == DataSource.LLM_GENERATED:
            raise ValueError(
                "Place data cannot be LLM_GENERATED — must come from "
                "SerpApi google_maps"
            )
        return self


class Restaurant(Place):
    """Restaurant-specific extension of Place."""

    category: PlaceCategory = PlaceCategory.RESTAURANT
    cuisine_types: list[str] = Field(default_factory=list)
    accepts_reservations: bool | None = None