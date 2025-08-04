import os
import sys
from decimal import Decimal
from pathlib import Path

# Ensure project root on path for direct module imports
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_daily_interest_accrual():
    debts = [{"name": "Loan", "balance": 1000.0, "apr": 36.5, "minimum_payment": 0.0}]
    schedule, after, _ = daily_avalanche_schedule(0, [], [], debts, days=2)
    loan_info = next(d for d in after if d["name"] == "Loan")
    loan_balance = loan_info["balance"]
    interest = loan_info["interest_accrued"]

    rate = Decimal("36.5") / Decimal("36500")
    expected = Decimal("1000")
    for _ in range(3):
        expected += expected * rate
    precision = Decimal("0.000001")
    assert loan_balance.quantize(precision) == expected.quantize(precision)
    expected_interest = expected - Decimal("1000")
    assert interest.quantize(precision) == expected_interest.quantize(precision)
