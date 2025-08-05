import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule
from min_payments.credit_card import calculate as credit_card_min_payment


def test_debt_add_updates_min_payment_and_reserves_cash():
    today = date.today()
    bills = [
        {
            "name": "Charge",
            "amount": 100.0,
            "date": (today + timedelta(days=5)).isoformat(),
            "debt": "Card",
        }
    ]
    paychecks = [{"amount": 50.0, "date": today.isoformat()}]
    debts = [
        {
            "name": "Card",
            "balance": 100.0,
            "apr": 0.0,
            "minimum_payment": 1.0,
            "due_date": (today + timedelta(days=10)).isoformat(),
            "min_payment_formula": credit_card_min_payment,
        }
    ]

    schedule, _, _ = daily_avalanche_schedule(0, paychecks, bills, debts, days=20)

    extra = next(ev for ev in schedule if ev["type"] == "extra")
    assert float(extra["amount"]) == -48.0

    debt_min = next(ev for ev in schedule if ev["type"] == "debt_min")
    assert debt_min["date"] == today + timedelta(days=10)
    assert float(debt_min["amount"]) == -1.52
