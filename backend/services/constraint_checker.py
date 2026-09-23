"""
Deterministic constraint checking against TripConstraints. Used by the
Verification Agent to produce hard, reproducible violations rather than
asking an LLM to judge "does this fit the budget/pace?".
"""
from models.budget import BudgetBreakdown
from models.constraints import TripConstraints
from models.itinerary import Itinerary
from models.verification import VerificationIssue


def check_budget_constraint(breakdown: BudgetBreakdown) -> VerificationIssue | None:
    if breakdown.remaining.amount < 0:
        return VerificationIssue(
            code="OVER_BUDGET",
            message=(
                f"Trip exceeds budget by "
                f"{abs(breakdown.remaining.amount)} {breakdown.remaining.currency}"
            ),
        )
    return None


def check_pace_constraint(
    itinerary: Itinerary, constraints: TripConstraints
) -> list[VerificationIssue]:
    issues: list[VerificationIssue] = []
    for day in itinerary.days:
        if len(day.activities) > constraints.max_daily_activities:
            issues.append(
                VerificationIssue(
                    code="PACE_VIOLATION",
                    message=(
                        f"Day {day.day_number} has {len(day.activities)} activities, "
                        f"exceeding max_daily_activities="
                        f"{constraints.max_daily_activities}"
                    ),
                    day_number=day.day_number,
                )
            )
        if day.estimated_travel_minutes > constraints.max_daily_travel_minutes:
            issues.append(
                VerificationIssue(
                    code="TRAVEL_TIME_VIOLATION",
                    message=(
                        f"Day {day.day_number} has "
                        f"{day.estimated_travel_minutes} minutes of travel, "
                        f"exceeding max_daily_travel_minutes="
                        f"{constraints.max_daily_travel_minutes}"
                    ),
                    day_number=day.day_number,
                )
            )
    return issues


def check_hotel_changes_constraint(
    itinerary: Itinerary, constraints: TripConstraints
) -> VerificationIssue | None:
    hotel_sequence = [day.hotel_id for day in itinerary.days if day.hotel_id]
    changes = sum(
        1
        for i in range(1, len(hotel_sequence))
        if hotel_sequence[i] != hotel_sequence[i - 1]
    )
    if changes > constraints.max_hotel_changes:
        return VerificationIssue(
            code="TOO_MANY_HOTEL_CHANGES",
            message=(
                f"Itinerary has {changes} hotel changes, exceeding "
                f"max_hotel_changes={constraints.max_hotel_changes}"
            ),
        )
    return None


def check_unsourced_claims(itinerary: Itinerary) -> list[VerificationIssue]:
    """
    Flags any activity that references no place_id at all — a bare
    free-text activity with no traceable source. This is a structural
    check; the deeper "does place_id actually exist in verified data"
    check is done by the Verification Agent, which has access to the full
    TripState (places/hotels lists) that this function does not.
    """
    issues: list[VerificationIssue] = []
    for day in itinerary.days:
        for activity in day.activities:
            if activity.place_id is None:
                issues.append(
                    VerificationIssue(
                        code="UNSOURCED_CLAIM",
                        message=(
                            f"Activity '{activity.title}' on day "
                            f"{day.day_number} has no place_id reference"
                        ),
                        day_number=day.day_number,
                        activity_title=activity.title,
                    )
                )
    return issues


def run_all_constraint_checks(
    itinerary: Itinerary,
    constraints: TripConstraints,
    breakdown: BudgetBreakdown,
) -> list[VerificationIssue]:
    issues: list[VerificationIssue] = []

    budget_issue = check_budget_constraint(breakdown)
    if budget_issue:
        issues.append(budget_issue)

    issues.extend(check_pace_constraint(itinerary, constraints))

    hotel_issue = check_hotel_changes_constraint(itinerary, constraints)
    if hotel_issue:
        issues.append(hotel_issue)

    return issues