from event_scheduler import forecast_events


def main():
    """Run a 60-day event-based debt forecast."""
    start_balance = 100

    bills = [
        {"name": "Phone", "amount": 50, "date": "2025-08-20"},
        {"name": "Rent", "amount": 800, "date": "2025-09-01"},
        {"name": "Insurance", "amount": 100, "date": "2025-09-10"},
    ]

    incomes = [
        {"name": "Paycheck", "amount": 1100, "date": "2025-08-12"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-08-26"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-09-09"},
        {"name": "Paycheck", "amount": 1100, "date": "2025-09-23"},
    ]

    debts = [
        {"name": "Credit Card", "balance": 500, "minimum_payment": 25, "apr": 20.0, "due_day": 15},
        {"name": "Loan", "balance": 1000, "minimum_payment": 50, "apr": 5.0, "due_day": 5},
    ]

    events, debts_after = forecast_events(start_balance, bills, incomes, debts, days=60)

    for ev in events:
        print(
            f"{ev['date']} | Balance: ${ev['balance']:.2f} | "
            f"Bills: ${ev['bills']:.2f} | Minimums: ${ev['minimums']:.2f} | Extra: ${ev['extra']:.2f}"
        )

    print("\nRemaining debt balances after 60 days:")
    for d in debts_after:
        print(f"  {d['name']}: ${d['balance']:.2f}")


if __name__ == "__main__":
    main()
