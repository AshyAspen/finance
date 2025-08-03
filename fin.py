import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, getcontext

# Use Decimal for precise financial calculations
getcontext().prec = 10

def get_paydays_in_month(year, month, pay_cycle_start_date, frequency_weeks):
    """
    Calculates the number of paydays for a specific month.

    Args:
        year (int): The year of the month to check.
        month (int): The month number (1-12) to check.
        pay_cycle_start_date (date): A known date of a paycheck.
        frequency_weeks (int): The number of weeks in the pay cycle (e.g., 2 for bi-weekly).

    Returns:
        int: The number of paydays in the specified month.
    """
    paydays = 0
    p_date = pay_cycle_start_date
    
    # Find the first payday that is on or after the month we are looking for.
    while p_date.year < year or (p_date.year == year and p_date.month < month):
        p_date += relativedelta(weeks=frequency_weeks)
        
    p_date -= relativedelta(weeks=frequency_weeks)

    # Now, iterate forward and count any paydays that fall within the target month.
    while True:
        p_date += relativedelta(weeks=frequency_weeks)
        if p_date.year == year and p_date.month == month:
            paydays += 1
        elif p_date.year > year or (p_date.year == year and p_date.month > month):
            break
            
    return paydays

def calculate_avalanche_plan(bills, incomes, debts, forecast_months):
    """Calculate a debt avalanche payment plan based on monthly surplus."""
    # --- Data Initialization ---
    for debt in debts:
        debt['balance'] = Decimal(str(debt['balance']))
        debt['minimum_payment'] = Decimal(str(debt['minimum_payment']))
        debt['apr'] = Decimal(str(debt['apr']))
        debt['paid_off'] = False

    payment_schedule = []
    total_interest_paid = Decimal('0')
    
    current_date = datetime.date.today().replace(day=1)
    end_date = current_date + relativedelta(months=forecast_months)
    
    # --- Main Monthly Simulation Loop ---
    month_count = 0
    while any(not d['paid_off'] for d in debts) and current_date < end_date:
        month_count += 1
        
        # --- 1. Calculate Accurate Monthly Income ---
        monthly_income = Decimal('0')
        for income in incomes:
            amount = Decimal(str(income['amount']))
            if income['frequency'] == 'monthly':
                monthly_income += amount
            elif income['frequency'] in ['bi-weekly', 'weekly']:
                freq_weeks = 2 if income['frequency'] == 'bi-weekly' else 1
                start_date = datetime.datetime.strptime(income['start_date'], '%Y-%m-%d').date()
                num_paydays = get_paydays_in_month(current_date.year, current_date.month, start_date, freq_weeks)
                monthly_income += amount * num_paydays

        monthly_bills = sum(Decimal(str(b['amount'])) for b in bills)
        cash_for_debts = monthly_income - monthly_bills
        
        # --- 2. Apply Interest and Sort Debts for Avalanche ---
        active_debts = sorted(
            [d for d in debts if not d['paid_off']], key=lambda x: x['apr'], reverse=True
        )
        
        if not active_debts:
            break

        monthly_payments = {}
        for debt in active_debts:
            monthly_interest = debt['balance'] * (debt['apr'] / Decimal('100') / Decimal('12'))
            debt['balance'] += monthly_interest
            total_interest_paid += monthly_interest
            monthly_payments[debt['name']] = {'interest': monthly_interest, 'payment': Decimal('0')}

        # --- 3. Distribute Payments with Avalanche Logic ---
        available_for_payments = cash_for_debts
        target_debt = active_debts[0]

        # First, pay minimums on all NON-TARGET debts
        for debt in active_debts:
            if debt != target_debt:
                # Pay the minimum, but not more than the balance or what's available
                payment_amount = min(debt['minimum_payment'], debt['balance'])
                actual_payment = min(available_for_payments, payment_amount)
                
                debt['balance'] -= actual_payment
                available_for_payments -= actual_payment
                monthly_payments[debt['name']]['payment'] = actual_payment
                
                if debt['balance'] <= 0:
                    debt['paid_off'] = True

        # Second, the ENTIRE remaining amount goes to the target debt
        if target_debt and not target_debt['paid_off']:
            target_payment_amount = min(available_for_payments, target_debt['balance'])
            target_debt['balance'] -= target_payment_amount
            monthly_payments[target_debt['name']]['payment'] = target_payment_amount
            
            if target_debt['balance'] <= 0:
                target_debt['paid_off'] = True


        # --- 4. Record the Month's Activity ---
        payment_schedule.append({
            'month': month_count,
            'date': current_date.strftime('%B %Y'),
            'details': monthly_payments,
            'remaining_balances': {d['name']: d['balance'] for d in debts}
        })
        current_date += relativedelta(months=1)
        
    return payment_schedule, total_interest_paid


def daily_avalanche_schedule(current_balance, bills, incomes, debts, days=60):
    """Return daily balances and debt payments for the next ``days`` days."""

    start_date = datetime.date.today()
    balance = Decimal(str(current_balance))

    daily_minimums = {}
    for debt in debts:
        debt['balance'] = Decimal(str(debt['balance']))
        debt['minimum_payment'] = Decimal(str(debt['minimum_payment']))
        debt['apr'] = Decimal(str(debt['apr']))
        daily_minimums[debt['name']] = debt['minimum_payment'] / Decimal('30')

    daily_bills = sum(Decimal(str(b['amount'])) for b in bills) / Decimal('30')

    paydates: dict[datetime.date, list[Decimal]] = {}
    end_date = start_date + datetime.timedelta(days=days)
    for income in incomes:
        amount = Decimal(str(income['amount']))
        freq_weeks = 2 if income['frequency'] == 'bi-weekly' else 1
        pay_date = datetime.datetime.strptime(income['start_date'], "%Y-%m-%d").date()
        while pay_date < end_date:
            if pay_date >= start_date:
                paydates.setdefault(pay_date, []).append(amount)
            pay_date += relativedelta(weeks=freq_weeks)

    schedule = []
    for offset in range(days):
        current_date = start_date + datetime.timedelta(days=offset)

        for amt in paydates.get(current_date, []):
            balance += amt

        payments = {}

        balance -= daily_bills

        for debt in debts:
            if debt['balance'] <= 0:
                continue
            min_pay = min(daily_minimums[debt['name']], debt['balance'])
            balance -= min_pay
            debt['balance'] -= min_pay
            payments[debt['name']] = min_pay

        future_paydates = [d for d in paydates if d > current_date]
        next_pay = min(future_paydates) if future_paydates else end_date
        days_until_next_pay = (next_pay - current_date).days
        daily_required = daily_bills + sum(
            min(daily_minimums[d['name']], d['balance']) for d in debts if d['balance'] > 0
        )
        buffer = daily_required * days_until_next_pay
        extra = balance - buffer
        if extra > 0:
            active_debts = [d for d in debts if d['balance'] > 0]
            if active_debts:
                target = max(active_debts, key=lambda x: x['apr'])
                extra_payment = min(extra, target['balance'])
                balance -= extra_payment
                target['balance'] -= extra_payment
                payments[target['name']] = payments.get(target['name'], Decimal('0')) + extra_payment

        schedule.append(
            {
                'date': current_date.isoformat(),
                'balance': balance,
                'payments': payments,
            }
        )

    return schedule

def main():
    """Prompt for balance and show 60-day avalanche payment forecast."""
    print("---  Debt Avalanche Forecaster ---")

    current_balance = Decimal(input("Enter current account balance: ").strip())

    bills = [
        {'name': 'Rent', 'amount': 200.00},
        {'name': 'Student Loan', 'amount': 184.86},
        {'name': 'Car Insurance', 'amount': 206.33},
        {'name': 'iCloud', 'amount': 9.99},
        {'name': 'Copilot', 'amount': 13.00},
        {'name': 'HP Instant Ink', 'amount': 8.43},
        {'name': 'ChatGPT', 'amount': 20.00},
        {'name': 'Gas', 'amount': 150.00},
        {'name': 'Food', 'amount': 200.00},
        {'name': 'Medications', 'amount': 50.97},
        {'name': 'Tests', 'amount': 20.53},
    ]

    incomes = [
        {
            'name': 'Paycheck',
            'amount': 1100.00,
            'frequency': 'bi-weekly',
            'start_date': '2025-08-12',
        },
    ]

    debts = [
        {'name': 'iPhone Installment', 'balance': 919.44, 'minimum_payment': 54.08, 'apr': 0.0},
        {'name': 'Patient Fi Loan', 'balance': 1555.00, 'minimum_payment': 64.80, 'apr': 0.0},
        {'name': 'Citi Card', 'balance': 1925.00, 'minimum_payment': 20.00, 'apr': 23.24},
        {'name': 'Apple Card', 'balance': 4145.93, 'minimum_payment': 119.00, 'apr': 26.24},
        {'name': 'Alpheon Loan', 'balance': 5195.00, 'minimum_payment': 153.00, 'apr': 0.0},
        {'name': 'Auto Loan', 'balance': 25970.64, 'minimum_payment': 463.11, 'apr': 8.5},
    ]

    schedule = daily_avalanche_schedule(current_balance, bills, incomes, debts, days=60)

    print("\n--- 60-Day Payment Plan ---")
    for day in schedule:
        if day['payments']:
            pays = ", ".join(
                f"{name}: ${amount:.2f}" for name, amount in day['payments'].items()
            )
            print(f"{day['date']}: balance=${day['balance']:.2f} | payments -> {pays}")
        else:
            print(f"{day['date']}: balance=${day['balance']:.2f}")

    print("\nRemaining Balances:")
    for debt in debts:
        print(f" - {debt['name']}: ${debt['balance']:.2f}")

if __name__ == "__main__":
    main()
