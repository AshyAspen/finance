import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_balances_never_negative():
    """Run the avalanche scheduler and ensure balances stay non-negative."""
    today = date.today()
    start = today.replace(day=1)
    paychecks = [
        {"amount": 3000.0, "date": start.isoformat()},
    ]
    bills = [
        {"amount": 1000.0, "date": (start + timedelta(days=10)).isoformat()},
        {"amount": 200.0, "date": (start + timedelta(days=20)).isoformat()},
    ]
    debts = [
        {
            "name": "Credit Card",
            "balance": 500.0,
            "apr": 15.0,
            "minimum_payment": 50.0,
            "due_date": (start + timedelta(days=25)).isoformat(),
        },
        {
            "name": "Car Loan",
            "balance": 1500.0,
            "apr": 6.0,
            "minimum_payment": 100.0,
            "due_date": (start + timedelta(days=35)).isoformat(),
        },
    ]

    schedule, _ = daily_avalanche_schedule(0, paychecks, bills, debts)

    for event in schedule:
        assert event["balance"] >= 0, f"Negative balance {event['balance']} on {event['date']}"


def test_events_before_today_in_month_included():
    """Bills earlier in the month should still be scheduled."""
    today = date.today()
    start = today.replace(day=1)
    if today.day > 1:
        due = start
    else:
        due = start + timedelta(days=1)
    bills = [{"amount": 100.0, "date": due.isoformat()}]
    schedule, _ = daily_avalanche_schedule(1000, [], bills, [])
    assert schedule and schedule[0]["date"] == due
