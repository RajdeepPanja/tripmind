"""
Verification Agent — 100% deterministic for MVP, per architecture
decision. Wraps services/constraint_checker.py and adds a structural check
that every itinerary activity references a place_id/hotel_id/flight_id
that actually exists in the verified TripState data. No LLM is involved
anywhere in this file.
"""
from models.budget import BudgetBreakdown
from models.constraints import TripConstraints
from models.flight import FlightOption
from models.hotel import HotelOption
from models.itinerary import Itinerary
from models.place import Place
from models.verification import VerificationIssue, VerificationResult
from services.constraint_checker import check_unsourced_claims, run_all_constraint_checks


def _known_ids(
    places: list[Place], hotels: list[HotelOption], flights: list[FlightOption]
) -> set[str]:
    ids = {p.id for p in places}
    ids.update(h.id for h in hotels)
    ids.update(f.id for f in flights)
    return ids


def check_place_ids_exist(
    itinerary: Itinerary,
    places: list[Place],
    hotels: list[HotelOption],
    flights: list[FlightOption],
) -> list[VerificationIssue]:
    """
    Flags any activity whose place_id doesn't match any verified
    place/hotel/flight in TripState — the deeper check flagged as missing
    back in Phase 2, now possible because this layer has the full state.
    """
    known = _known_ids(places, hotels, flights)
    issues: list[VerificationIssue] = []

    for day in itinerary.days:
        for activity in day.activities:
            if activity.place_id is not None and activity.place_id not in known:
                issues.append(
                    VerificationIssue(
                        code="UNKNOWN_PLACE_ID",
                        message=(
                            f"Activity '{activity.title}' on day "
                            f"{day.day_number} references place_id "
                            f"'{activity.place_id}', which does not exist "
                            f"in verified trip data"
                        ),
                        day_number=day.day_number,
                        activity_title=activity.title,
                    )
                )
    return issues


def run_verification(
    itinerary: Itinerary,
    constraints: TripConstraints,
    breakdown: BudgetBreakdown,
    places: list[Place],
    hotels: list[HotelOption],
    flights: list[FlightOption],
) -> VerificationResult:
    """
    Runs every deterministic check and aggregates results. `violations`
    covers budget/pace/hotel-change rule breaks; `unsupported_claims`
    covers structurally unsourced or unknown-reference activities.
    """
    violations = run_all_constraint_checks(itinerary, constraints, breakdown)

    unsupported_claims: list[VerificationIssue] = []
    unsupported_claims.extend(check_place_ids_exist(itinerary, places, hotels, flights))
    unsupported_claims.extend(check_unsourced_claims(itinerary))

    passed = not violations and not unsupported_claims

    return VerificationResult(
        passed=passed,
        violations=violations,
        unsupported_claims=unsupported_claims,
    )