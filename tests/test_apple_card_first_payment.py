import os
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_UP
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_first_min_payment_includes_prior_interest_and_installment():
    today = date.today()
    due_date = today + timedelta(days=10)

    debts = [
        {
            "name": "Apple Card",
            "balance": 1000.0,
            "apr": 26.24,
            "minimum_payment": 0.0,
            "due_date": due_date.isoformat(),
            "min_payment_formula": "apple_card",
            "interest_method": "apple_card",
            "interest_billed": 90.0,
            "installment_due": 50.0,
            "financing_balance": 600.0,
        }
    ]

    schedule, _, _ = daily_avalanche_schedule(0, [], [], debts, days=20, debug=True)

    debt_min = next(ev for ev in schedule if ev["type"] == "debt_min")

    regular_balance = Decimal("1000") - Decimal("600")
    base = (regular_balance * Decimal("0.01")).quantize(Decimal("1"), rounding=ROUND_UP)
    base = max(Decimal("25"), base)
    expected = base + Decimal("90") + Decimal("50")

    assert debt_min["date"] == due_date
    assert -debt_min["amount"] == expected
