"""
Small shared value objects reused across multiple domain models.
"""
from pydantic import BaseModel, Field, field_validator

from models.enums import DataSource


class GeoPoint(BaseModel):
    """A latitude/longitude pair. Used by hotels, places, and route legs."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @field_validator("latitude", "longitude")
    @classmethod
    def not_nan(cls, v: float) -> float:
        if v != v:  # NaN check without importing math
            raise ValueError("Coordinate cannot be NaN")
        return v


class Money(BaseModel):
    """
    Explicit monetary value. Always pair an amount with its currency —
    never pass around a bare float for money anywhere in the system.
    """

    amount: float = Field(..., ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

class SignedMoney(BaseModel):
    """
    Like Money, but allows negative amounts. Used specifically for values
    that can legitimately go negative — e.g. BudgetBreakdown.remaining when
    a trip is over budget. Do not use this for prices; use Money instead.
    """

    amount: float
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

class SourceRef(BaseModel):
    """
    Provenance record for a single retrieved or computed fact. Every
    FlightOption, HotelOption, and Place should carry one of these, and the
    Verification Agent treats any fact without a valid SourceRef as
    unsupported.
    """

    source: DataSource
    query: str | None = None
    retrieved_at: str | None = None  # ISO timestamp string, set by caller
    raw_result_id: str | None = None  # e.g. SerpApi result index/id for traceability