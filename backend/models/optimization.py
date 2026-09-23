"""
Request/response shapes for the Optimize endpoint. The action enum drives
which constraints a service mutates — the LLM is not asked to interpret
the button click; that mapping lives in a deterministic service.
"""
from typing import Any

from pydantic import BaseModel, Field

from models.enums import OptimizationAction


class TripOptimizationRequest(BaseModel):
    trip_id: str
    action: OptimizationAction


class ConstraintDiff(BaseModel):
    field: str
    before: Any
    after: Any


class TripOptimizationResult(BaseModel):
    trip_id: str
    action: OptimizationAction
    diffs: list[ConstraintDiff] = Field(default_factory=list)