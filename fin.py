from decimal import Decimal
from avalanche import daily_avalanche_schedule


def main() -> None:
    """Run a 60-day event-based debt forecast using the avalanche scheduler."""
    print("---  Debt Avalanche Forecaster ---")
    start_balance = Decimal(input("Enter current account balance: ").strip())

    bills = [
        {"name": "Phone", "amount": 50, "date": "2025-08-20"},
        {"name": "Rent", "amount": 800, "date": "2025-09-01"},
        {"name": "Insurance", "amount": 100, "date": "2025-09-10"},
    ]

    paychecks = [
        {"name": "Paycheck", "amount": 1100, "date": "2025-08-12"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-08-26"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-09-09"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-09-23"},
    ]

    debts = [
        {
            "name": "Credit Card",
            "balance": 500,
            "apr": 20.0,
            "minimum_payment": 25,
            "due_date": "2025-08-15",
        },
        {
            "name": "Loan",
            "balance": 1000,
            "apr": 5.0,
            "minimum_payment": 50,
            "due_date": "2025-09-05",
        },
    ]

    schedule, debts_after = daily_avalanche_schedule(
        start_balance, paychecks, bills, debts
    )

    for ev in schedule:
        bills_paid = (-ev["amount"]) if ev["type"] == "bill" else Decimal("0")
        mins_paid = (-ev["amount"]) if ev["type"] == "debt_min" else Decimal("0")
        extra_paid = (-ev["amount"]) if ev["type"] == "extra" else Decimal("0")
        print(
            f"{ev['date']}: balance=${ev['balance']:.2f} "
            f"(bills=${bills_paid:.2f}, minimums=${mins_paid:.2f}, extra=${extra_paid:.2f})"
        )

    print("\nRemaining debt balances after 60 days:")
    for d in debts_after:
        print(f"  {d['name']}: ${d['balance']:.2f}")


if __name__ == "__main__":
    main()
