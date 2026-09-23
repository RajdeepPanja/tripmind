"""
Shared enums used across TripMind's domain models.
Centralized here so agents, services, and the API layer all reference the
same set of allowed values.
"""
from enum import Enum


class TravelStyle(str, Enum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"


class HotelTier(str, Enum):
    BUDGET = "budget"
    MIDRANGE = "midrange"
    LUXURY = "luxury"


class PlaceCategory(str, Enum):
    ATTRACTION = "attraction"
    RESTAURANT = "restaurant"
    ACTIVITY = "activity"


class TransportMode(str, Enum):
    WALK = "walk"
    TAXI = "taxi"
    RIDESHARE = "rideshare"
    PUBLIC_TRANSPORT = "public_transport"
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"


class BudgetCategory(str, Enum):
    FLIGHTS = "flights"
    HOTELS = "hotels"
    FOOD = "food"
    ACTIVITIES = "activities"
    TRANSPORT = "transport"
    BUFFER = "buffer"


class OptimizationAction(str, Enum):
    MAKE_CHEAPER = "make_cheaper"
    MORE_RELAXED = "more_relaxed"
    MORE_ADVENTURE = "more_adventure"
    MORE_FOOD = "more_food"
    MORE_LUXURY = "more_luxury"
    FEWER_HOTEL_CHANGES = "fewer_hotel_changes"
    LESS_TRAVEL_TIME = "less_travel_time"


class DisruptionType(str, Enum):
    FLIGHT_DELAY = "flight_delay"
    FLIGHT_CANCELLATION = "flight_cancellation"
    HOTEL_UNAVAILABLE = "hotel_unavailable"
    ATTRACTION_CLOSED = "attraction_closed"
    SKIP_ACTIVITY = "skip_activity"
    ADD_ACTIVITY = "add_activity"


class DataSource(str, Enum):
    """
    Where a piece of data came from. Every fact with a monetary value or a
    real-world claim (price, availability, hours) must carry one of the
    SERPAPI_* sources — never LLM_GENERATED. This is what the Verification
    Agent checks against later.
    """
    SERPAPI_GOOGLE_FLIGHTS = "serpapi_google_flights"
    SERPAPI_GOOGLE_HOTELS = "serpapi_google_hotels"
    SERPAPI_GOOGLE_MAPS = "serpapi_google_maps"
    SERPAPI_GOOGLE_SEARCH = "serpapi_google_search"
    SERPAPI_GOOGLE_NEWS = "serpapi_google_news"
    COMPUTED = "computed"          # deterministic service output
    LLM_GENERATED = "llm_generated"  # reasoning/explanation text only, never a fact
    USER_PROVIDED = "user_provided"


class WorkflowStatus(str, Enum):
    """
    Overall status of a trip-planning run through the LangGraph workflow.
    Surfaced to the frontend so the loading screen can show real progress
    instead of a generic spinner, and so the final API response is honest
    about whether an itinerary is fully verified or a best-effort fallback.
    """
    PENDING = "pending"
    SEARCHING = "searching"
    PLANNING = "planning"
    VERIFYING = "verifying"
    REVISING = "revising"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"