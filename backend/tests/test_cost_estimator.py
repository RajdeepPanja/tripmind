from models.common import GeoPoint, SourceRef
from models.enums import DataSource, HotelTier, PlaceCategory
from models.place import Place
from services.cost_estimator import (
    estimate_activities_cost,
    estimate_food_cost,
    estimate_transport_cost,
)


def make_attraction(id_, price_level=None):
    return Place(
        id=id_,
        name=f"Attraction {id_}",
        category=PlaceCategory.ATTRACTION,
        price_level=price_level,
        location=GeoPoint(latitude=26.9, longitude=75.8),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS),
    )


def test_estimate_food_cost_budget_tier():
    assert estimate_food_cost(travelers=2, duration_days=4, hotel_tier=HotelTier.BUDGET) == 6400.0


def test_estimate_food_cost_luxury_tier():
    assert estimate_food_cost(travelers=2, duration_days=4, hotel_tier=HotelTier.LUXURY) == 24000.0


def test_estimate_activities_cost_no_attractions_returns_zero():
    assert estimate_activities_cost([], travelers=2, duration_days=4, max_daily_activities=5) == 0.0


def test_estimate_activities_cost_uses_price_level():
    attractions = [make_attraction("a1", "$$"), make_attraction("a2", "$$")]
    cost = estimate_activities_cost(attractions, travelers=1, duration_days=1, max_daily_activities=5)
    # average per-person cost = 500; expected_visits_per_day = min(5, max(1, 2//1)) = 2
    assert cost == 1000.0


def test_estimate_activities_cost_uses_default_when_no_price_level():
    attractions = [make_attraction("a1", None)]
    cost = estimate_activities_cost(attractions, travelers=1, duration_days=1, max_daily_activities=5)
    assert cost == 400.0  # DEFAULT_ACTIVITY_COST_PER_PERSON


def test_estimate_transport_cost_basic():
    assert estimate_transport_cost(travelers=2, duration_days=4) == 2400.0