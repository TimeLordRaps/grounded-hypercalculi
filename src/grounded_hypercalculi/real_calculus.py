"""Real Analysis Calculus: continuum foundations, Dedekind cuts, Cauchy sequences, and surreal numbers."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class GroundedRational:
    """Exact rational number p/q."""
    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        if self.denominator == 0:
            raise ZeroDivisionError("Denominator cannot be zero")
        frac = Fraction(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", frac.numerator)
        object.__setattr__(self, "denominator", frac.denominator)

    def to_float(self) -> float:
        return self.numerator / self.denominator

    def __add__(self, other: GroundedRational) -> GroundedRational:
        return GroundedRational(
            self.numerator * other.denominator + other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def __sub__(self, other: GroundedRational) -> GroundedRational:
        return GroundedRational(
            self.numerator * other.denominator - other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def __mul__(self, other: GroundedRational) -> GroundedRational:
        return GroundedRational(
            self.numerator * other.numerator,
            self.denominator * other.denominator,
        )

    def __truediv__(self, other: GroundedRational) -> GroundedRational:
        if other.numerator == 0:
            raise ZeroDivisionError("Cannot divide by zero rational")
        return GroundedRational(
            self.numerator * other.denominator,
            self.denominator * other.numerator,
        )

    def __lt__(self, other: GroundedRational) -> bool:
        if not isinstance(other, GroundedRational):
            return NotImplemented
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other: GroundedRational) -> bool:
        if not isinstance(other, GroundedRational):
            return NotImplemented
        return self.numerator * other.denominator <= other.numerator * self.denominator

    def __gt__(self, other: GroundedRational) -> bool:
        if not isinstance(other, GroundedRational):
            return NotImplemented
        return self.numerator * other.denominator > other.numerator * self.denominator

    def __ge__(self, other: GroundedRational) -> bool:
        if not isinstance(other, GroundedRational):
            return NotImplemented
        return self.numerator * other.denominator >= other.numerator * self.denominator


@dataclass(frozen=True)
class DedekindCut:
    """A real number represented as a Dedekind cut (L, R) of rationals."""
    lower_bound: float
    upper_bound: float
    cut_predicate: Optional[Callable[[float], bool]] = None

    @property
    def midpoint(self) -> float:
        return (self.lower_bound + self.upper_bound) / 2.0

    def approximate(self) -> float:
        return self.midpoint

    def contains(self, q: GroundedRational | float) -> bool:
        """Check if a rational or value is in the lower cut L."""
        val = q.to_float() if isinstance(q, GroundedRational) else float(q)
        if self.cut_predicate is not None:
            return self.cut_predicate(val)
        return val < self.lower_bound

    @classmethod
    def sqrt_two(cls, precision: float = 1e-4) -> DedekindCut:
        """Construct a Dedekind cut bounding sqrt(2)."""
        low, high = 1.0, 2.0
        while high - low > precision:
            mid = (low + high) / 2.0
            if mid * mid < 2.0:
                low = mid
            else:
                high = mid
        return cls(
            lower_bound=low,
            upper_bound=high,
            cut_predicate=lambda x: x <= 0 or x * x < 2.0,
        )


@dataclass(frozen=True)
class SurrealGame:
    """A Conway Surreal Number {L | R} supporting transfinite and infinitesimal quantities."""
    left: Tuple[float, ...] = ()
    right: Tuple[float, ...] = ()

    @property
    def is_number(self) -> bool:
        """A game is a surreal number iff no member of left is >= any member of right."""
        if not self.left or not self.right:
            return True
        return all(l < r for l in self.left for r in self.right)

    @property
    def value(self) -> float:
        """Numeric value of a standard surreal game."""
        if not self.is_number:
            raise ValueError("Not a valid numeric surreal number: left contains elements >= right")
        l_max = max(self.left) if self.left else 0.0
        r_min = min(self.right) if self.right else 0.0
        if not self.left and not self.right:
            return 0.0
        if self.left and not self.right:
            return l_max + 1.0
        if not self.left and self.right:
            return r_min - 1.0
        return (l_max + r_min) / 2.0

    @classmethod
    def infinitesimal(cls) -> SurrealGame:
        """The canonical infinitesimal epsilon = { 0 | 1, 1/2, 1/4, ... }."""
        return cls(left=(0.0,), right=(1.0, 0.5, 0.25))


@dataclass(frozen=True)
class CauchySequence:
    """A Cauchy sequence of rationals generating a real number."""
    generator: Callable[[int], GroundedRational]

    def term(self, n: int) -> GroundedRational:
        if n < 0:
            raise ValueError("Term index must be non-negative")
        return self.generator(n)

    def is_cauchy(self, tolerance: float = 1e-4, test_terms: int = 15) -> bool:
        """Verify the Cauchy criterion |a_m - a_n| < epsilon for late terms."""
        terms = [self.term(i).to_float() for i in range(test_terms, test_terms + 10)]
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                if abs(terms[i] - terms[j]) >= tolerance:
                    return False
        return True

    def limit(self, n: int = 30) -> float:
        """Approximate the real limit of the Cauchy sequence."""
        return self.term(n).to_float()

    @classmethod
    def euler_e(cls) -> CauchySequence:
        """Construct the Cauchy sequence for Euler's e = sum_{k=0}^n 1/k!."""
        def e_term(n: int) -> GroundedRational:
            val = GroundedRational(1, 1)
            fact = 1
            for k in range(1, n + 1):
                fact *= k
                val = val + GroundedRational(1, fact)
            return val
        return cls(generator=e_term)

    @classmethod
    def geometric_series(cls, ratio: GroundedRational) -> CauchySequence:
        """Construct Cauchy sequence for geometric series sum_{k=0}^n r^k."""
        def geom_term(n: int) -> GroundedRational:
            total = GroundedRational(0, 1)
            power = GroundedRational(1, 1)
            for _ in range(n + 1):
                total = total + power
                power = power * ratio
            return total
        return cls(generator=geom_term)



def numerical_derivative(f: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    """Central difference derivative: (f(x+h) - f(x-h)) / (2h)."""
    if h <= 0:
        raise ValueError("Step size h must be positive")
    return (f(x + h) - f(x - h)) / (2.0 * h)


def riemann_integral(f: Callable[[float], float], a: float, b: float, subdivisions: int = 1000) -> float:
    """Riemann midpoint integration of f over [a, b]."""
    if subdivisions <= 0:
        raise ValueError("Subdivisions must be positive")
    h = (b - a) / subdivisions
    total = sum(f(a + (i + 0.5) * h) for i in range(subdivisions))
    return total * h
