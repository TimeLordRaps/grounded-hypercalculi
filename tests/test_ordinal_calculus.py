import pytest
from grounded_hypercalculi.ordinal_calculus import (
    BoundedOrdinal,
    OMEGA,
    ONE,
    ZERO,
    VeblenHierarchy,
    ordinal_derivative,
    ordinal_difference,
)


def test_bounded_ordinal_arithmetic():
    o1 = BoundedOrdinal.from_int(5)
    o2 = BoundedOrdinal.from_int(3)
    assert o1.to_int() == 5
    assert o1 > o2

    # Left subtraction: 3 + gamma = 5 => gamma = 2
    gamma = o1.left_sub(o2)
    assert gamma.to_int() == 2

    # Transfinite ordinal addition: 1 + omega = omega
    assert ONE + OMEGA == OMEGA
    # omega + 1 > omega
    om_plus_1 = OMEGA + ONE
    assert om_plus_1 > OMEGA


def test_ordinal_difference_and_derivative():
    # F(alpha) = 2 * alpha
    F = lambda a: a + a
    diff = ordinal_difference(F, BoundedOrdinal.from_int(2))
    assert diff.is_finite

    # Normal function fixed points: F(gamma) = gamma
    # F(x) = x has fixed points everywhere
    id_func = lambda x: x
    fps = ordinal_derivative(id_func, n_fixed_points=3)
    assert len(fps) == 3


def test_ordinal_derivative_non_convergent_fails_closed():
    # Successor function alpha + 1 has no fixed points
    succ = lambda x: x + ONE
    with pytest.raises(ValueError, match="did not converge to a fixed point"):
        ordinal_derivative(succ, n_fixed_points=1)

