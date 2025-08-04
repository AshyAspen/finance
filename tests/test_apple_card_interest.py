import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

import avalanche


def test_apple_card_interest_no_compounding(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2023, 1, 1)

    monkeypatch.setattr(avalanche, "date", FixedDate)

    debts = [
        {
            "name": "Apple Card",
            "balance": 1000.0,
            "apr": 24.0,
            "minimum_payment": 0.0,
            "min_payment_formula": "apple_card",
        }
    ]

    debt_log = []
    _, after, _ = avalanche.daily_avalanche_schedule(
        0, [], [], debts, days=364, debug=True, debt_log=debt_log
    )

    info = after[0]

    principal = Decimal("1000")
    apr = Decimal("24")
    current = FixedDate.today()
    end = current.replace(year=current.year + 1)
    expected = Decimal("0")
    while current < end:
        next_month = current.replace(day=1)
        if current.month == 12:
            next_month = next_month.replace(year=current.year + 1, month=1)
        else:
            next_month = next_month.replace(month=current.month + 1)
        days = (next_month - current).days
        month_interest = principal * apr / Decimal("36500") * days
        expected += month_interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        current = next_month

    assert info["interest_charges"] == expected
    assert info["balance"] == principal + expected
    assert debt_log[0]["interest_charges"]["Apple Card"] == Decimal("0")
    assert debt_log[-1]["interest_charges"]["Apple Card"] == expected

