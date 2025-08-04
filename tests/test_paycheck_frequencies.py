import os
import sys
from datetime import date, timedelta
from calendar import monthrange
from pathlib import Path

# Ensure project root on path for direct module imports
sys.path.insert(0, os.path.abspath(os.path.join(Path(__file__).resolve().parent, "..")))

from avalanche import daily_avalanche_schedule


def _add_month(d: date) -> date:
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def test_weekly_paychecks():
    today = date.today()
    paychecks = [{"amount": 100, "date": today.isoformat(), "frequency": "weekly"}]
    schedule, _, _ = daily_avalanche_schedule(0, paychecks, [], [], days=28)
    pay_dates = [ev["date"] for ev in schedule if ev["type"] == "paycheck"]
    expected = [today + timedelta(days=7 * i) for i in range(5)]
    assert pay_dates[:5] == expected


def test_biweekly_paychecks():
    today = date.today()
    paychecks = [{"amount": 100, "date": today.isoformat(), "frequency": "biweekly"}]
    schedule, _, _ = daily_avalanche_schedule(0, paychecks, [], [], days=42)
    pay_dates = [ev["date"] for ev in schedule if ev["type"] == "paycheck"]
    expected = [today + timedelta(days=14 * i) for i in range(4)]
    assert pay_dates[:4] == expected


def test_semi_monthly_paychecks():
    today = date.today()
    paychecks = [{"amount": 100, "date": today.isoformat(), "frequency": "semi-monthly"}]
    schedule, _, _ = daily_avalanche_schedule(0, paychecks, [], [], days=60)
    pay_dates = [ev["date"] for ev in schedule if ev["type"] == "paycheck"]
    first_day = today.day
    second = today.replace(day=min(first_day + 15, monthrange(today.year, today.month)[1]))
    next_month = _add_month(today)
    third = next_month.replace(day=min(first_day, monthrange(next_month.year, next_month.month)[1]))
    fourth = next_month.replace(day=min(first_day + 15, monthrange(next_month.year, next_month.month)[1]))
    expected = [today, second, third, fourth]
    assert pay_dates[:4] == expected
