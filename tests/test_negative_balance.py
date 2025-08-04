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
