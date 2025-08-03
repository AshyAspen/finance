from collections import defaultdict
from datetime import date
from decimal import Decimal
from avalanche import daily_avalanche_schedule


def main() -> None:
    """Run a 60-day event-based debt forecast using the avalanche scheduler."""
    print("---  Debt Avalanche Forecaster ---")
    start_balance = Decimal(input("Enter current account balance: ").strip())


    today = date.today()
    month_start = today.replace(day=1)
    next_month_start = date(month_start.year + (month_start.month // 12), (month_start.month % 12) + 1, 1)

    bills = [
        {"name": "Rent", "amount": 200.00, "date": month_start.replace(day=1).isoformat()},
        {"name": "Student Loan", "amount": 184.86, "date": month_start.replace(day=5).isoformat()},
        {"name": "Car Insurance", "amount": 206.33, "date": month_start.replace(day=10).isoformat()},
        {"name": "iCloud", "amount": 9.99, "date": month_start.replace(day=15).isoformat()},
        {"name": "Copilot", "amount": 13.00, "date": month_start.replace(day=20).isoformat()},
        {"name": "HP Instant Ink", "amount": 8.43, "date": month_start.replace(day=25).isoformat()},
        {"name": "ChatGPT", "amount": 20.00, "date": next_month_start.replace(day=1).isoformat()},
        {"name": "Gas", "amount": 150.00, "date": next_month_start.replace(day=5).isoformat()},
        {"name": "Food", "amount": 200.00, "date": next_month_start.replace(day=10).isoformat()},
        {"name": "Medications", "amount": 50.97, "date": next_month_start.replace(day=15).isoformat()},
        {"name": "Tests", "amount": 20.53, "date": next_month_start.replace(day=20).isoformat()},
    ]

    paychecks = [
        {
            "name": "Paycheck",
            "amount": 1100.00,
            "date": date(2025, 7, 29).isoformat(),
            "frequency": "biweekly",
        },
    ]

    debts = [
        {
            "name": "iPhone Installment",
            "balance": 919.44,
            "minimum_payment": 54.08,
            "apr": 0.0,
            "due_date": month_start.replace(day=28).isoformat(),
        },
        {
            "name": "Patient Fi Loan",
            "balance": 1555.00,
            "minimum_payment": 64.80,
            "apr": 0.0,
            "due_date": next_month_start.replace(day=2).isoformat(),
        },
        {
            "name": "Citi Card",
            "balance": 1925.00,
            "minimum_payment": 20.00,
            "apr": 23.24,
            "due_date": month_start.replace(day=25).isoformat(),
        },
        {
            "name": "Apple Card",
            "balance": 4145.93,
            "minimum_payment": 119.00,
            "apr": 26.24,
            "due_date": next_month_start.replace(day=7).isoformat(),
        },
        {
            "name": "Alpheon Loan",
            "balance": 5195.00,
            "minimum_payment": 153.00,
            "apr": 0.0,
            "due_date": next_month_start.replace(day=15).isoformat(),
        },
        {
            "name": "Auto Loan",
            "balance": 25970.64,
            "minimum_payment": 463.11,
            "apr": 8.5,
            "due_date": next_month_start.replace(day=20).isoformat(),
        },
    ]

    schedule, debts_after = daily_avalanche_schedule(
        start_balance, paychecks, bills, debts
    )

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

    print("\nRemaining debt balances after 60 days:")
    for d in debts_after:
        due = d.get("next_due_date")
        due_str = due.isoformat() if due else "N/A"
        print(f"  {d['name']}: ${d['balance']:.2f} (next due {due_str})")


if __name__ == "__main__":
    main()
