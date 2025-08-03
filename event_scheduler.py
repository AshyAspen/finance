from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict

from dateutil.relativedelta import relativedelta

from cash_flow import max_safe_payment


def _parse_date(value: date | str) -> date:
    """Parse a date or ISO formatted string."""
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


@dataclass
class Event:
    date: date
    type: str  # 'income', 'bill', 'debt_min'
    name: str
    amount: Decimal
    debt_index: int | None = None


def _generate_events(
    bills: List[Dict],
    incomes: List[Dict],
    debts: List[Dict],
    start: date,
    days: int,
) -> List[Event]:
    """Create a sorted list of events within the forecast window."""
    events: List[Event] = []
    end = start + timedelta(days=days)

    for b in bills:
        dt = _parse_date(b["date"])
        if start <= dt <= end:
            events.append(Event(date=dt, type="bill", name=b["name"], amount=Decimal(str(b["amount"])) ))

    for inc in incomes:
        dt = _parse_date(inc["date"])
        if start <= dt <= end:
            events.append(Event(date=dt, type="income", name=inc["name"], amount=Decimal(str(inc["amount"])) ))

    for idx, debt in enumerate(debts):
        due_day = int(debt["due_day"])
        due = start.replace(day=due_day)
        if due < start:
            due = (start + relativedelta(months=1)).replace(day=due_day)
        while due <= end:
            events.append(Event(date=due, type="debt_min", name=debt["name"], amount=debt["minimum_payment"], debt_index=idx))
            due = (due + relativedelta(months=1)).replace(day=due_day)

    events.sort(key=lambda e: e.date)
    return events


def forecast_events(
    start_balance: float | Decimal,
    bills: List[Dict],
    incomes: List[Dict],
    debts: List[Dict],
    days: int = 60,
):
    """Run a day-by-day cash flow with debt payments using snowball logic."""
    start = datetime.today().date()
    balance = Decimal(str(start_balance))

    # ensure decimals for debts
    for d in debts:
        d["balance"] = Decimal(str(d["balance"]))
        d["minimum_payment"] = Decimal(str(d["minimum_payment"]))

    events = _generate_events(bills, incomes, debts, start, days)

    results = []
    for idx, ev in enumerate(events):
        bills_paid = Decimal("0")
        mins_paid = Decimal("0")
        extra_paid = Decimal("0")

        if ev.type == "income":
            balance += ev.amount
        elif ev.type == "bill":
            balance -= ev.amount
            bills_paid = ev.amount
        elif ev.type == "debt_min":
            pay = min(ev.amount, debts[ev.debt_index]["balance"])
            balance -= pay
            debts[ev.debt_index]["balance"] -= pay
            mins_paid = pay

        if ev.type == "income":
            future = events[idx + 1 :]
            future_bills = [{"date": f.date, "amount": f.amount} for f in future if f.type in {"bill", "debt_min"}]
            future_incomes = [{"date": f.date, "amount": f.amount} for f in future if f.type == "income"]
            extra = max_safe_payment(balance, future_bills, future_incomes)
            if extra > 0:
                targets = [i for i, d in enumerate(debts) if d["balance"] > 0]
                if targets:
                    target = min(targets, key=lambda i: debts[i]["balance"])
                    pay_extra = min(extra, debts[target]["balance"])
                    balance -= pay_extra
                    debts[target]["balance"] -= pay_extra
                    extra_paid = pay_extra

        results.append(
            {
                "date": ev.date,
                "balance": balance,
                "bills": bills_paid,
                "minimums": mins_paid,
                "extra": extra_paid,
            }
        )

    return results, debts
