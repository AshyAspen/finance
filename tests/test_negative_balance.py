import os
import sys
from datetime import date, timedelta
from pathlib import Path
import pytest

# Ensure project root on path for direct module imports
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def test_negative_balance_raises():
    today = date.today()
    future_bill = today + timedelta(days=10)
    bills = [{"amount": 100.0, "date": future_bill.isoformat()}]

    with pytest.raises(ValueError):
        daily_avalanche_schedule(50.0, [], bills, [], days=30)


def test_debug_mode_continues():
    today = date.today()
    future_bill = today + timedelta(days=10)
    future_paycheck = future_bill + timedelta(days=30)
    bills = [{"amount": 100.0, "date": future_bill.isoformat()}]
    paychecks = [{"amount": 10.0, "date": future_paycheck.isoformat()}]

    schedule, _, negative_date = daily_avalanche_schedule(
        50.0, paychecks, bills, [], days=40, debug=True
    )
    assert negative_date == future_bill
    assert any(ev["date"] == future_paycheck for ev in schedule)
