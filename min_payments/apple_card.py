from __future__ import annotations

"""Apple Card minimum payment formula."""

from datetime import date
from decimal import Decimal, ROUND_UP
from typing import Iterable, List


def apple_card_minimum_payment(
    statement_balance: Decimal,
    interest_accrued: Decimal,
    installment_payments: Decimal,
    daily_cash_adjustments: Iterable[Decimal],
) -> Decimal:
    """Return the minimum payment for an Apple Card statement.

    The calculation follows Apple's published rules: one percent of the
    statement balance plus any accrued interest and Daily Cash adjustments,
    rounded up to the nearest dollar, with installment payments added on top.
    """

    one_percent_balance = statement_balance * Decimal("0.01")
    daily_cash_total = sum(daily_cash_adjustments, Decimal("0"))
    payment_sum = one_percent_balance + interest_accrued + daily_cash_total
    rounded_sum = payment_sum.quantize(Decimal("1"), rounding=ROUND_UP)
    return rounded_sum + installment_payments


def calculate(debt, as_of: date) -> Decimal:
    """Compute the minimum payment for an Apple Card debt."""

    args = getattr(debt, "min_payment_args", {})
    statement_balance = Decimal(str(args.get("statement_balance", debt.balance)))
    interest_accrued = Decimal(str(args.get("interest_accrued", 0)))
    installments = args.get("installments", [])
    installment_payments = sum(
        Decimal(str(item.get("minimum_payment", 0))) for item in installments
    )
    daily_cash_adjustments: List[Decimal] = [
        Decimal(str(x)) for x in args.get("daily_cash_adjustments", [])
    ]

    payment = apple_card_minimum_payment(
        statement_balance,
        interest_accrued,
        installment_payments,
        daily_cash_adjustments,
    )
    if debt.balance < payment:
        payment = debt.balance
    return payment
