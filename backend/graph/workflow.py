"""
LangGraph workflow definition for the TripMind planning pipeline:

  validate -> [search_flights || search_hotels || search_places]
    -> select_options -> calculate_budget -> build_route
    -> generate_itinerary -> verify_itinerary
       -> pass: finalize
       -> fail, revisions remaining: prepare_revision -> generate_itinerary (loop)
       -> fail, revisions exhausted: finalize_with_warnings

All client/llm parameters are optional injection points for offline
testing — production calls omit them and each node's underlying agent
falls back to constructing its real client/LLM.
"""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    build_route_node,
    calculate_budget_node,
    fail_gracefully_node,
    finalize_node,
    finalize_with_warnings_node,
    generate_itinerary_node,
    prepare_revision_node,
    search_flights_node,
    search_hotels_node,
    search_places_node,
    select_options,
    validate_request,
    verify_itinerary_node,
)
from graph.state import TripState, build_initial_state
from models.constraints import TripConstraints
from models.enums import WorkflowStatus
from models.trip_request import TripRequest


def _route_after_validation(state: TripState) -> list[str]:
    if state.get("errors"):
        return ["fail_gracefully"]
    return ["search_flights", "search_hotels", "search_places"]


def _route_after_selection(state: TripState) -> str:
    if state.get("status") == WorkflowStatus.FAILED:
        return "fail_gracefully"
    return "calculate_budget"


def _route_after_itinerary_generation(state: TripState) -> str:
    if state.get("status") == WorkflowStatus.FAILED:
        return "fail_gracefully"
    return "verify_itinerary"


def _route_after_verification(state: TripState) -> str:
    verification = state.get("verification")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    if verification and verification.passed:
        return "finalize"
    if revision_count < max_revisions:
        return "prepare_revision"
    return "finalize_with_warnings"


def build_graph(flight_client=None, hotel_client=None, places_client=None, llm=None):
    """
    Compiles the TripMind planning graph. Optional injected clients/llm
    are for offline testing; production code calls build_graph() with no
    arguments and each node constructs its real dependency.
    """
    graph = StateGraph(TripState)

    graph.add_node("validate_request", validate_request)
    graph.add_node("search_flights", partial(search_flights_node, client=flight_client))
    graph.add_node("search_hotels", partial(search_hotels_node, client=hotel_client))
    graph.add_node("search_places", partial(search_places_node, client=places_client))
    graph.add_node("select_options", select_options)
    graph.add_node("calculate_budget", calculate_budget_node)
    graph.add_node("build_route", build_route_node)
    graph.add_node("generate_itinerary", partial(generate_itinerary_node, llm=llm))
    graph.add_node("verify_itinerary", verify_itinerary_node)
    graph.add_node("prepare_revision", prepare_revision_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("finalize_with_warnings", finalize_with_warnings_node)
    graph.add_node("fail_gracefully", fail_gracefully_node)

    graph.add_edge(START, "validate_request")

    graph.add_conditional_edges(
        "validate_request",
        _route_after_validation,
        ["search_flights", "search_hotels", "search_places", "fail_gracefully"],
    )

    graph.add_edge("search_flights", "select_options")
    graph.add_edge("search_hotels", "select_options")
    graph.add_edge("search_places", "select_options")

    graph.add_conditional_edges(
        "select_options",
        _route_after_selection,
        ["calculate_budget", "fail_gracefully"],
    )

    graph.add_edge("calculate_budget", "build_route")
    graph.add_edge("build_route", "generate_itinerary")

    graph.add_conditional_edges(
        "generate_itinerary",
        _route_after_itinerary_generation,
        ["verify_itinerary", "fail_gracefully"],
    )

    graph.add_conditional_edges(
        "verify_itinerary",
        _route_after_verification,
        ["finalize", "prepare_revision", "finalize_with_warnings"],
    )

    graph.add_edge("prepare_revision", "generate_itinerary")

    graph.add_edge("finalize", END)
    graph.add_edge("finalize_with_warnings", END)
    graph.add_edge("fail_gracefully", END)

    return graph.compile()


async def run_trip_planning(
    request: TripRequest,
    constraints: TripConstraints,
    max_revisions: int = 2,
    flight_client=None,
    hotel_client=None,
    places_client=None,
    llm=None,
) -> TripState:
    """Convenience entry point: builds the graph and runs one full trip plan."""
    graph = build_graph(
        flight_client=flight_client,
        hotel_client=hotel_client,
        places_client=places_client,
        llm=llm,
    )
    initial_state = build_initial_state(request, constraints, max_revisions)
    return await graph.ainvoke(initial_state)