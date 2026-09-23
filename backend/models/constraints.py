"""
TripConstraints is the mutable planning target. Optimize actions (e.g.
"make it cheaper") mutate this object, which then drives a partial re-run
of the LangGraph workflow. It intentionally holds only numbers/enums/flags
that a deterministic service can act on — no free text.
"""
from pydantic import BaseModel, Field, model_validator

from models.enums import HotelTier, TravelStyle


class TripConstraints(BaseModel):
    max_budget_amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    pace: TravelStyle = TravelStyle.BALANCED
    hotel_tier: HotelTier = HotelTier.MIDRANGE

    # Weight given to each interest when scoring itinerary candidates.
    # Keys are free-form interest tags (e.g. "history", "food") to stay in
    # sync with TravelerProfile.interests; values should sum to ~1.0 but
    # this is enforced by the scoring service, not here.
    priority_weights: dict[str, float] = Field(default_factory=dict)

    max_hotel_changes: int = Field(default=2, ge=0)
    max_daily_travel_minutes: int = Field(default=180, ge=0)
    max_daily_activities: int = Field(default=6, ge=1)

    @model_validator(mode="after")
    def weights_in_range(self) -> "TripConstraints":
        for tag, weight in self.priority_weights.items():
            if not (0.0 <= weight <= 1.0):
                raise ValueError(
                    f"priority_weights['{tag}']={weight} must be between 0 and 1"
                )
        return self