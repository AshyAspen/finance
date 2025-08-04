import os
import sys
from datetime import date
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

import fin


def test_run_simulation_debug_mode(monkeypatch, capsys):
    data = {
        "paychecks": [],
        "bills": [
            {
                "name": "Big bill",
                "amount": 100.0,
                "date": date.today().isoformat(),
            }
        ],
        "debts": [],
    }

    inputs = iter(["1", "0", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    fin.run_simulation(data, debug=True)
    out = capsys.readouterr().out
    assert "<<< LOW BALANCE" in out
