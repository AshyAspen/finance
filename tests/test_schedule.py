import os
import sys
from datetime import date
from calendar import monthrange
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_balances_never_negative():
    """Run the avalanche scheduler and ensure balances stay non-negative."""
    today = date.today()
    month_start = today.replace(day=1)
    paychecks = [
        {"amount": 3000.0, "date": today.isoformat()},
    ]
    bills = [
        {"amount": 1000.0, "date": month_start.replace(day=10).isoformat()},
        {"amount": 200.0, "date": month_start.replace(day=20).isoformat()},
    ]
    debts = [
        {
            "name": "Credit Card",
            "balance": 500.0,
            "apr": 15.0,
            "minimum_payment": 50.0,
            "due_date": month_start.replace(day=25).isoformat(),
        },
        {
            "name": "Car Loan",
            "balance": 1500.0,
            "apr": 6.0,
            "minimum_payment": 100.0,
            "due_date": month_start.replace(day=15).isoformat(),
        },
    ]

    schedule, _ = daily_avalanche_schedule(0, paychecks, bills, debts)

    for event in schedule:
        assert event["balance"] >= 0, f"Negative balance {event['balance']} on {event['date']}"


def _add_month(d):
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def test_events_before_today_skipped():
    """Events dated earlier this month roll forward to their next occurrence."""
    today = date.today()
    past = today.replace(day=1)
    bills = [{"amount": 100.0, "date": past.isoformat()}]
    schedule, _ = daily_avalanche_schedule(1000, [], bills, [])

    expected = past
    while expected < today:
        expected = _add_month(expected)

    assert schedule and schedule[0]["date"] == expected
