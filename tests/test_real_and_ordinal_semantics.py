"""Properties the real and ordinal calculi have to hold, not outputs they happen to give.

Each section pins one correction and carries a negative control -- the replaced
computation, reproduced locally -- so that the tests are shown to fail against
the code they were written for. A test that cannot fail proves nothing.

The sections are:

1. `CauchySequence.is_cauchy` examined a single window at a fixed start index,
   which rejected `1/(n + 1)` and accepted sequences that diverge.
2. `DedekindCut.contains` answered False across the undetermined interval of a
   cut that records only bounds.
3. `SurrealGame.value` took a midpoint where Conway's simplicity rule applies.
4. `ordinal_derivative` enumerated one fixed point repeatedly for a function
   that is not normal.
5. `VeblenHierarchy.evaluate_finite` returned omega for every phi_alpha with
   alpha >= 1, all of which are above omega^omega.
"""

from __future__ import annotations

import math

import pytest

from grounded_hypercalculi.ordinal_calculus import (
    OMEGA,
    BoundedOrdinal,
    VeblenHierarchy,
    ordinal_derivative,
)
from grounded_hypercalculi.real_calculus import (
    CauchySequence,
    DedekindCut,
    GroundedRational,
    SurrealGame,
)


def _seq(term):
    return CauchySequence(generator=term)


# ============================================================================
# 1. is_cauchy: a screen that answers for textbook sequences
# ============================================================================


def _legacy_is_cauchy(sequence, tolerance=1e-4, test_terms=15) -> bool:
    """The replaced implementation: one window, at one fixed start index."""
    terms = [sequence.term(i).to_float() for i in range(test_terms, test_terms + 10)]
    return all(
        abs(terms[i] - terms[j]) < tolerance
        for i in range(len(terms))
        for j in range(i + 1, len(terms))
    )


CONVERGENT = [
    ("reciprocal", lambda n: GroundedRational(1, n + 1)),
    ("reciprocal_square", lambda n: GroundedRational(1, (n + 1) ** 2)),
    ("constant", lambda n: GroundedRational(3, 1)),
]


@pytest.mark.parametrize("label,term", CONVERGENT, ids=[c[0] for c in CONVERGENT])
def test_convergent_sequences_are_not_rejected(label, term) -> None:
    assert _seq(term).is_cauchy() is True


def test_negative_control_a_fixed_window_rejects_a_convergent_sequence() -> None:
    # 1/(n + 1) converges to 0 and is Cauchy. Across terms 15..24 it still spans
    # 1/16 - 1/25 = 0.0225, well over the default tolerance, so a screen that
    # looks only there reports False. Searching for a quiet window finds one.
    reciprocal = _seq(lambda n: GroundedRational(1, n + 1))
    assert _legacy_is_cauchy(reciprocal) is False
    assert reciprocal.is_cauchy() is True


def test_a_fast_divergent_sequence_is_still_rejected() -> None:
    # Widening the search must not turn the screen into a rubber stamp.
    assert _seq(lambda n: GroundedRational(n, 1)).is_cauchy() is False
    assert _seq(lambda n: GroundedRational(n, 10)).is_cauchy() is False


def test_a_slowly_divergent_sequence_still_passes_and_that_is_documented() -> None:
    # The honest limit of the method, pinned so it cannot be mistaken for a
    # proof of convergence. a_n = n * 1e-6 increases without bound and varies by
    # under 1e-5 across any window of ten consecutive terms.
    slow = _seq(lambda n: GroundedRational(n, 1_000_000))
    assert slow.is_cauchy() is True
    assert slow.term(10_000_000).to_float() > 9.0  # nowhere near converging
    # Tightening the tolerance is what actually catches it.
    assert slow.is_cauchy(tolerance=1e-7) is False


def test_tolerance_and_window_are_validated() -> None:
    reciprocal = _seq(lambda n: GroundedRational(1, n + 1))
    with pytest.raises(ValueError, match="Tolerance must be positive"):
        reciprocal.is_cauchy(tolerance=0.0)
    with pytest.raises(ValueError, match="at least two terms"):
        reciprocal.is_cauchy(window=1)


def test_the_published_sequences_still_pass() -> None:
    assert CauchySequence.euler_e().is_cauchy(tolerance=1e-5) is True
    assert CauchySequence.geometric_series(GroundedRational(1, 2)).is_cauchy() is True


# ============================================================================
# 2. DedekindCut.contains distinguishes "not in L" from "not known"
# ============================================================================


def test_membership_is_settled_outside_the_bounds() -> None:
    cut = DedekindCut(lower_bound=1.0, upper_bound=2.0)
    # q < lower_bound <= r, so q < r and q is in the lower cut.
    assert cut.contains(0.5) is True
    assert cut.contains(0.999) is True
    # q >= upper_bound >= r, so q is not below r.
    assert cut.contains(2.0) is False
    assert cut.contains(2.5) is False


@pytest.mark.parametrize("q", [1.0, 1.25, 1.5, 1.9999])
def test_membership_inside_the_bounds_is_refused_not_denied(q: float) -> None:
    # The cut records only that the real lies in [1, 2]. Where q falls relative
    # to it is not determined by that, and False would assert it is.
    cut = DedekindCut(lower_bound=1.0, upper_bound=2.0)
    with pytest.raises(ValueError, match="undetermined"):
        cut.contains(q)


def test_negative_control_the_replaced_rule_denied_the_whole_interval() -> None:
    cut = DedekindCut(lower_bound=1.0, upper_bound=2.0)
    for q in (1.0, 1.25, 1.5, 1.9999):
        assert (q < cut.lower_bound) is False  # what contains() used to return


def test_a_cut_with_a_predicate_answers_everywhere() -> None:
    # sqrt_two supplies x*x < 2, which settles membership without reference to
    # the bracketing bounds, so the refusal above never applies to it.
    cut = DedekindCut.sqrt_two(precision=1e-5)
    assert cut.contains(GroundedRational(14, 10)) is True
    assert cut.contains(GroundedRational(15, 10)) is False
    assert cut.contains(1.41421) is True
    assert abs(cut.approximate() - math.sqrt(2)) < 1e-4


# ============================================================================
# 3. SurrealGame.value is the simplicity rule
# ============================================================================


def _legacy_value(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """The replaced computation: midpoint, with +-1 for one-sided games."""
    l_max = max(left) if left else 0.0
    r_min = min(right) if right else 0.0
    if not left and not right:
        return 0.0
    if left and not right:
        return l_max + 1.0
    if not left and right:
        return r_min - 1.0
    return (l_max + r_min) / 2.0


# (left, right, value under the simplicity rule)
SIMPLICITY: list[tuple[tuple[float, ...], tuple[float, ...], float]] = [
    ((), (), 0.0),
    ((0.0,), (), 1.0),
    ((), (0.0,), -1.0),
    ((0.0,), (1.0,), 0.5),
    ((-1.0,), (1.0,), 0.0),
    ((2.0,), (), 3.0),
    ((0.5,), (1.0,), 0.75),
    ((0.25,), (0.5,), 0.375),
    ((0.0,), (1.0, 0.5, 0.25), 0.125),
    # The cases the midpoint rule got wrong.
    ((1.0,), (4.0,), 2.0),
    ((-5.0,), (), 0.0),
    ((), (5.0,), 0.0),
    ((-4.0,), (-1.0,), -2.0),
]


@pytest.mark.parametrize("left,right,expected", SIMPLICITY)
def test_value_follows_the_simplicity_rule(left, right, expected) -> None:
    assert SurrealGame(left=left, right=right).value == expected


@pytest.mark.parametrize("left,right,expected", SIMPLICITY)
def test_the_value_is_simpler_than_every_other_number_in_the_gap(left, right, expected) -> None:
    # Independent of the table: whatever the value is, nothing strictly between
    # the bounds may be simpler. "Simpler" orders integers by magnitude ahead of
    # every non-integer, and dyadics by denominator.
    low = max(left) if left else -math.inf
    high = min(right) if right else math.inf
    assert low < expected < high

    def complexity(x: float) -> tuple[int, float]:
        if x == int(x):
            return (0, abs(x))
        denominator = 1
        while x * denominator != int(x * denominator) and denominator < 2**20:
            denominator *= 2
        return (1, float(denominator))

    for step in range(1, 400):
        candidate = expected + step / 64.0
        if candidate < high and complexity(candidate) < complexity(expected):
            raise AssertionError(f"{candidate} is simpler than {expected} and lies in the gap")
        candidate = expected - step / 64.0
        if candidate > low and complexity(candidate) < complexity(expected):
            raise AssertionError(f"{candidate} is simpler than {expected} and lies in the gap")


def test_negative_control_the_midpoint_rule_disagrees_on_four_of_these() -> None:
    disagreeing = [
        (left, right, expected)
        for left, right, expected in SIMPLICITY
        if _legacy_value(left, right) != expected
    ]
    assert len(disagreeing) == 4, disagreeing
    # Spelled out, because these are the cases that motivated the change.
    assert _legacy_value((1.0,), (4.0,)) == 2.5
    assert _legacy_value((-5.0,), ()) == -4.0
    assert _legacy_value((), (5.0,)) == 4.0
    assert _legacy_value((-4.0,), (-1.0,)) == -2.5


def test_a_game_that_is_not_a_number_has_no_value() -> None:
    bad = SurrealGame(left=(1.0,), right=(0.0,))
    assert bad.is_number is False
    with pytest.raises(ValueError, match="Not a valid numeric surreal number"):
        _ = bad.value


def test_the_infinitesimal_constructor_is_a_truncation_not_an_infinitesimal() -> None:
    # Pinned so the name cannot be read as a claim: the returned game's value is
    # a dyadic rational, and a real infinitesimal is below every positive real.
    epsilon = SurrealGame.infinitesimal()
    assert epsilon.value == 0.125
    assert epsilon.value > 1e-3  # an infinitesimal would not be
    assert SurrealGame().value < epsilon.value < SurrealGame(left=(0.0,), right=(1.0,)).value


# ============================================================================
# 4. ordinal_derivative enumerates distinct, increasing fixed points
# ============================================================================


def test_fixed_points_of_a_normal_function_are_enumerated_in_order() -> None:
    points = ordinal_derivative(lambda a: a, n_fixed_points=5)
    assert [p.to_int() for p in points] == [0, 1, 2, 3, 4]
    assert all(points[i] < points[i + 1] for i in range(len(points) - 1))


def test_a_function_that_is_not_normal_is_refused_rather_than_repeated() -> None:
    # F(alpha) = 5 has exactly one fixed point. Iterating F from 6 lands back on
    # 5, so the enumeration used to report 5 four times as "the first four".
    with pytest.raises(ValueError, match="not normal"):
        ordinal_derivative(lambda a: BoundedOrdinal.from_int(5), n_fixed_points=4)
    # Asking for the one that exists is still fine.
    assert ordinal_derivative(lambda a: BoundedOrdinal.from_int(5), n_fixed_points=1)[0].to_int() == 5


def test_negative_control_the_unchecked_enumeration_repeated_itself() -> None:
    # The replaced loop, without the increasing check.
    constant = lambda a: BoundedOrdinal.from_int(5)
    found = []
    curr = BoundedOrdinal(())
    for _ in range(4):
        for _ in range(50):
            nxt = constant(curr)
            if nxt == curr:
                break
            curr = nxt
        found.append(curr)
        curr = curr + BoundedOrdinal((1,))
    assert len(set(found)) == 1, "the unchecked loop should return the same point four times"


def test_a_function_with_no_reachable_fixed_point_still_fails_closed() -> None:
    with pytest.raises(ValueError, match="did not converge"):
        ordinal_derivative(lambda a: a + BoundedOrdinal((1,)), n_fixed_points=1)


# ============================================================================
# 5. VeblenHierarchy refuses what it cannot represent
# ============================================================================


@pytest.mark.parametrize("beta,expected", [(0, (1,)), (1, (0, 1)), (2, (0, 0, 1)), (3, (0, 0, 0, 1))])
def test_phi_zero_of_a_finite_ordinal_is_omega_to_that_power(beta, expected) -> None:
    value = VeblenHierarchy(alpha=0, beta=BoundedOrdinal.from_int(beta)).evaluate_finite()
    assert value.coefficients == expected


def test_phi_zero_of_omega_is_out_of_range() -> None:
    # phi_0(omega) is omega^omega, the exclusive upper bound of this representation.
    with pytest.raises(ValueError, match="not below|not representable"):
        VeblenHierarchy(alpha=0, beta=OMEGA).evaluate_finite()


@pytest.mark.parametrize("alpha", [1, 2, 3, 10])
@pytest.mark.parametrize("beta", [0, 1, 5])
def test_every_higher_veblen_row_is_refused(alpha: int, beta: int) -> None:
    # phi_1(beta) is epsilon_beta, already far above omega^omega. Returning
    # omega for these was not a coarse approximation: omega is smaller than the
    # ordinal asked for, and smaller than phi_0(2) which the same method returns
    # exactly.
    with pytest.raises(ValueError, match="epsilon_0"):
        VeblenHierarchy(alpha=alpha, beta=BoundedOrdinal.from_int(beta)).evaluate_finite()


def test_negative_control_the_replaced_branch_returned_omega_for_all_of_them() -> None:
    # What evaluate_finite used to return, next to a value it computes exactly.
    legacy = OMEGA
    exact_phi_0_of_2 = VeblenHierarchy(alpha=0, beta=BoundedOrdinal.from_int(2)).evaluate_finite()
    assert legacy < exact_phi_0_of_2, (
        "the old phi_1(beta) was below phi_0(2), which is the wrong direction "
        "for a hierarchy that only grows"
    )
