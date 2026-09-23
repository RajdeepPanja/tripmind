"""
Shared LangGraph state definition.

TripState is a TypedDict, not a Pydantic model — this is a deliberate,
isolated change from the earlier stub. LangGraph needs typed reducers
(Annotated[..., operator.add]) to safely merge updates from concurrent
branches (the parallel flight/hotel/places search fan-out), which is the
standard, safe pattern for this in LangGraph 0.2.x. Nothing in Phase 1-3
depended on this file being a Pydantic model.

Flights/hotels/places are written by three different parallel nodes to
three different keys — no reducer needed there, since LangGraph merges
distinct keys without conflict. `errors` is the one field multiple
concurrent nodes might append to, so it uses an additive reducer to avoid
one branch's error silently overwriting another's.
"""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from models.budget import BudgetBreakdown
from models.constraints import TripConstraints
from models.disruption import TripDisruption
from models.enums import WorkflowStatus
from models.flight import FlightOption
from models.hotel import HotelOption
from models.itinerary import Itinerary
from models.place import Place
from models.route import RoutePlan
from models.trip_request import TripRequest
from models.verification import VerificationResult


class TripState(TypedDict, total=False):
    request: TripRequest
    constraints: TripConstraints

    flights: list[FlightOption]
    hotels: list[HotelOption]
    places: list[Place]

    selected_flight: FlightOption | None
    selected_hotel: HotelOption | None
    selection_reasons: dict[str, str]
    budget_feasible: bool

    budget: BudgetBreakdown | None
    route_plan: RoutePlan | None

    itinerary: Itinerary | None
    verification: VerificationResult | None

    revision_count: int
    max_revisions: int
    revision_feedback: list[str]

    disruption: TripDisruption | None
    errors: Annotated[list[str], operator.add]
    status: WorkflowStatus


def build_initial_state(
    request: TripRequest,
    constraints: TripConstraints,
    max_revisions: int = 2,
) -> TripState:
    """Constructs a clean starting TripState for a new planning run."""
    return TripState(
        request=request,
        constraints=constraints,
        flights=[],
        hotels=[],
        places=[],
        selected_flight=None,
        selected_hotel=None,
        selection_reasons={},
        budget_feasible=True,
        budget=None,
        route_plan=None,
        itinerary=None,
        verification=None,
        revision_count=0,
        max_revisions=max_revisions,
        revision_feedback=[],
        disruption=None,
        errors=[],
        status=WorkflowStatus.PENDING,
    )