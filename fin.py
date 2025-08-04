"""Command-line interface for managing finances and running simulations."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import json
from typing import Dict, List

from avalanche import daily_avalanche_schedule


DATA_FILE = Path(__file__).with_name("financial_data.json")


def load_data() -> Dict:
    """Load financial data from ``financial_data.json``."""
    if DATA_FILE.exists():
        with DATA_FILE.open() as f:
            return json.load(f)
    return {"paychecks": [], "bills": [], "debts": []}


def save_data(data: Dict) -> None:
    """Persist financial data to disk, including optional debt links."""
    with DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Editing helpers


def _delete_item(items: List[dict]) -> None:
    idx = input("Number to delete: ").strip()
    if idx.isdigit() and 1 <= int(idx) <= len(items):
        del items[int(idx) - 1]


def edit_paychecks(data: Dict) -> None:
    """Add or remove recurring income entries."""
    paychecks = data.setdefault("paychecks", [])
    while True:
        print("\nCurrent paychecks:")
        for i, p in enumerate(paychecks, 1):
            freq = p.get("frequency", "monthly")
            print(f"{i}. {p['name']} ${p['amount']} starting {p['date']} ({freq})")
        action = input("A)dd, E)dit, D)elete, B)ack: ").strip().lower()
        if action == "a":
            name = input("Name: ").strip() or "Paycheck"
            amount = float(input("Amount: ").strip())
            date = input("First date (YYYY-MM-DD): ").strip()
            freq = input("Frequency [monthly]: ").strip() or "monthly"
            paychecks.append(
                {"name": name, "amount": amount, "date": date, "frequency": freq}
            )
            save_data(data)
        elif action == "e":
            idx = input("Number to edit: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(paychecks):
                p = paychecks[int(idx) - 1]
                name = input(f"Name [{p['name']}]: ").strip() or p['name']
                amount = input(f"Amount [{p['amount']}]: ").strip()
                date = input(f"First date (YYYY-MM-DD) [{p['date']}]: ").strip() or p['date']
                freq = input(
                    f"Frequency [{p.get('frequency', 'monthly')}]: "
                ).strip() or p.get("frequency", "monthly")
                if amount:
                    p['amount'] = float(amount)
                p.update({"name": name, "date": date, "frequency": freq})
                save_data(data)
        elif action == "d":
            _delete_item(paychecks)
            save_data(data)
        elif action == "b":
            break


def edit_bills(data: Dict) -> None:
    """Add or remove bill entries."""
    bills = data.setdefault("bills", [])
    debts = data.get("debts", [])
    while True:
        print("\nCurrent bills:")
        for i, b in enumerate(bills, 1):
            debt_info = f" (debt: {b['debt']})" if b.get("debt") else ""
            print(f"{i}. {b['name']} ${b['amount']} due {b['date']}{debt_info}")
        action = input("A)dd, E)dit, D)elete, B)ack: ").strip().lower()
        if action == "a":
            name = input("Name: ").strip() or "Bill"
            amount = float(input("Amount: ").strip())
            date = input("Due date (YYYY-MM-DD): ").strip()
            debt = None
            if debts:
                while True:
                    print("Associate with debt? (0 for none)")
                    for i, d in enumerate(debts, 1):
                        print(f"{i}. {d['name']}")
                    choice = input("Debt number [0]: ").strip()
                    if not choice or choice == "0":
                        break
                    if choice.isdigit() and 1 <= int(choice) <= len(debts):
                        debt = debts[int(choice) - 1]["name"]
                        break
                    print("Invalid selection. Please try again.")
            bill = {"name": name, "amount": amount, "date": date}
            if debt:
                bill["debt"] = debt
            bills.append(bill)
            save_data(data)
        elif action == "e":
            idx = input("Number to edit: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(bills):
                b = bills[int(idx) - 1]
                name = input(f"Name [{b['name']}]: ").strip() or b['name']
                amount = input(f"Amount [{b['amount']}]: ").strip()
                date = input(f"Due date (YYYY-MM-DD) [{b['date']}]: ").strip() or b['date']
                b.update({"name": name, "date": date})
                if amount:
                    b['amount'] = float(amount)
                if debts:
                    while True:
                        print("Associate with debt? (0 for none)")
                        for i, d in enumerate(debts, 1):
                            print(f"{i}. {d['name']}")
                        current = next(
                            (i + 1 for i, d in enumerate(debts) if d['name'] == b.get('debt')),
                            0,
                        )
                        choice = input(f"Debt number [{current}]: ").strip()
                        if not choice:
                            choice = str(current)
                        if choice == "0":
                            b.pop("debt", None)
                            break
                        if choice.isdigit() and 1 <= int(choice) <= len(debts):
                            b["debt"] = debts[int(choice) - 1]["name"]
                            break
                        print("Invalid selection. Please try again.")
                save_data(data)
        elif action == "d":
            _delete_item(bills)
            save_data(data)
        elif action == "b":
            break


def edit_debts(data: Dict) -> None:
    """Add or remove debt entries."""
    debts = data.setdefault("debts", [])
    while True:
        print("\nCurrent debts:")
        for i, d in enumerate(debts, 1):
            print(
                f"{i}. {d['name']} balance ${d['balance']} min ${d['minimum_payment']} APR {d['apr']} due {d['due_date']}"
            )
        action = input("A)dd, E)dit, D)elete, B)ack: ").strip().lower()
        if action == "a":
            name = input("Name: ").strip() or "Debt"
            balance = float(input("Balance: ").strip())
            minimum = float(input("Minimum payment: ").strip())
            apr = float(input("APR: ").strip())
            due = input("Next due date (YYYY-MM-DD): ").strip()
            debts.append(
                {
                    "name": name,
                    "balance": balance,
                    "minimum_payment": minimum,
                    "apr": apr,
                    "due_date": due,
                }
            )
            save_data(data)
        elif action == "e":
            idx = input("Number to edit: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(debts):
                d = debts[int(idx) - 1]
                name = input(f"Name [{d['name']}]: ").strip() or d['name']
                balance = input(f"Balance [{d['balance']}]: ").strip()
                minimum = input(f"Minimum payment [{d['minimum_payment']}]: ").strip()
                apr = input(f"APR [{d['apr']}]: ").strip()
                due = input(
                    f"Next due date (YYYY-MM-DD) [{d.get('due_date', '')}]: "
                ).strip() or d.get("due_date", "")
                if balance:
                    d['balance'] = float(balance)
                if minimum:
                    d['minimum_payment'] = float(minimum)
                if apr:
                    d['apr'] = float(apr)
                d.update({"name": name, "due_date": due})
                save_data(data)
        elif action == "d":
            _delete_item(debts)
            save_data(data)
        elif action == "b":
            break


# ---------------------------------------------------------------------------
# Simulation


def run_simulation(data: Dict) -> None:
    """Run the avalanche debt payoff simulation."""
    print("---  Debt Avalanche Forecaster ---")
    days_str = input("Enter number of days to simulate [60]: ").strip()
    days = int(days_str) if days_str else 60
    start_balance = Decimal(input("Enter current account balance: ").strip())

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
            "debt_add": Decimal("0"),
            "names": defaultdict(list),
            "balance": Decimal("0"),
        }
    )
    for ev in schedule:
        day = ev["date"]
        d = daily[day]
        if ev["type"] not in d:
            d[ev["type"]] = Decimal("0")
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
        for cat in ["paycheck", "bill", "debt_min", "extra", "debt_add"]:
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
                    "debt_add": "Debt additions",
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


# ---------------------------------------------------------------------------
# Menu


def main() -> None:
    """Display the main menu and handle user selections."""
    data = load_data()
    while True:
        print("\n--- Finance Menu ---")
        print("1. Edit income")
        print("2. Edit bills")
        print("3. Edit debts")
        print("4. Run simulation")
        print("5. Quit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            edit_paychecks(data)
        elif choice == "2":
            edit_bills(data)
        elif choice == "3":
            edit_debts(data)
        elif choice == "4":
            run_simulation(data)
        elif choice == "5":
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()

