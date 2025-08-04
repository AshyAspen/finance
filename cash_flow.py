"""Cash flow helper to find immediate safe payment amount.

This module computes the maximum amount of money that can be paid today
without causing future negative balances, given known future bills and
incomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
from typing import Iterable, List


@dataclass
class CashEvent:
    """Represents a dated cash flow event."""

    date: date
    amount: Decimal  # positive for income, negative for bills


def _parse_date(value: date | str) -> date:
    """Parse a ``date`` object or an ISO date string."""

    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _build_events(bills: Iterable[dict], incomes: Iterable[dict]) -> List[CashEvent]:
    """Convert bill and income dictionaries into ``CashEvent`` objects."""

    events: List[CashEvent] = []
    for item in bills:
        events.append(
            CashEvent(
                date=_parse_date(item["date"]),
                amount=Decimal(str(item["amount"]))
                .quantize(CENT, rounding=ROUND_HALF_UP)
                * Decimal("-1"),
            )
        )
    for item in incomes:
        events.append(
            CashEvent(
                date=_parse_date(item["date"]),
                amount=Decimal(str(item["amount"]))
                .quantize(CENT, rounding=ROUND_HALF_UP),
            )
        )
    # Sort by date; on same day, incomes (positive) should apply before bills
    events.sort(key=lambda e: (e.date, e.amount < 0))
    return events


def projected_min_balance(
    initial_balance: float | Decimal, bills: Iterable[dict], incomes: Iterable[dict]
) -> tuple[Decimal, date | None]:
    """Return the minimum projected balance and when it occurs."""

    balance = Decimal(str(initial_balance)).quantize(CENT, rounding=ROUND_HALF_UP)
    events = _build_events(bills, incomes)

    running = balance
    min_balance = running
    negative_date = None
    for event in events:
        running += event.amount
        running = running.quantize(CENT, rounding=ROUND_HALF_UP)
        if running < min_balance:
            min_balance = running
        if negative_date is None and running < 0:
            negative_date = event.date

    return min_balance, negative_date


def max_safe_payment(initial_balance: float | Decimal, bills: Iterable[dict], incomes: Iterable[dict]) -> Decimal:
    """Return the largest amount that can be paid today without future overdraft.

    Parameters
    ----------
    initial_balance:
        Current amount of money available.
    bills:
        Iterable of dicts with ``amount`` and ``date`` keys for upcoming
        obligations.
    incomes:
        Iterable of dicts with ``amount`` and ``date`` keys for known future
        income.

    Returns
    -------
    Decimal
        The maximum additional payment that can be made immediately while
        keeping the balance non-negative for all future events.
    """

    min_balance, _ = projected_min_balance(initial_balance, bills, incomes)
    return max(Decimal("0"), min_balance.quantize(CENT, rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    # Example usage
    current_balance = 1000
    bills = [
        {"amount": 300, "date": "2025-06-15"},
        {"amount": 200, "date": "2025-06-20"},
    ]
    incomes = [{"amount": 1000, "date": "2025-06-25"}]

    print("Max safe payment:", max_safe_payment(current_balance, bills, incomes))
