"""Ordinal Calculus: exact transfinite arithmetic below omega^omega, differences, derivatives, and Veblen hierarchies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class BoundedOrdinal:
    """An ordinal below omega^omega represented in Cantor Normal Form as polynomial coefficients."""
    coefficients: Tuple[int, ...] = ()

    def __post_init__(self) -> None:
        coeffs = list(self.coefficients)
        while coeffs and coeffs[-1] == 0:
            coeffs.pop()
        object.__setattr__(self, "coefficients", tuple(coeffs))

    @classmethod
    def from_int(cls, n: int) -> BoundedOrdinal:
        if n < 0:
            raise ValueError("Ordinal must be non-negative")
        return cls((n,) if n > 0 else ())

    @property
    def is_zero(self) -> bool:
        return len(self.coefficients) == 0

    @property
    def is_finite(self) -> bool:
        return len(self.coefficients) <= 1

    def to_int(self) -> int:
        if not self.is_finite:
            raise ValueError("Transfinite ordinal cannot convert to finite integer")
        return self.coefficients[0] if self.coefficients else 0

    def __add__(self, other: BoundedOrdinal) -> BoundedOrdinal:
        if other.is_zero:
            return self
        deg_b = len(other.coefficients) - 1
        if deg_b >= len(self.coefficients):
            return other
        res = list(self.coefficients)
        res[:deg_b] = other.coefficients[:deg_b]
        res[deg_b] += other.coefficients[deg_b]
        return BoundedOrdinal(tuple(res))

    def left_sub(self, other: BoundedOrdinal) -> BoundedOrdinal:
        """Left subtraction: unique gamma such that other + gamma == self."""
        if other > self:
            raise ValueError("Cannot subtract larger ordinal from smaller ordinal")
        if other == self:
            return BoundedOrdinal()
        if other.is_zero:
            return self
        max_len = max(len(self.coefficients), len(other.coefficients))
        s_c = self.coefficients + (0,) * (max_len - len(self.coefficients))
        o_c = other.coefficients + (0,) * (max_len - len(other.coefficients))
        diff_k = 0
        for k in range(max_len - 1, -1, -1):
            if s_c[k] != o_c[k]:
                diff_k = k
                break
        res = list(s_c[:diff_k]) + [s_c[diff_k] - o_c[diff_k]]
        return BoundedOrdinal(tuple(res))

    def __lt__(self, other: BoundedOrdinal) -> bool:
        return (len(self.coefficients), self.coefficients[::-1]) < (
            len(other.coefficients), other.coefficients[::-1]
        )

    def __le__(self, other: BoundedOrdinal) -> bool:
        return self == other or self < other


OMEGA = BoundedOrdinal((0, 1))
ZERO = BoundedOrdinal(())
ONE = BoundedOrdinal((1,))


def ordinal_difference(F: Callable[[BoundedOrdinal], BoundedOrdinal], alpha: BoundedOrdinal) -> BoundedOrdinal:
    """Discrete difference operator Delta F(alpha) = F(alpha + 1) - F(alpha)."""
    alpha_succ = alpha + ONE
    f_succ = F(alpha_succ)
    f_curr = F(alpha)
    return f_succ.left_sub(f_curr)


def ordinal_derivative(F: Callable[[BoundedOrdinal], BoundedOrdinal], n_fixed_points: int = 3) -> List[BoundedOrdinal]:
    """Enumerate the first n fixed points of a normal ordinal function F (where F(gamma) == gamma)."""
    fixed_points: List[BoundedOrdinal] = []
    curr = ZERO
    for _ in range(n_fixed_points):
        is_fixed = False
        for _ in range(50):
            nxt = F(curr)
            if nxt == curr:
                is_fixed = True
                break
            curr = nxt
        if not is_fixed:
            raise ValueError(f"Function did not converge to a fixed point from initial stage {curr}")
        fixed_points.append(curr)
        curr = curr + ONE
    return fixed_points



@dataclass(frozen=True)
class VeblenHierarchy:
    """The Veblen hierarchy phi_alpha(beta)."""
    alpha: int
    beta: BoundedOrdinal
    symbolic_name: str = ""

    def evaluate_finite(self) -> BoundedOrdinal:
        if self.alpha == 0:
            # phi_0(beta) = omega^beta
            return BoundedOrdinal((0,) * self.beta.to_int() + (1,)) if self.beta.is_finite else OMEGA
        return OMEGA
