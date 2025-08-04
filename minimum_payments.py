from __future__ import annotations

"""Minimum payment calculation formulas for various debts.

Each function here takes a ``debt`` object and an ``as_of`` date and returns
its calculated minimum payment as a ``Decimal``.  Formulas are centralized in
this module so they can be easily maintained or extended for additional
cardholder agreements.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP
from calendar import monthrange
from typing import Callable, Dict


def _add_month(d: date) -> date:
    """Return a date one month after ``d`` preserving month length."""

    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def credit_card(debt, as_of: date) -> Decimal:
    """Generic credit card minimum payment.

    This mirrors the previous default behaviour: 1% of the projected balance at
    the next due date plus one month's interest.  It provides a reasonable
    approximation for cards without a specific formula implementation.
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


def apple_card(debt, as_of: date) -> Decimal:
    """Apple Card minimum payment calculation.

    The formula is derived from the publicly documented rules.  It supports
    optional parameters supplied via ``debt.min_payment_args``:

    ``unpaid_daily_cash`` – any unpaid Daily Cash adjustments
    ``interest_billed`` – interest billed in the current statement period
    ``past_due`` – any past due amounts
    ``financing_balance`` – balance tied to financing plans (if any)
    ``installment_due`` – installment amount(s) due for financing plans
    
    The resulting minimum payment is the usual payment calculation plus any
    billed interest, installment amounts, and past due totals.
    """

    args = getattr(debt, "min_payment_args", {})
    unpaid_daily_cash = Decimal(str(args.get("unpaid_daily_cash", 0)))
    interest_billed = Decimal(str(args.get("interest_billed", 0)))
    past_due = Decimal(str(args.get("past_due", 0)))
    financing_balance = Decimal(str(args.get("financing_balance", 0)))
    installment_due = Decimal(str(args.get("installment_due", 0)))

    total_balance = debt.balance
    regular_balance = total_balance - financing_balance

    base = ((regular_balance - unpaid_daily_cash) * Decimal("0.01") + unpaid_daily_cash)
    base = base.quantize(Decimal("1"), rounding=ROUND_UP)
    base = max(Decimal("25"), base)

    payment = base + interest_billed + installment_due + past_due
    if total_balance < payment:
        payment = total_balance
    return payment


FORMULAS: Dict[str, Callable[[object, date], Decimal]] = {
    "credit_card": credit_card,
    "apple_card": apple_card,
}
