from datetime import date, timedelta
from decimal import Decimal

from avalanche import daily_avalanche_schedule


def test_goal_event_included():
    goal_date = date.today() + timedelta(days=7)
    goals = [{"name": "Tires", "amount": 500.0, "date": goal_date.isoformat()}]
    schedule, _, _ = daily_avalanche_schedule(1000, [], [], [], goals, days=10)
    assert any(
        ev["type"] == "goal"
        and ev["description"] == "Tires"
        and ev["date"] == goal_date
        and ev["amount"] == Decimal("-500")
        for ev in schedule
    )
