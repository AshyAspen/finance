from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import json
from avalanche import daily_avalanche_schedule


def main() -> None:
    """Run an event-based debt forecast using the avalanche scheduler."""
    print("---  Debt Avalanche Forecaster ---")
    days_str = input("Enter number of days to simulate [60]: ").strip()
    days = int(days_str) if days_str else 60
    start_balance = Decimal(input("Enter current account balance: ").strip())

    data_file = Path(__file__).with_name("financial_data.json")
    with data_file.open() as f:
        data = json.load(f)

    paychecks = data.get("paychecks", [])
    bills = data.get("bills", [])
    debts = data.get("debts", [])

    try:
        schedule, debts_after = daily_avalanche_schedule(
            start_balance, paychecks, bills, debts, days=days
        )
    except ValueError as exc:
        print(f"Warning: {exc}")
        return

    # Summarize events by date
    daily = defaultdict(
        lambda: {
            "paycheck": Decimal("0"),
            "bill": Decimal("0"),
            "debt_min": Decimal("0"),
            "extra": Decimal("0"),
            "names": defaultdict(list),
            "balance": Decimal("0"),
        }
    )
    for ev in schedule:
        day = ev["date"]
        d = daily[day]
        d[ev["type"]] += ev["amount"]
        d["names"][ev["type"]].append((ev["description"], ev["amount"]))
        d["balance"] = ev["balance"]

    for day in sorted(daily):
        d = daily[day]
        print(
            f"{day}: balance=${d['balance']:.2f} "
            f"(income=${d['paycheck']:.2f}, bills=${-d['bill']:.2f}, "
            f"minimums=${-d['debt_min']:.2f}, extra=${-d['extra']:.2f})"
        )
        for cat in ["paycheck", "bill", "debt_min", "extra"]:
            if d["names"][cat]:
                items = ", ".join(
                    f"{name} ${(-amt if amt < 0 else amt):.2f}"
                    for name, amt in d["names"][cat]
                )
                label = {
                    "paycheck": "Income",
                    "bill": "Bills",
                    "debt_min": "Debt minimums",
                    "extra": "Extra",
                }[cat]
                print(f"  {label}: {items}")

    print(f"\nRemaining debt balances after {days} days:")
    for d in debts_after:
        paid = d.get("paid_off_date")
        if paid:
            print(
                f"  {d['name']}: ${d['balance']:.2f} (paid off {paid.isoformat()})"
            )
        else:
            due = d.get("next_due_date")
            due_str = due.isoformat() if due else "N/A"
            print(f"  {d['name']}: ${d['balance']:.2f} (next due {due_str})")


if __name__ == "__main__":
    main()
