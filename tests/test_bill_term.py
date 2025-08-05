import os
import sys
from datetime import date, timedelta
from calendar import monthrange
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_bill_occurs_only_for_term_months():
    today = date.today()
    bills = [
        {
            "name": "Installment",
            "amount": 10.0,
            "date": today.isoformat(),
            "debt": "Card",
            "term_months": 2,
        }
    ]
    debts = [
        {
            "name": "Card",
            "balance": 0.0,
            "apr": 0.0,
            "minimum_payment": 0.0,
            "due_date": (today + timedelta(days=30)).isoformat(),
        }
    ]

    schedule, _, _ = daily_avalanche_schedule(0, [], bills, debts, days=90)

    adds = [ev for ev in schedule if ev["type"] == "debt_add"]
    assert len(adds) == 2
    assert adds[0]["date"] == today

    year = today.year + (today.month // 12)
    month = today.month % 12 + 1
    day = min(today.day, monthrange(year, month)[1])
    assert adds[1]["date"] == date(year, month, day)
