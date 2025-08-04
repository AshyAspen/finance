import os
import sys
from datetime import date
from pathlib import Path

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_bill_adds_to_debt_not_balance():
    today = date.today()
    bills = [
        {"amount": 200.0, "date": today.isoformat(), "debt": "Card", "name": "Purchase"}
    ]
    debts = [
        {"name": "Card", "balance": 0.0, "apr": 0.0, "minimum_payment": 0.0}
    ]

    schedule, after = daily_avalanche_schedule(0, [], bills, debts, days=30)

    assert schedule[0]["type"] == "debt_add"
    assert schedule[0]["balance"] == 0
    assert schedule[0]["amount"] == 0

    card = next(d for d in after if d["name"] == "Card")
    assert float(card["balance"]) == 200.0
