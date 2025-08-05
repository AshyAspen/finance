"""Minimum payment formulas."""

from .apple_card import calculate as apple_card
from .credit_card import calculate as credit_card

__all__ = ["apple_card", "credit_card"]
