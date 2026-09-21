from grounded_hypercalculi.real_calculus import (
    CauchySequence,
    DedekindCut,
    GroundedRational,
    Interval,
    SurrealGame,
    numerical_derivative,
    riemann_integral,
)



def test_grounded_rationals():
    r1 = GroundedRational(1, 2)
    r2 = GroundedRational(1, 3)
    sum_r = r1 + r2
    assert sum_r.numerator == 5
    assert sum_r.denominator == 6
    assert abs(sum_r.to_float() - 5/6) < 1e-9


def test_dedekind_cuts():
    cut = DedekindCut(lower_bound=1.414, upper_bound=1.415)
    assert 1.414 < cut.midpoint < 1.415


def test_surreal_games_and_infinitesimals():
    zero_game = SurrealGame()
    assert zero_game.value == 0.0

    one_game = SurrealGame(left=(0.0,), right=())
    assert one_game.value == 1.0

    eps = SurrealGame.infinitesimal()
    assert 0.0 < eps.value < 1.0


def test_numerical_calculus():
    f = lambda x: x ** 2
    # f'(3) = 6
    df = numerical_derivative(f, 3.0)
    assert abs(df - 6.0) < 1e-4

    # integral of x^2 from 0 to 3 is 9
    integral = riemann_integral(f, 0.0, 3.0, subdivisions=1000)
    assert abs(integral - 9.0) < 1e-2


def test_infinitesimal_ordering_and_surreals():
    eps = SurrealGame.infinitesimal()
    zero = SurrealGame()
    half = SurrealGame(left=(0.0,), right=(1.0,))
    # Epsilon is between 0 and 1/2
    assert zero.value < eps.value < half.value


def test_grounded_rational_arithmetic():
    r1 = GroundedRational(3, 4)
    r2 = GroundedRational(2, 5)
    # 3/4 - 2/5 = 15/20 - 8/20 = 7/20
    diff = r1 - r2
    assert diff.numerator == 7
    assert diff.denominator == 20
    # 3/4 * 2/5 = 6/20 = 3/10
    prod = r1 * r2
    assert prod.numerator == 3
    assert prod.denominator == 10

    # Division
    div = r1 / r2
    assert div == GroundedRational(15, 8)
    assert r2 < r1
    assert r1 > r2
    assert r2 <= r1
    assert r1 >= r2


def test_dedekind_cut_sqrt_two():
    cut = DedekindCut.sqrt_two(precision=1e-5)
    assert abs(cut.approximate() - 1.41421356) < 1e-4
    assert cut.contains(GroundedRational(14, 10))
    assert not cut.contains(GroundedRational(15, 10))


def test_surreal_game_invalid_number():
    bad_game = SurrealGame(left=(1.0,), right=(0.0,))
    assert not bad_game.is_number
    import pytest
    with pytest.raises(ValueError, match="Not a valid numeric surreal number"):
        _ = bad_game.value


def test_cauchy_sequence():
    e_seq = CauchySequence.euler_e()
    assert e_seq.is_cauchy(tolerance=1e-5)
    assert abs(e_seq.limit(n=10) - 2.71828) < 1e-4

    geom = CauchySequence.geometric_series(GroundedRational(1, 2))
    assert geom.is_cauchy(tolerance=1e-4)
    # sum 1/2^k from 0 to infty is 2
    assert abs(geom.limit(n=15) - 2.0) < 1e-4


def test_interval_arithmetic():
    import pytest

    i1 = Interval(1.0, 3.0)
    assert i1.midpoint == 2.0
    assert i1.width == 2.0
    assert i1.radius == 1.0
    assert 2.0 in i1
    assert 0.5 not in i1

    # Invariant validation
    with pytest.raises(ValueError, match="cannot exceed upper bound"):
        Interval(3.0, 1.0)
    with pytest.raises(ValueError, match="cannot be NaN"):
        Interval(float("nan"), 1.0)

    # Arithmetic operations
    i2 = Interval(2.0, 4.0)
    add_i = i1 + i2
    assert add_i == Interval(3.0, 7.0)

    sub_i = i1 - i2
    assert sub_i == Interval(-3.0, 1.0)

    mul_i = i1 * Interval(-2.0, 4.0)
    assert mul_i == Interval(-6.0, 12.0)

    div_i = Interval(4.0, 8.0) / Interval(2.0, 4.0)
    assert div_i == Interval(1.0, 4.0)

    with pytest.raises(ZeroDivisionError, match="containing zero"):
        _ = i1 / Interval(-1.0, 2.0)

    # Powers and negation
    assert -i1 == Interval(-3.0, -1.0)
    assert Interval(-2.0, 3.0) ** 2 == Interval(0.0, 9.0)
    assert Interval(2.0, 3.0) ** 3 == Interval(8.0, 27.0)

    # Intersection and hull
    overlap = Interval(1.0, 4.0) & Interval(3.0, 6.0)
    assert overlap == Interval(3.0, 4.0)
    disjoint = Interval(1.0, 2.0) & Interval(3.0, 4.0)
    assert disjoint is None

    hull = Interval(1.0, 2.0) | Interval(4.0, 6.0)
    assert hull == Interval(1.0, 6.0)

    # Enclosure
    enclosed = Interval.enclose_samples([1.5, -2.0, 4.5, 0.0])
    assert enclosed == Interval(-2.0, 4.5)


