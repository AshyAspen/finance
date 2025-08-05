import os
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_UP
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule
from min_payments.apple_card import calculate as apple_card_min_payment


def test_first_min_payment_includes_prior_interest_and_installment():
    today = date.today()
    due_date = today + timedelta(days=10)

    debts = [
        {
            "name": "Apple Card",
            "balance": 1000.0,
            "apr": 26.24,
            "due_date": due_date.isoformat(),
            "min_payment_formula": apple_card_min_payment,
            "interest_method": "apple_card",
            "min_payment_args": {
                "statement_balance": 1000.0,
                "interest_accrued": 90.0,
                "installments": [
                    {
                        "balance": 500.0,
                        "minimum_payment": 50.0,
                        "term_months": 12,
                        "start_date": due_date.isoformat(),
                    }
                ],
                "daily_cash_adjustments": [],
            },
        }
    ]

    schedule, _, _ = daily_avalanche_schedule(0, [], [], debts, days=20, debug=True)

    debt_min = next(ev for ev in schedule if ev["type"] == "debt_min")

    payment_sum = Decimal("1000") * Decimal("0.01") + Decimal("90")
    expected = payment_sum.quantize(Decimal("1"), rounding=ROUND_UP) + Decimal("50")

    assert debt_min["date"] == due_date
    assert -debt_min["amount"] == expected
