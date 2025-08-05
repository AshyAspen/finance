import math

def appleCardMinimumPayment(
    statement_balance,
    interest_accrued,
    installment_payments,
    daily_cash_adjustments
    ):
    # Calculate 1% of statement balance
    one_percent_balance = statement_balance * 0.01

    # Sum daily cash adjustments
    daily_cash_adj_total = sum(daily_cash_adjustments)

    # Calculate the sum as per agreement
    payment_sum = one_percent_balance + interest_accrued + daily_cash_adj_total

    # Round up to the nearest dollar
    rounded_sum = math.ceil(payment_sum)

    # Add installment payments
    final_minimum_payment = rounded_sum + installment_payments

    return final_minimum_payment