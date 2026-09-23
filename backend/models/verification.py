"""
Output of the Verification Agent. `passed=False` should block an itinerary
from being returned to the user until the itinerary is regenerated or the
issue is surfaced explicitly.
"""
from pydantic import BaseModel, Field


class VerificationIssue(BaseModel):
    code: str  # e.g. "OVER_BUDGET", "UNSOURCED_CLAIM", "PACE_VIOLATION"
    message: str
    day_number: int | None = None
    activity_title: str | None = None


class VerificationResult(BaseModel):
    passed: bool
    violations: list[VerificationIssue] = Field(default_factory=list)
    unsupported_claims: list[VerificationIssue] = Field(default_factory=list)