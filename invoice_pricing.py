
"""
invoice_pricing.py

Single concept: invoice pricing (subtotal -> discount -> tax -> total).

Highlights for 'Software Construction':
- One abstract concept per file (pricing).
- Useful comments document intent and contracts (not obvious code).
- No magic literals: use named constants (TAX_RATE, MAX_DISCOUNT_PCT).
- LSP: DiscountPolicy contract + PercentageDiscountPolicy subclass preserves it.
- Error handling: validate inputs, raise precise exceptions, resource-safety not needed here.
- Defensive semantics: pre/postconditions, immutability (frozen dataclass), exhaustive match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, NamedTuple, Protocol, Final, Literal


# ---- Constants (avoid magic literals) ----
TAX_RATE: Final[float] = 0.19          # 19% VAT; adjust per locale
MAX_DISCOUNT_PCT: Final[float] = 0.50  # 50% maximum discount cap


# ---- Contracts / Abstractions ----
class DiscountPolicy(Protocol):
    """
    Contract:
    - apply(subtotal) returns a non-negative discount <= subtotal.
    - Does not mutate caller state.
    """
    def apply(self, subtotal: float) -> float: ...


@dataclass(frozen=True)
class PercentageDiscountPolicy:
    """
    LSP-compliant implementation of DiscountPolicy.
    Preconditions/postconditions are identical to the base contract.
    """
    percent: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.percent <= MAX_DISCOUNT_PCT):
            raise ValueError("percent must be in [0.0, 0.50]")

    def apply(self, subtotal: float) -> float:
        if subtotal < 0.0:
            raise ValueError("subtotal must be >= 0.0")
        return subtotal * self.percent


class Item(NamedTuple):
    price: float
    qty: int


def currency_symbol(currency: Literal["USD", "EUR"]) -> str:
    """
    Exhaustive branching over allowed literals; default raises.
    Demonstrates 'exhaustive switch/match' semantics.
    """
    match currency:
        case "USD":
            return "$"
        case "EUR":
            return "€"
        case _:
            raise ValueError(f"Unsupported currency: {currency!r}")


def compute_total(items: Iterable[Item], discount: DiscountPolicy | None = None) -> float:
    """
    Compute final total given items, optional discount, and TAX_RATE.

    Preconditions:
    - items is not None.
    - Every item has price >= 0 and qty > 0.

    Postconditions:
    - Return value >= 0 and rounded to two decimals.
    """
    if items is None:
        raise ValueError("items cannot be None")

    subtotal = 0.0
    for it in items:
        if it.price < 0.0 or it.qty <= 0:
            raise ValueError(f"invalid item: {it!r}")
        subtotal += it.price * it.qty

    discount_value = discount.apply(subtotal) if discount else 0.0
    if not (0.0 <= discount_value <= subtotal):
        raise AssertionError("discount must be in [0, subtotal]")

    taxed = (subtotal - discount_value) * (1.0 + TAX_RATE)
    assert taxed >= 0.0, "post: total must be >= 0"
    return round(taxed, 2)


if __name__ == "__main__":
    items = [Item(10.0, 2), Item(4.5, 1)]
    policy = PercentageDiscountPolicy(0.10)  # 10% discount
    total = compute_total(items, policy)
    print(f"Total: {currency_symbol('USD')}{total}")
