from __future__ import annotations

"""Interest calculation methods for debts.

Each method exposes functions to handle new charges, daily accrual and
end-of-month processing. Methods are registered in ``INTEREST_METHODS`` so
that debts can specify which calculation to use.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange
from typing import Callable, Dict


def _add_month(d: date) -> date:
    """Return a date one month after ``d`` preserving month length."""
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


# ---------------------------------------------------------------------------
# Generic credit card interest


def credit_card_add_charge(debt, amount: Decimal, ch_date: date) -> None:
    debt.balance_subject_to_interest += amount


def credit_card_daily(debt, current_date: date) -> None:
    if debt.balance_subject_to_interest > 0 and debt.apr > 0:
        interest = debt.balance_subject_to_interest * debt.apr / Decimal("36500")
        debt.interest_buffer += interest
        debt.interest_accrued += interest


def credit_card_month_end(debt, current_date: date) -> Decimal:
    if debt.interest_buffer > 0:
        billed = debt.interest_buffer.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        debt.interest_buffer = Decimal("0")
        return billed
    return Decimal("0")


# ---------------------------------------------------------------------------
# Apple Card interest


def apple_card_add_charge(debt, amount: Decimal, ch_date: date) -> None:
    if debt.balance_subject_to_interest == 0:
        debt.grace_charges.append((ch_date, amount))
    else:
        debt.balance_subject_to_interest += amount


def apple_card_daily(debt, current_date: date) -> None:
    credit_card_daily(debt, current_date)
    if debt.due_date and current_date == debt.due_date and debt.grace_charges:
        for ch_date, amt in debt.grace_charges:
            days = (current_date - ch_date).days + 1
            retro = amt * debt.apr / Decimal("36500") * days
            debt.interest_buffer += retro
            debt.interest_accrued += retro
            debt.balance_subject_to_interest += amt
        debt.grace_charges.clear()
        debt.due_date = _add_month(debt.due_date)


def apple_card_month_end(debt, current_date: date) -> Decimal:
    return credit_card_month_end(debt, current_date)


# ---------------------------------------------------------------------------
# Registry


class InterestMethod:
    def __init__(self, add_charge: Callable, daily: Callable, month_end: Callable):
        self.add_charge = add_charge
        self.daily = daily
        self.month_end = month_end


INTEREST_METHODS: Dict[str, InterestMethod] = {
    "credit_card": InterestMethod(
        add_charge=credit_card_add_charge,
        daily=credit_card_daily,
        month_end=credit_card_month_end,
    ),
    "apple_card": InterestMethod(
        add_charge=apple_card_add_charge,
        daily=apple_card_daily,
        month_end=apple_card_month_end,
    ),
}
