import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_debt_min_less_than_balance_does_not_raise():
    today = date.today()
    debts = [
        {
            "name": "Card",
            "balance": 20.0,
            "minimum_payment": 100.0,
            "apr": 0.0,
            "due_date": (today + timedelta(days=1)).isoformat(),
        }
    ]
    schedule, after = daily_avalanche_schedule(
        50.0, [], [], debts, days=30
    )
    assert after[0]["balance"] == 0
    assert schedule[-1]["balance"] == 30
