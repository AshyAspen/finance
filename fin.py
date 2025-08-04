"""Interactive finance tool with editing and simulation options."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import json

from avalanche import daily_avalanche_schedule


DATA_FILE = Path(__file__).with_name("financial_data.json")


def load_data() -> dict:
    with DATA_FILE.open() as f:
        return json.load(f)


def save_data(data: dict) -> None:
    with DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)


def edit_section(section: str, fields: list[str], numeric_fields: set[str]) -> None:
    """Generic editor for paychecks, bills, or debts."""

    data = load_data()
    items = data.setdefault(section, [])
    while True:
        print(f"\nCurrent {section}:")
        for i, item in enumerate(items):
            print(f"  {i}: {item}")
        choice = input("Enter index to edit, 'a' to add, 'd' to delete, or blank to return: ").strip()
        if not choice:
            break
        if choice == "a":
            entry = {}
            for field in fields:
                val = input(f"{field}: ").strip()
                if field in numeric_fields:
                    val = float(val)
                entry[field] = val
            items.append(entry)
        elif choice == "d":
            idx = int(input("Index to delete: ").strip() or -1)
            if 0 <= idx < len(items):
                items.pop(idx)
        elif choice.isdigit() and int(choice) < len(items):
            idx = int(choice)
            entry = items[idx]
            for field in fields:
                current = entry.get(field, "")
                val = input(f"{field} [{current}]: ").strip()
                if val:
                    entry[field] = float(val) if field in numeric_fields else val
        else:
            print("Invalid selection.")
    save_data(data)


def run_simulation() -> None:
    """Run the avalanche debt payoff simulation."""

    print("---  Debt Avalanche Forecaster ---")
    days_str = input("Enter number of days to simulate [60]: ").strip()
    days = int(days_str) if days_str else 60
    start_balance = Decimal(input("Enter current account balance: ").strip())

    data = load_data()
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


def main() -> None:
    while True:
        print("\n--- Finance Menu ---")
        print("1) Edit income")
        print("2) Edit bills")
        print("3) Edit debt")
        print("4) Run simulation")
        print("5) Quit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            edit_section("paychecks", ["name", "amount", "date", "frequency"], {"amount"})
        elif choice == "2":
            edit_section("bills", ["name", "amount", "date"], {"amount"})
        elif choice == "3":
            edit_section(
                "debts",
                ["name", "balance", "minimum_payment", "apr", "due_date"],
                {"balance", "minimum_payment", "apr"},
            )
        elif choice == "4":
            run_simulation()
        elif choice in {"5", "q", "Q"}:
            break


if __name__ == "__main__":
    main()

