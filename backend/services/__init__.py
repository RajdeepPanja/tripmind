"""
Deterministic services: budget_calculator, distance_calculator,
constraint_checker, scoring.

These modules perform all arithmetic and rule-checking for TripMind.
Agents call into these services; the LLM is never asked to compute prices,
distances, totals, percentages, or scores.
"""