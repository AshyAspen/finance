import os
import sys
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from fin import calculate_snowball_plan


def test_balances_never_negative():
    """Run the snowball scheduler for ~360 days and ensure balances stay non-negative."""
    bills = [
        {"name": "Rent", "amount": 1000.0},
        {"name": "Utilities", "amount": 200.0},
    ]

    incomes = [
        {"name": "Salary", "amount": 3000.0, "frequency": "monthly", "start_date": "2025-01-01"},
    ]

    debts = [
        {"name": "Credit Card", "balance": 500.0, "minimum_payment": 50.0, "apr": 15.0},
        {"name": "Car Loan", "balance": 1500.0, "minimum_payment": 100.0, "apr": 6.0},
    ]

    # Run scheduling for approximately 360 days (12 months)
    schedule, _ = calculate_snowball_plan(bills, incomes, debts, forecast_months=12)

    # Ensure all recorded balances are non-negative throughout the schedule
    for month_data in schedule:
        for balance in month_data["remaining_balances"].values():
            assert balance >= 0, f"Negative balance {balance} recorded in {month_data['date']}"
