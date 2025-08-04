import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_debt_min_rounds_up_to_cents():
    today = date.today()
    debts = [
        {
            "name": "Alpheon",
            "balance": 152.995,
            "minimum_payment": 153.0,
            "apr": 0.0,
            "due_date": (today + timedelta(days=4)).isoformat(),
        },
        {
            "name": "Other",
            "balance": 100.0,
            "minimum_payment": 0.0,
            "apr": 0.0,
            "due_date": (today + timedelta(days=30)).isoformat(),
        },
    ]
    schedule, _ = daily_avalanche_schedule(200.0, [], [], debts, days=10)
    pay = next(
        e for e in schedule if e["type"] == "debt_min" and e["description"] == "Alpheon"
    )
    assert pay["amount"] == Decimal("-153.00")
    assert schedule[-1]["balance"] >= 0
