import os
import sys
from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal, ROUND_UP, ROUND_HALF_UP
from pathlib import Path

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_installment_and_interest_added_and_min_payment():
    today = date.today()
    end_of_month = today.replace(day=monthrange(today.year, today.month)[1])

    bills = [
        {
            "name": "iPhone Installment",
            "amount": 50.0,
            "date": end_of_month.isoformat(),
            "debt": "Apple Card",
        }
    ]

    due_date = end_of_month + timedelta(days=10)

    debts = [
        {
            "name": "Apple Card",
            "balance": 1000.0,
            "minimum_payment": 25.0,
            "apr": 24.0,
            "due_date": due_date.isoformat(),
            "min_payment_formula": "apple_card",
            "unpaid_daily_cash": 0,
            "interest_billed": 0,
            "past_due": 0,
            "installment_due": 50.0,
        }
    ]

    schedule, _, _ = daily_avalanche_schedule(0, [], bills, debts, days=40, debug=True)

    # Interest added at end of month
    interest_event = next(
        ev for ev in schedule if ev["type"] == "debt_add" and "interest" in ev["description"].lower()
    )
    assert interest_event["date"] == end_of_month

    rate = Decimal("24") / Decimal("36500")
    remaining = (end_of_month - today).days + 1
    expected_interest = (
        rate * (Decimal("1000") * (remaining - 1) + Decimal("1050"))
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert interest_event["amount"] == expected_interest

    debt_min = next(ev for ev in schedule if ev["type"] == "debt_min")
    regular_balance = Decimal("1000") + Decimal("50") + expected_interest
    base = (regular_balance * Decimal("0.01")).quantize(Decimal("1"), rounding=ROUND_UP)
    base = max(Decimal("25"), base)
    expected_min = base + expected_interest + Decimal("50")
    assert -debt_min["amount"] == expected_min
