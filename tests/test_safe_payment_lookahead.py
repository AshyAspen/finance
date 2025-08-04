import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_schedule_independent_of_simulation_length():
    """Schedules should match for overlapping period regardless of horizon."""
    today = date.today()
    bill_date = today + timedelta(days=31)
    paycheck_date = today + timedelta(days=60)

    bills = [{"amount": 800.0, "date": bill_date.isoformat()}]
    paychecks = [{"amount": 1000.0, "date": paycheck_date.isoformat()}]
    debts = [
        {"name": "Card", "balance": 500.0, "apr": 0.0, "minimum_payment": 0.0}
    ]

    short_schedule, _, _ = daily_avalanche_schedule(
        1000.0, paychecks, bills, debts, days=30
    )
    long_schedule, _, _ = daily_avalanche_schedule(
        1000.0, paychecks, bills, debts, days=60
    )

    end_short = today + timedelta(days=30)
    long_trimmed = [ev for ev in long_schedule if ev["date"] <= end_short]
    assert short_schedule == long_trimmed
