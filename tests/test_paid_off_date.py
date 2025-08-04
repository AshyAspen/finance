import os
import sys
from datetime import date
from pathlib import Path

# Ensure project root on path for direct module imports
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_paid_off_debt_reports_date():
    today = date.today()
    debts = [
        {
            "name": "Loan",
            "balance": 100.0,
            "apr": 0.0,
            "minimum_payment": 100.0,
            "due_date": today.isoformat(),
        }
    ]
    schedule, after, _ = daily_avalanche_schedule(100, [], [], debts, days=30)
    loan = next(d for d in after if d["name"] == "Loan")
    assert loan["balance"] == 0
    assert loan["paid_off_date"] == today
    assert loan["next_due_date"] is None

