from datetime import date, timedelta
from decimal import Decimal

def calculate_interest(purchases, payments, statement_start, statement_end, apr):
    """
    Calculate interest for a statement period.

    purchases: List of (amount, date) tuples for purchases.
    payments: List of (amount, date) tuples for payments.
    statement_start: Start date of the statement period.
    statement_end: End date of the statement period.
    apr: Annual percentage rate (as a Decimal, e.g. Decimal('19.99')).
    """
    # Build daily balance
    balance = Decimal("0")
    daily_balances = []
    current_date = statement_start

    # Sort transactions by date
    purchases = sorted(purchases, key=lambda x: x[1])
    payments = sorted(payments, key=lambda x: x[1])

    purchase_idx = 0
    payment_idx = 0

    while current_date <= statement_end:
        # Add purchases for the day
        while purchase_idx < len(purchases) and purchases[purchase_idx][1] == current_date:
            balance += Decimal(str(purchases[purchase_idx][0]))
            purchase_idx += 1
        # Subtract payments for the day
        while payment_idx < len(payments) and payments[payment_idx][1] == current_date:
            balance -= Decimal(str(payments[payment_idx][0]))
            payment_idx += 1
        daily_balances.append(balance)
        current_date += timedelta(days=1)

    # Calculate average daily balance
    avg_daily_balance = sum(daily_balances) / Decimal(len(daily_balances))

    # Calculate interest: (APR / 365) * avg_daily_balance * number of days
    interest = (apr / Decimal("100") / Decimal("365")) * avg_daily_balance * Decimal(len(daily_balances))
    return interest.quantize(Decimal("0.01"))

# Example usage:
# purchases = [(100, date(2025, 7, 5)), (50, date(2025, 7, 10))]
# payments = [(80, date(2025, 7, 15))]
# interest = calculate_interest(purchases, payments, date(2025, 7, 1), date(2025, 7, 31), Decimal("19.99"))