"""
API response model for POST /api/trips.
"""
from pydantic import BaseModel, Field

from models.budget import BudgetBreakdown
from models.enums import WorkflowStatus
from models.flight import FlightOption
from models.hotel import HotelOption
from models.itinerary import Itinerary
from models.route import RoutePlan
from models.verification import VerificationResult


class SourceCounts(BaseModel):
    flights_considered: int = 0
    hotels_considered: int = 0
    places_considered: int = 0


class TripPlanResponse(BaseModel):
    trip_id: str
    status: WorkflowStatus

    itinerary: Itinerary | None = None
    budget: BudgetBreakdown | None = None
    route_plan: RoutePlan | None = None
    verification: VerificationResult | None = None

    selected_flight: FlightOption | None = None
    selected_hotel: HotelOption | None = None
    selected_flight_id: str | None = None
    selected_hotel_id: str | None = None
    selection_reasons: dict[str, str] = Field(default_factory=dict)
    budget_feasible: bool = True

    revision_count: int = 0
    errors: list[str] = Field(default_factory=list)

    sources: SourceCounts = Field(default_factory=SourceCounts)