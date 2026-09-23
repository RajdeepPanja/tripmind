from datetime import date

from agents.verification_agent import run_verification
from models.budget import BudgetBreakdown
from models.common import GeoPoint, SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource, PlaceCategory
from models.itinerary import DailyActivity, DayPlan, Itinerary
from models.place import Place


def make_place(id_="p1"):
    return Place(
        id=id_,
        name="Test Place",
        category=PlaceCategory.ATTRACTION,
        location=GeoPoint(latitude=26.9, longitude=75.8),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS),
    )


def make_breakdown(remaining=1000.0):
    return BudgetBreakdown(
        total_budget={"amount": 50000, "currency": "INR"},
        line_items=[],
        spent={"amount": 50000 - remaining, "currency": "INR"},
        remaining={"amount": remaining, "currency": "INR"},
    )


def make_constraints(**overrides):
    defaults = dict(
        max_budget_amount=50000,
        max_daily_activities=5,
        max_daily_travel_minutes=300,
        max_hotel_changes=2,
    )
    defaults.update(overrides)
    return TripConstraints(**defaults)


def test_run_verification_passes_clean_itinerary():
    place = make_place("p1")
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[DailyActivity(time="09:00", place_id="p1", title="Visit", duration_minutes=60)],
            )
        ]
    )
    result = run_verification(itinerary, make_constraints(), make_breakdown(), [place], [], [])
    assert result.passed is True
    assert result.violations == []
    assert result.unsupported_claims == []


def test_run_verification_flags_unknown_place_id():
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[DailyActivity(time="09:00", place_id="ghost", title="Visit", duration_minutes=60)],
            )
        ]
    )
    result = run_verification(itinerary, make_constraints(), make_breakdown(), [], [], [])
    assert result.passed is False
    assert any(i.code == "UNKNOWN_PLACE_ID" for i in result.unsupported_claims)


def test_run_verification_flags_over_budget():
    place = make_place("p1")
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[DailyActivity(time="09:00", place_id="p1", title="Visit", duration_minutes=60)],
            )
        ]
    )
    result = run_verification(
        itinerary, make_constraints(), make_breakdown(remaining=-500.0), [place], [], []
    )
    assert result.passed is False
    assert any(i.code == "OVER_BUDGET" for i in result.violations)


def test_run_verification_flags_pace_violation():
    place = make_place("p1")
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[
                    DailyActivity(time="09:00", place_id="p1", title="A", duration_minutes=30),
                    DailyActivity(time="10:00", place_id="p1", title="B", duration_minutes=30),
                ],
            )
        ]
    )
    result = run_verification(
        itinerary, make_constraints(max_daily_activities=1), make_breakdown(), [place], [], []
    )
    assert result.passed is False
    assert any(i.code == "PACE_VIOLATION" for i in result.violations)


def test_run_verification_flags_missing_place_id_activity():
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[DailyActivity(time="09:00", place_id=None, title="Mystery stop", duration_minutes=60)],
            )
        ]
    )
    result = run_verification(itinerary, make_constraints(), make_breakdown(), [], [], [])
    assert result.passed is False
    assert any(i.code == "UNSOURCED_CLAIM" for i in result.unsupported_claims)