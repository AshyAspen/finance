import os
import sys
from datetime import date
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

import fin
from avalanche import daily_avalanche_schedule


def test_run_simulation_handles_debt_add(monkeypatch, capsys):
    data = {
        "paychecks": [],
        "bills": [
            {
                "name": "Purchase",
                "amount": 25.0,
                "date": date.today().isoformat(),
                "debt": "Card",
            }
        ],
        "debts": [
            {
                "name": "Card",
                "balance": 0.0,
                "apr": 0.0,
                "minimum_payment": 0.0,
            }
        ],
    }

    inputs = iter(["1", "0"])  # simulate one day and $0 balance
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    fin.run_simulation(data)
    output = capsys.readouterr().out
    assert "Debt additions" in output
    assert "Purchase $25.00" in output

    schedule, _ = daily_avalanche_schedule(
        0, [], data["bills"], data["debts"], days=1
    )
    assert schedule[0]["amount"] == 25
    assert schedule[0]["balance"] == 0
