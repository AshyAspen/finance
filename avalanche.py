from __future__ import annotations

"""Generate a daily debt payment schedule using the avalanche method.

The simulation starts on the current date and builds recurring income, bill,
and debt events through the requested horizon. Only future occurrences of
each event are included—any dates before the start are treated as already
paid. On each day income is applied first, then any bill or minimum debt
payment due that day is paid. Remaining cash that can safely be used (as
calculated by ``cash_flow.max_safe_payment``) is directed to the highest-APR
debt.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple
from calendar import monthrange

from cash_flow import max_safe_payment


@dataclass
class Event:
    """Represents a financial event."""

    date: date
    type: str  # "paycheck", "bill", or "debt_min"
    amount: Decimal
    name: str


@dataclass
class Debt:
    """Represents a debt with APR and balance."""

    name: str
    balance: Decimal
    apr: Decimal
    minimum_payment: Decimal
    due_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Helpers


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()



def _add_month(d: date) -> date:
    """Return a date one month after ``d`` preserving month length."""

    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _advance_paycheck(current: date, freq: str, first_day: int) -> date:
    """Return the next paycheck date based on ``freq`` starting from ``current``."""

    if freq == "weekly":
        return current + timedelta(weeks=1)
    if freq == "biweekly":
        return current + timedelta(weeks=2)
    if freq == "semi-monthly":
        second_day = min(first_day + 15, monthrange(current.year, current.month)[1])
        if current.day == first_day:
            return current.replace(day=second_day)
        next_month = _add_month(current.replace(day=1))
        return next_month.replace(
            day=min(first_day, monthrange(next_month.year, next_month.month)[1])
        )
    return _add_month(current)


def _build_events(
    paychecks: Iterable[dict],
    bills: Iterable[dict],
    debts: Iterable[Debt],
    start: date,
    end: date,
) -> List[Event]:
    events: List[Event] = []

    # Generate recurring paychecks
    for p in paychecks:
        current = _parse_date(p["date"])
        freq = p.get("frequency", "monthly").lower()
        first_day = current.day
        while current < start:
            current = _advance_paycheck(current, freq, first_day)
        while current <= end:
            events.append(
                Event(
                    date=current,
                    type="paycheck",
                    amount=Decimal(str(p["amount"])),
                    name=p.get("name", "Paycheck"),
                )
            )
            current = _advance_paycheck(current, freq, first_day)

    # Recurring bills
    for b in bills:
        current = _parse_date(b["date"])
        while current < start:
            current = _add_month(current)
        while current <= end:
            events.append(
                Event(
                    date=current,
                    type="bill",
                    amount=Decimal(str(b["amount"])),
                    name=b.get("name", "Bill"),
                )
            )
            current = _add_month(current)

    # Minimum debt payments
    for d in debts:
        if d.due_date is None or d.minimum_payment <= 0:
            continue
        current = d.due_date
        while current < start:
            current = _add_month(current)
        while current <= end:
            events.append(Event(current, "debt_min", d.minimum_payment, d.name))
            current = _add_month(current)

    events.sort(key=lambda e: e.date)
    return events


def _next_due_date(due: Optional[date], end: date) -> Optional[date]:
    if due is None:
        return None
    current = due
    while current <= end:
        current = _add_month(current)
    return current


# ---------------------------------------------------------------------------
# Core algorithm


def daily_avalanche_schedule(
    starting_balance: float | Decimal,
    paychecks: Iterable[dict],
    bills: Iterable[dict],
    debts_input: Iterable[dict],
    days: int = 60,
) -> Tuple[List[dict], List[dict]]:
    """Return scheduled transactions and final debt balances using the avalanche method.

    Parameters
    ----------
    starting_balance:
        Current cash balance.
    paychecks:
        Iterable of dictionaries with ``amount`` and ``date`` keys.
    bills:
        Iterable of dictionaries with ``amount`` and ``date`` keys for regular
        bills.
    debts_input:
        Iterable of dictionaries describing debts with keys ``name``, ``balance``,
        ``apr``, ``minimum_payment`` and ``due_date``.
    Returns
    -------
    Tuple[List[dict], List[dict]]
        ``schedule`` of transactions and a list of remaining ``debts`` with updated balances.
    """

    balance = Decimal(str(starting_balance))

    start = date.today()
    end = start + timedelta(days=days)

    # Prepare debt objects for tracking balances and APRs
    debts: List[Debt] = [
        Debt(
            name=d["name"],
            balance=Decimal(str(d["balance"])),
            apr=Decimal(str(d["apr"])),
            minimum_payment=Decimal(str(d.get("minimum_payment", 0))),
            due_date=_parse_date(d["due_date"]) if d.get("due_date") else None,
        )
        for d in debts_input
    ]
    debt_lookup = {d.name: d for d in debts}

    events = _build_events(paychecks, bills, debts, start, end)

    schedule: List[dict] = []

    i = 0
    while i < len(events):
        current_date = events[i].date
        todays: List[Event] = []
        while i < len(events) and events[i].date == current_date:
            todays.append(events[i])
            i += 1

        # Process income first
        for ev in [e for e in todays if e.type == "paycheck"]:
            balance += ev.amount
            schedule.append(
                {
                    "date": ev.date,
                    "type": "paycheck",
                    "description": ev.name,
                    "amount": ev.amount,
                    "balance": balance,
                }
            )

        # Then pay bills or minimum debt payments for the day
        for ev in [e for e in todays if e.type != "paycheck"]:
            payment_amount = ev.amount
            if ev.type == "debt_min":
                debt = debt_lookup[ev.name]
                payment_amount = min(ev.amount, debt.balance)
                if payment_amount <= 0:
                    continue
                debt.balance -= payment_amount
            balance -= payment_amount
            schedule.append(
                {
                    "date": ev.date,
                    "type": ev.type,
                    "description": ev.name,
                    "amount": -payment_amount,
                    "balance": balance,
                }
            )

        # Future events for safe-payment calculation
        future_events = events[i:]
        future_bills = [
            {"amount": ev.amount, "date": ev.date.isoformat()}
            for ev in future_events
            if ev.type != "paycheck"
        ]
        future_incomes = [
            {"amount": ev.amount, "date": ev.date.isoformat()}
            for ev in future_events
            if ev.type == "paycheck"
        ]
        safe = max_safe_payment(balance, future_bills, future_incomes)

        if safe > 0:
            active_debts = [d for d in debts if d.balance > 0]
            if active_debts:
                target = max(active_debts, key=lambda d: d.apr)
                payment = min(safe, target.balance)
                if payment > 0:
                    target.balance -= payment
                    balance -= payment
                    schedule.append(
                        {
                            "date": current_date,
                            "type": "extra",
                            "description": f"Extra payment to {target.name}",
                            "amount": -payment,
                            "balance": balance,
                        }
                    )

    return schedule, [
        {
            "name": d.name,
            "balance": d.balance,
            "next_due_date": _next_due_date(d.due_date, end),
        }
        for d in debts
    ]

