"""
Budget-related models. `Budget` is the user's input constraint;
`BudgetBreakdown` (defined here too, alongside BudgetLineItem) is the
service-computed output. Kept in one file since they're tightly coupled.
"""
from pydantic import BaseModel, Field, model_validator

from models.common import Money, SignedMoney
from models.enums import BudgetCategory, DataSource


class Budget(BaseModel):
    """User-specified total budget for the trip."""

    total: Money
    per_person: bool = False


class BudgetLineItem(BaseModel):
    category: BudgetCategory
    amount: Money
    source: DataSource = DataSource.COMPUTED
    notes: str | None = None


class BudgetBreakdown(BaseModel):
    """
    Output of the Budget Agent / budget_calculator service. All amounts
    must be in the same currency as `total_budget` — validated below.
    `remaining` uses SignedMoney since a trip can legitimately go over
    budget (negative remaining) and that must be representable.
    """

    total_budget: Money
    line_items: list[BudgetLineItem] = Field(default_factory=list)
    spent: Money
    remaining: SignedMoney
    per_person_per_day: Money | None = None

    @model_validator(mode="after")
    def currencies_must_match(self) -> "BudgetBreakdown":
        currency = self.total_budget.currency
        mismatched = [
            item.category.value
            for item in self.line_items
            if item.amount.currency != currency
        ]
        if mismatched:
            raise ValueError(
                f"Line items with mismatched currency vs total_budget "
                f"({currency}): {mismatched}"
            )
        if self.spent.currency != currency or self.remaining.currency != currency:
            raise ValueError(
                "spent/remaining currency must match total_budget currency"
            )
        return self