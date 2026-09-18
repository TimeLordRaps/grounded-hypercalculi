"""Real Analysis Calculus: continuum foundations, Dedekind cuts, Cauchy sequences, and surreal numbers."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

# Denominators up to 2**_MAX_DYADIC_EXPONENT are searched when the simplicity
# rule needs a dyadic rational. Beyond 2**52 a float cannot represent the
# distinct candidates anyway, so the search refuses rather than rounding.
_MAX_DYADIC_EXPONENT = 52
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
        """Whether a rational lies in the lower cut L = {x : x < r}.

        With a ``cut_predicate`` the cut knows its own membership and answers
        directly.

        Without one it knows only that the real ``r`` lies somewhere in
        ``[lower_bound, upper_bound]``, and that settles membership only outside
        that interval: ``q < lower_bound <= r`` puts q in L, and
        ``q >= upper_bound >= r`` keeps it out. For q inside the interval the
        answer depends on where r actually falls, which the cut does not record.

        This previously returned ``val < self.lower_bound``, which answered False
        across the whole interval -- including for rationals below r, which are
        in L. That reported an undetermined membership as a settled exclusion.

        Raises:
            ValueError: q lies in the undetermined interval of a cut carrying no
                predicate. Narrow the bounds or supply a ``cut_predicate``.
        """
        val = q.to_float() if isinstance(q, GroundedRational) else float(q)
        if self.cut_predicate is not None:
            return self.cut_predicate(val)
        if val < self.lower_bound:
            return True
        if val >= self.upper_bound:
            return False
        raise ValueError(
            f"membership of {val} is undetermined: this cut records only that the "
            f"real lies in [{self.lower_bound}, {self.upper_bound}], and {val} is "
            f"inside that interval. Supply a cut_predicate, or tighten the bounds."
        )

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
        """Value of the game under Conway's simplicity rule.

        The value of ``{L | R}`` is the *simplest* number strictly between
        ``max(L)`` and ``min(R)``: zero if it lies in the gap, else the integer
        of least magnitude in the gap, else the dyadic rational with the smallest
        denominator in it.

        This was previously the midpoint ``(max(L) + min(R)) / 2`` with
        ``max(L) + 1`` and ``min(R) - 1`` for one-sided games. Those agree with
        the simplicity rule on the canonical constructions -- ``{|} = 0``,
        ``{0|} = 1``, ``{0|1} = 1/2`` -- and diverge elsewhere: ``{1 | 4}`` has
        value 2, not 2.5, and ``{-5 | }`` has value 0, not -4, because 0 is
        simpler than every number in the gap and lies in it.

        Raises:
            ValueError: the game is not a number, or the gap admits no dyadic
                rational within the searched denominators.
        """
        if not self.is_number:
            raise ValueError("Not a valid numeric surreal number: left contains elements >= right")

        low = max(self.left) if self.left else None
        high = min(self.right) if self.right else None

        # Zero is the simplest number there is; take it whenever the gap holds it.
        if (low is None or low < 0.0) and (high is None or high > 0.0):
            return 0.0

        # Otherwise the gap lies wholly on one side of zero, so the least-magnitude
        # integer in it is the next integer inward from the bound nearest zero.
        if high is None:
            return float(math.floor(low) + 1)
        if low is None:
            return float(math.ceil(high) - 1)
        if low >= 0.0:
            candidate = math.floor(low) + 1
            if candidate < high:
                return float(candidate)
        else:
            candidate = math.ceil(high) - 1
            if candidate > low:
                return float(candidate)

        # No integer fits; find the dyadic with the smallest denominator that does.
        for exponent in range(1, _MAX_DYADIC_EXPONENT + 1):
            denominator = 2**exponent
            numerator = math.floor(low * denominator) + 1
            candidate_value = numerator / denominator
            if low < candidate_value < high:
                return candidate_value
        raise ValueError(
            f"no dyadic rational with denominator up to 2**{_MAX_DYADIC_EXPONENT} lies "
            f"strictly between {low} and {high}; the gap is narrower than this "
            f"float-valued representation can resolve"
        )

    @classmethod
    def infinitesimal(cls) -> SurrealGame:
        """A finite truncation of epsilon = { 0 | 1, 1/2, 1/4, ... }.

        Returns ``{0 | 1, 1/2, 1/4}``, whose value under the simplicity rule is
        1/8. That is a dyadic rational, not an infinitesimal: it is larger than
        many positive reals, which epsilon is not.

        A genuine infinitesimal needs the full infinite right set, and the
        options here are ``float``, so no such game is representable by this
        class. Read this as the third stage of the sequence of games converging
        on epsilon, not as epsilon.
        """
        return cls(left=(0.0,), right=(1.0, 0.5, 0.25))


@dataclass(frozen=True)
class CauchySequence:
    """A Cauchy sequence of rationals generating a real number."""
    generator: Callable[[int], GroundedRational]

    def term(self, n: int) -> GroundedRational:
        if n < 0:
            raise ValueError("Term index must be non-negative")
        return self.generator(n)

    def is_cauchy(
        self,
        tolerance: float = 1e-4,
        test_terms: int = 15,
        window: int = 10,
        max_start: int = 1024,
    ) -> bool:
        """Report whether some sampled window of late terms stays within tolerance.

        The Cauchy criterion is ``for all eps > 0 there exists N such that
        |a_m - a_n| < eps for all m, n >= N``. Both quantifiers are infinite, so
        no finite computation settles it. This method samples: it tries start
        indices ``test_terms, 2 * test_terms, 4 * test_terms, ...`` up to
        ``max_start`` and returns True at the first one whose ``window``
        consecutive terms all lie within ``tolerance`` of one another.

        Neither answer is a proof, and it is worth being exact about why.

        A True is evidence, not a certificate. A sequence that grows slowly
        enough passes at any fixed tolerance and still diverges: ``a_n = n * 1e-6``
        varies by 9e-6 across the default window and increases without bound.

        A False is not a refutation either. It says no start index up to
        ``max_start`` produced a quiet window, which leaves open that a later one
        would. The previous implementation examined only the single start index
        ``test_terms`` and so answered False for ``a_n = 1/(n + 1)``, which is
        Cauchy; searching upward answers True for it, but the asymmetry of the
        criterion is unchanged.

        For a sequence whose convergence actually matters, supply a proof or a
        modulus of convergence; this is a screen.

        Args:
            tolerance: The epsilon at which the window is judged.
            test_terms: First start index tried.
            window: How many consecutive terms make up a window.
            max_start: Largest start index tried before giving up.
        """
        if tolerance <= 0:
            raise ValueError("Tolerance must be positive")
        if window < 2:
            raise ValueError("A window must contain at least two terms")
        start = max(test_terms, 0)
        while True:
            terms = [self.term(i).to_float() for i in range(start, start + window)]
            if max(terms) - min(terms) < tolerance:
                return True
            if start >= max_start:
                return False
            start = max(start * 2, 1)

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
