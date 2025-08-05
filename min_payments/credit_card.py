from __future__ import annotations

"""Generic credit card minimum payment formula."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange


def _add_month(d: date) -> date:
    """Return a date one month after ``d`` preserving month length."""
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate(debt, as_of: date) -> Decimal:
    """Generic credit card minimum payment.

    This mirrors the previous default behaviour: 1% of the projected balance at
    the next due date plus one month's interest.
    """

    balance = debt.balance
    if getattr(debt, "due_date", None) and debt.apr > 0:
        next_due = debt.due_date
        while next_due <= as_of:
            next_due = _add_month(next_due)
        days = (next_due - as_of).days
        if days > 0:
            balance += balance * debt.apr / Decimal("36500") * days

    base = balance * (debt.apr / Decimal("1200") + Decimal("0.01"))
    return base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
