"""Ordinal representations must contain exact nonnegative integer coefficients."""

from fractions import Fraction

import pytest

from grounded_hypercalculi.ordinal_calculus import BoundedOrdinal, OMEGA, ONE, ZERO


@pytest.mark.parametrize("value", [-1, -10])
def test_negative_coefficients_are_rejected(value):
    with pytest.raises(ValueError, match="nonnegative"):
        BoundedOrdinal((0, value))


@pytest.mark.parametrize("value", [True, False, 0.0, 1.5, "2", Fraction(1, 2)])
def test_inexact_or_boolean_coefficients_are_rejected(value):
    with pytest.raises(TypeError, match="integer"):
        BoundedOrdinal((value,))


@pytest.mark.parametrize("value", [True, False, 0.0, 1.5, "2", Fraction(1, 2)])
def test_from_int_does_not_coerce_nonintegers(value):
    with pytest.raises(TypeError, match="integer"):
        BoundedOrdinal.from_int(value)


class ExactIndex:
    def __index__(self):
        return 3


def test_exact_integer_protocol_is_canonicalized():
    ordinal = BoundedOrdinal((ExactIndex(), 0))
    assert ordinal.coefficients == (3,)
    assert type(ordinal.coefficients[0]) is int
    assert BoundedOrdinal.from_int(ExactIndex()) == ordinal


def test_inputs_are_frozen_and_ordinary_addition_is_preserved():
    coefficients = [3, 2, 0]
    ordinal = BoundedOrdinal(coefficients)
    coefficients[0] = -5
    assert ordinal.coefficients == (3, 2)
    assert BoundedOrdinal((0, 0)) == ZERO
    assert ONE + OMEGA == OMEGA
    assert OMEGA + ONE > OMEGA
    assert OMEGA + ordinal.left_sub(OMEGA) == ordinal
