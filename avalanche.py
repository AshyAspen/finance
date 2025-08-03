from __future__ import annotations

"""Generate a daily debt payment schedule using the avalanche method.

The schedule processes a chronologically sorted list of financial events and
routes surplus cash to the highest-APR debt while ensuring upcoming bills are
covered.  The algorithm operates on paydays: income is deposited, bills due
before the next payday are paid, and any remaining safe cash (as calculated by
:func:`cash_flow.max_safe_payment`) is sent as an extra payment toward the
highest-APR debt.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

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

    def to_min_event(self) -> Event:
        if self.due_date is None:
            raise ValueError("debt due_date required for minimum payment event")
        return Event(self.due_date, "debt_min", self.minimum_payment, self.name)


# ---------------------------------------------------------------------------
# Helpers


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _build_events(paychecks: Iterable[dict], bills: Iterable[dict], debts: Iterable[Debt]) -> List[Event]:
    events: List[Event] = []
    for p in paychecks:
        events.append(
            Event(
                date=_parse_date(p["date"]),
                type="paycheck",
                amount=Decimal(str(p["amount"])),
                name=p.get("name", "Paycheck"),
            )
        )
    for b in bills:
        events.append(
            Event(
                date=_parse_date(b["date"]),
                type="bill",
                amount=Decimal(str(b["amount"])),
                name=b.get("name", "Bill"),
            )
        )
    for d in debts:
        if d.due_date is not None and d.minimum_payment > 0:
            events.append(d.to_min_event())
    events.sort(key=lambda e: e.date)
    return events


# ---------------------------------------------------------------------------
# Core algorithm


def daily_avalanche_schedule(
    starting_balance: float | Decimal,
    paychecks: Iterable[dict],
    bills: Iterable[dict],
    debts_input: Iterable[dict],
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

    events = _build_events(paychecks, bills, debts)

    # Separate lists for ease of future lookups
    pay_events = [e for e in events if e.type == "paycheck"]
    other_events = [e for e in events if e.type != "paycheck"]

    schedule: List[dict] = []

    for i, payday in enumerate(pay_events):
        next_payday = pay_events[i + 1].date if i + 1 < len(pay_events) else None

        # Deposit income
        balance += payday.amount
        schedule.append(
            {
                "date": payday.date,
                "type": "paycheck",
                "description": payday.name,
                "amount": payday.amount,
                "balance": balance,
            }
        )

        # Pay bills/debt minimums due before the next payday on this payday
        remaining_events: List[Event] = []
        for ev in other_events:
            due_now = ev.date <= payday.date or (next_payday is None or ev.date < next_payday)
            if due_now:
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
                        "date": payday.date,
                        "type": ev.type,
                        "description": ev.name,
                        "amount": -payment_amount,
                        "balance": balance,
                    }
                )
            else:
                remaining_events.append(ev)
        other_events = remaining_events

        # Build future events for safe-payment calculation
        future_bills = [
            {"amount": ev.amount, "date": ev.date.isoformat()}
            for ev in other_events
        ]
        future_incomes = [
            {"amount": p.amount, "date": p.date.isoformat()}
            for p in pay_events[i + 1 :]
        ]
        safe = max_safe_payment(balance, future_bills, future_incomes)

        if safe > 0:
            # Target highest-APR debt with remaining balance
            active_debts = [d for d in debts if d.balance > 0]
            if active_debts:
                target = max(active_debts, key=lambda d: d.apr)
                payment = min(safe, target.balance)
                target.balance -= payment
                balance -= payment
                schedule.append(
                    {
                        "date": payday.date,
                        "type": "extra",
                        "description": f"Extra payment to {target.name}",
                        "amount": -payment,
                        "balance": balance,
                    }
                )

    return schedule, [{"name": d.name, "balance": d.balance} for d in debts]

