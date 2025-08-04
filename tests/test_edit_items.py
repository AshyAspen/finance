import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

import fin


def _mock_inputs(monkeypatch, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _: next(it))
    monkeypatch.setattr(fin, "save_data", lambda data: None)


def test_edit_paycheck(monkeypatch):
    data = {
        "paychecks": [
            {"name": "Job", "amount": 1000.0, "date": "2024-01-01", "frequency": "monthly"}
        ]
    }
    _mock_inputs(monkeypatch, [
        "e", "1", "Job2", "2000", "2024-02-01", "biweekly", "b"
    ])
    fin.edit_paychecks(data)
    p = data["paychecks"][0]
    assert p["name"] == "Job2"
    assert p["amount"] == 2000.0
    assert p["date"] == "2024-02-01"
    assert p["frequency"] == "biweekly"


def test_edit_bill(monkeypatch):
    data = {
        "bills": [{"name": "Rent", "amount": 100.0, "date": "2024-01-05"}],
        "debts": [
            {
                "name": "Card",
                "balance": 0.0,
                "minimum_payment": 0.0,
                "apr": 0.0,
                "due_date": "2024-01-10",
            }
        ],
    }
    _mock_inputs(monkeypatch, ["e", "1", "", "150", "", "1", "b"])
    fin.edit_bills(data)
    b = data["bills"][0]
    assert b["amount"] == 150.0
    assert b["debt"] == "Card"


def test_edit_debt(monkeypatch):
    data = {
        "debts": [
            {
                "name": "Card",
                "balance": 100.0,
                "minimum_payment": 10.0,
                "apr": 5.0,
                "due_date": "2024-01-10",
            }
        ]
    }
    _mock_inputs(monkeypatch, [
        "e", "1", "Card2", "150", "15", "7", "2024-02-10", "b"
    ])
    fin.edit_debts(data)
    d = data["debts"][0]
    assert d["name"] == "Card2"
    assert d["balance"] == 150.0
    assert d["minimum_payment"] == 15.0
    assert d["apr"] == 7.0
    assert d["due_date"] == "2024-02-10"


def test_edit_goal(monkeypatch, capsys):
    data = {"goals": [{"name": "Trip", "amount": 500.0, "date": "2024-12-01"}]}
    _mock_inputs(monkeypatch, ["e", "1", "Trip2", "600", "2025-01-01", "b"])
    fin.edit_goals(data)
    g = data["goals"][0]
    assert g["name"] == "Trip2"
    assert g["amount"] == 600.0
    assert g["date"] == "2025-01-01"
    out = capsys.readouterr().out.lower()
    assert "wants and goals" in out


def test_toggle_goal(monkeypatch):
    data = {
        "goals": [
            {
                "name": "Trip",
                "amount": 500.0,
                "date": "2024-12-01",
                "enabled": True,
            }
        ]
    }
    _mock_inputs(monkeypatch, ["t", "1", "b"])
    fin.edit_goals(data)
    g = data["goals"][0]
    assert g["enabled"] is False
    # Ensure details remain
    assert g["amount"] == 500.0
    assert g["date"] == "2024-12-01"
