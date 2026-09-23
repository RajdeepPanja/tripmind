"""
Tests for deterministic constraint checking.
"""
from datetime import date

from models.budget import BudgetBreakdown
from models.constraints import TripConstraints
from models.itinerary import DailyActivity, DayPlan, Itinerary
from services.constraint_checker import (
    check_budget_constraint,
    check_hotel_changes_constraint,
    check_pace_constraint,
    check_unsourced_claims,
    run_all_constraint_checks,
)


def make_constraints(**overrides):
    defaults = dict(
        max_budget_amount=50000.0,
        max_hotel_changes=1,
        max_daily_travel_minutes=120,
        max_daily_activities=3,
    )
    defaults.update(overrides)
    return TripConstraints(**defaults)


def make_breakdown(remaining=1000.0):
    return BudgetBreakdown(
        total_budget={"amount": 50000.0, "currency": "INR"},
        line_items=[],
        spent={"amount": 50000.0 - remaining, "currency": "INR"},
        remaining={"amount": remaining, "currency": "INR"},
    )


def test_check_budget_constraint_flags_over_budget():
    breakdown = make_breakdown(remaining=-500.0)
    issue = check_budget_constraint(breakdown)
    assert issue is not None
    assert issue.code == "OVER_BUDGET"


def test_check_budget_constraint_passes_when_within_budget():
    breakdown = make_breakdown(remaining=500.0)
    issue = check_budget_constraint(breakdown)
    assert issue is None


def test_check_pace_constraint_flags_too_many_activities():
    constraints = make_constraints(max_daily_activities=2)
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[
                    DailyActivity(time="09:00", title="A", duration_minutes=60),
                    DailyActivity(time="11:00", title="B", duration_minutes=60),
                    DailyActivity(time="13:00", title="C", duration_minutes=60),
                ],
                estimated_travel_minutes=30,
            )
        ]
    )
    issues = check_pace_constraint(itinerary, constraints)
    assert any(i.code == "PACE_VIOLATION" for i in issues)


def test_check_pace_constraint_flags_travel_time_violation():
    constraints = make_constraints(max_daily_travel_minutes=60)
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[],
                estimated_travel_minutes=200,
            )
        ]
    )
    issues = check_pace_constraint(itinerary, constraints)
    assert any(i.code == "TRAVEL_TIME_VIOLATION" for i in issues)


def test_check_hotel_changes_constraint_flags_too_many_changes():
    constraints = make_constraints(max_hotel_changes=1)
    itinerary = Itinerary(
        days=[
            DayPlan(day_number=1, date=date(2026, 12, 1), hotel_id="hotel_a"),
            DayPlan(day_number=2, date=date(2026, 12, 2), hotel_id="hotel_b"),
            DayPlan(day_number=3, date=date(2026, 12, 3), hotel_id="hotel_c"),
        ]
    )
    issue = check_hotel_changes_constraint(itinerary, constraints)
    assert issue is not None
    assert issue.code == "TOO_MANY_HOTEL_CHANGES"


def test_check_hotel_changes_constraint_passes_within_limit():
    constraints = make_constraints(max_hotel_changes=2)
    itinerary = Itinerary(
        days=[
            DayPlan(day_number=1, date=date(2026, 12, 1), hotel_id="hotel_a"),
            DayPlan(day_number=2, date=date(2026, 12, 2), hotel_id="hotel_a"),
        ]
    )
    issue = check_hotel_changes_constraint(itinerary, constraints)
    assert issue is None


def test_check_unsourced_claims_flags_missing_place_id():
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[
                    DailyActivity(time="09:00", title="Mystery stop", duration_minutes=60)
                ],
            )
        ]
    )
    issues = check_unsourced_claims(itinerary)
    assert len(issues) == 1
    assert issues[0].code == "UNSOURCED_CLAIM"


def test_run_all_constraint_checks_aggregates_issues():
    constraints = make_constraints(max_daily_activities=1, max_hotel_changes=0)
    breakdown = make_breakdown(remaining=-100.0)
    itinerary = Itinerary(
        days=[
            DayPlan(
                day_number=1,
                date=date(2026, 12, 1),
                activities=[
                    DailyActivity(time="09:00", title="A", duration_minutes=30),
                    DailyActivity(time="10:00", title="B", duration_minutes=30),
                ],
                hotel_id="hotel_a",
            ),
            DayPlan(day_number=2, date=date(2026, 12, 2), hotel_id="hotel_b"),
        ]
    )
    issues = run_all_constraint_checks(itinerary, constraints, breakdown)
    codes = {i.code for i in issues}
    assert "OVER_BUDGET" in codes
    assert "PACE_VIOLATION" in codes
    assert "TOO_MANY_HOTEL_CHANGES" in codes