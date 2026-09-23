"""
Trip Doctor input. `details` is intentionally a loose dict since each
DisruptionType needs different fields (e.g. flight_delay needs
delay_minutes; hotel_unavailable needs a reason) — the Trip Doctor Agent
validates the shape it expects per type rather than this model enforcing
a union of every possible field.
"""
from typing import Any

from pydantic import BaseModel, Field

from models.enums import DisruptionType


class TripDisruption(BaseModel):
    type: DisruptionType
    affected_day: int | None = Field(default=None, ge=1)
    details: dict[str, Any] = Field(default_factory=dict)
    reported_at: str | None = None  # ISO timestamp string, set by caller