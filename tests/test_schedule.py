import os
import sys
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_balances_never_negative():
    """Run the avalanche scheduler and ensure balances stay non-negative."""
    paychecks = [
        {"amount": 3000.0, "date": "2025-01-01"},
        {"amount": 3000.0, "date": "2025-02-01"},
    ]
    bills = [
        {"amount": 1000.0, "date": "2025-01-10"},
        {"amount": 200.0, "date": "2025-01-20"},
    ]
    debts = [
        {
            "name": "Credit Card",
            "balance": 500.0,
            "apr": 15.0,
            "minimum_payment": 50.0,
            "due_date": "2025-01-25",
        },
        {
            "name": "Car Loan",
            "balance": 1500.0,
            "apr": 6.0,
            "minimum_payment": 100.0,
            "due_date": "2025-02-15",
        },
    ]

    schedule, _ = daily_avalanche_schedule(0, paychecks, bills, debts)

    for event in schedule:
        assert event["balance"] >= 0, f"Negative balance {event['balance']} on {event['date']}"
