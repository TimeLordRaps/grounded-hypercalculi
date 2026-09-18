"""What the oracle calculus actually computes, pinned.

Two separate concerns live here.

`LeapfrogComputation.leapfrog_step` had a defect with a correct fix. It claimed
to return the state after `ordinal_stages` applications of a rule, and computed
that by sampling one step and extrapolating linearly. The extrapolation is the
right answer only for `s -> s + c` with `c` independent of the state and the
stage index; for everything else it returned a wrong value with no signal. The
first section tests the contract against direct iteration, and carries a
negative control -- a copy of the replaced extrapolation -- so that these tests
are shown to fail against the code they were written for.

`OracleTower.decide_halting` and `Hyperoracle` have no correct fix, because no
implementation decides halting. The second section is therefore
characterization, not conformance: it records what the verdicts are functions
of, so that the gap between the name and the computation is visible in the
suite rather than only in the source. These tests are expected to change if the
public API is revised; that is the point of having them.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from grounded_hypercalculi.oracle_calculus import (
    ComputationalQuery,
    ConclusionAnalysis,
    HaltingStatus,
    Hyperoracle,
    LeapfrogComputation,
    OracleTower,
)


def _iterate(rule: Callable[[Any, int], Any], state: Any, stages: int) -> Any:
    """The definition: apply the rule once per stage, passing the stage index."""
    for stage_index in range(stages):
        state = rule(state, stage_index)
    return state


def _legacy_extrapolation(initial_state: Any, rule: Callable[[Any, int], Any], stages: int) -> Any:
    """The replaced implementation, kept as a negative control.

    A test that cannot fail against the code it was written for proves nothing,
    so the defective body is reproduced here and asserted to disagree.
    """
    if stages == 0:
        return initial_state
    s1 = rule(initial_state, 0)
    if isinstance(s1, (int, float)):
        return initial_state + (s1 - initial_state) * stages
    if isinstance(s1, tuple) and isinstance(initial_state, tuple) and len(s1) == len(initial_state):
        if all(isinstance(a, (int, float)) and isinstance(b, (int, float)) for a, b in zip(initial_state, s1)):
            deltas = [b - a for a, b in zip(initial_state, s1)]
            return tuple(a + d * stages for a, d in zip(initial_state, deltas))
    return rule(initial_state, stages - 1)


# (label, rule, initial state, stages). Every rule here is a legitimate stage
# progression; none of them is affine, which is the whole point.
NON_AFFINE_CASES: list[tuple[str, Callable[[Any, int], Any], Any, int]] = [
    ("doubling", lambda s, i: s * 2, 1, 10),
    ("halving", lambda s, i: s / 2, 1.0, 10),
    ("geometric_decay", lambda s, i: s * 0.9, 100.0, 20),
    ("stage_indexed", lambda s, i: s + i, 0, 10),
    ("periodic_mod_7", lambda s, i: (s + 1) % 7, 0, 10),
    ("tuple_doubling", lambda s, i: (s[0] + 1, s[1] * 2), (0, 1), 10),
    ("string_append", lambda s, i: s + "a", "", 50),
]


# ============================================================================
# 1. leapfrog_step returns the state after the stages it was asked for
# ============================================================================


@pytest.mark.parametrize("label,rule,start,stages", NON_AFFINE_CASES, ids=lambda v: v if isinstance(v, str) else "")
def test_leapfrog_agrees_with_direct_iteration(label, rule, start, stages) -> None:
    leapfrog = LeapfrogComputation(dimension=1)
    assert leapfrog.leapfrog_step(start, rule, stages) == _iterate(rule, start, stages)


@pytest.mark.parametrize("label,rule,start,stages", NON_AFFINE_CASES, ids=lambda v: v if isinstance(v, str) else "")
def test_negative_control_the_replaced_extrapolation_gets_these_wrong(label, rule, start, stages) -> None:
    # Guards the tests above: each case must actually distinguish the fix from
    # the defect. If a case ever stopped disagreeing it would be testing nothing.
    assert _legacy_extrapolation(start, rule, stages) != _iterate(rule, start, stages)


def test_affine_rules_were_already_correct_and_still_are() -> None:
    # The extrapolation's one sound case. The fix must not disturb it -- these
    # are the values the existing suite and the published examples depend on.
    leapfrog = LeapfrogComputation(dimension=1)
    assert leapfrog.leapfrog_step(10, lambda s, i: s + 5, 1000) == 10 + 5 * 1000
    assert leapfrog.leapfrog_step(0, lambda s, i: s + 1, 10) == 10
    assert _legacy_extrapolation(10, lambda s, i: s + 5, 1000) == 10 + 5 * 1000


def test_a_contractive_sequence_stays_on_the_side_of_zero_it_started() -> None:
    # The docstring names contraction specifically, and contraction was the case
    # the extrapolation handled worst: halving 1.0 ten times returned -4.0, a
    # sign error on a sequence that is positive at every stage.
    leapfrog = LeapfrogComputation(dimension=1)
    result = leapfrog.leapfrog_step(1.0, lambda s, i: s / 2, 10)
    assert result == pytest.approx(2.0**-10)
    assert result > 0
    assert _legacy_extrapolation(1.0, lambda s, i: s / 2, 10) < 0


def test_a_rule_that_cannot_leave_its_carrier_does_not_leave_it() -> None:
    # (s + 1) % 7 maps into {0..6}. Any claimed stage value outside that set is
    # not a state of this system. The extrapolation returned 10.
    leapfrog = LeapfrogComputation(dimension=1)
    for stages in range(1, 30):
        assert leapfrog.leapfrog_step(0, lambda s, i: (s + 1) % 7, stages) in range(7)
    assert _legacy_extrapolation(0, lambda s, i: (s + 1) % 7, 10) not in range(7)


def test_every_stage_is_evaluated_exactly_once_and_in_order() -> None:
    seen: list[tuple[Any, int]] = []

    def recording(state: Any, index: int) -> Any:
        seen.append((state, index))
        return state + 1

    LeapfrogComputation(dimension=1).leapfrog_step(0, recording, 6)
    assert [index for _state, index in seen] == [0, 1, 2, 3, 4, 5]
    assert [state for state, _index in seen] == [0, 1, 2, 3, 4, 5]


def test_zero_stages_is_the_initial_state_and_runs_no_rule() -> None:
    def exploding(_state: Any, _index: int) -> Any:
        raise AssertionError("no stage should be evaluated")

    assert LeapfrogComputation(dimension=1).leapfrog_step(42, exploding, 0) == 42


def test_negative_stages_are_refused() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        LeapfrogComputation(dimension=1).leapfrog_step(0, lambda s, i: s + 1, -1)


def test_budget_refuses_rather_than_substituting_an_extrapolation() -> None:
    # Past the budget the value is unknown to the operator. Refusing says so;
    # returning a guessed closed form would say something stronger than is known.
    leapfrog = LeapfrogComputation(dimension=1)
    with pytest.raises(ValueError, match="exceeds the evaluation budget"):
        leapfrog.leapfrog_step(0, lambda s, i: s + 1, 11, max_evaluated_stages=10)
    # Exactly at the budget is inside it.
    assert leapfrog.leapfrog_step(0, lambda s, i: s + 1, 10, max_evaluated_stages=10) == 10


def test_raising_the_budget_never_changes_an_answer_already_given() -> None:
    leapfrog = LeapfrogComputation(dimension=1)
    rule = lambda s, i: (s * 2 + i) % 1009
    baseline = {n: leapfrog.leapfrog_step(1, rule, n, max_evaluated_stages=40) for n in range(41)}
    for n, value in baseline.items():
        assert leapfrog.leapfrog_step(1, rule, n, max_evaluated_stages=10_000) == value


# ============================================================================
# 2. What the halting verdicts are functions of
# ============================================================================


def test_a_query_carries_no_program() -> None:
    # The object handed to decide_halting holds a label, an integer, a
    # description and a rank. It does not hold the program, so no function of it
    # can be the halting predicate -- this is a fact about the signature, before
    # any question about the body.
    assert set(ComputationalQuery.__dataclass_fields__) == {
        "program_id",
        "input_val",
        "description",
        "complexity_rank",
    }


def test_the_verdict_is_not_invariant_under_renaming() -> None:
    # Halting is a property of a program, so any decision procedure for it gives
    # the same verdict to two names for the same program. This one does not:
    # over twenty pairs the verdict flips about half the time.
    tower = OracleTower()
    flips = sum(
        tower.decide_halting(ComputationalQuery(f"name_a_{i}", 0), 1)
        != tower.decide_halting(ComputationalQuery(f"name_b_{i}", 0), 1)
        for i in range(20)
    )
    assert flips > 0, "the verdict would have to depend on something other than the label"


def test_the_verdict_is_a_function_of_the_label_and_input_alone() -> None:
    # Everything else about a query is ignored: two queries differing only in
    # description get the same verdict, and the description is the only field
    # that could carry a program.
    tower = OracleTower()
    for i in range(25):
        plain = ComputationalQuery(f"p{i}", 3, description="")
        annotated = ComputationalQuery(f"p{i}", 3, description="while True: pass")
        assert tower.decide_halting(plain, 1) == tower.decide_halting(annotated, 1)


def test_the_verdict_does_not_track_programs_whose_behaviour_is_not_in_doubt() -> None:
    # Not a claim that these labels denote real programs -- only that if the
    # verdicts carried halting information, a label this explicit would be the
    # easiest possible case, and the verdicts do not line up with it.
    tower = OracleTower()
    verdicts = {
        label: tower.decide_halting(ComputationalQuery(label, 0), 1)
        for label in ("infinite_loop", "while_true_loop_forever", "noop", "return_immediately")
    }
    assert verdicts["infinite_loop"] == HaltingStatus.HALTS
    assert verdicts["noop"] == HaltingStatus.LOOPS


def test_the_tier_bookkeeping_is_the_part_that_is_real() -> None:
    # An oracle at or below the query's rank returns UNDECIDABLE_AT_TIER, and
    # that much is a genuine consequence of the stated hierarchy rather than a
    # hash. It holds for every rank and every label, which the verdicts do not.
    tower = OracleTower(max_level=20)
    for rank in range(10):
        query = ComputationalQuery(f"q{rank}", rank, complexity_rank=rank)
        for level in range(rank + 1):
            assert tower.decide_halting(query, level) == HaltingStatus.UNDECIDABLE_AT_TIER
        assert tower.decide_halting(query, rank + 1) != HaltingStatus.UNDECIDABLE_AT_TIER


def test_repeated_queries_are_stable_within_and_across_towers() -> None:
    # Determinism is real and worth keeping: the cache and a fresh tower agree,
    # so a recorded verdict is reproducible even though it is not a decision.
    first, second = OracleTower(), OracleTower()
    for i in range(30):
        query = ComputationalQuery(f"stable_{i}", i, complexity_rank=0)
        once = first.decide_halting(query, 1)
        assert first.decide_halting(query, 1) == once
        assert second.decide_halting(query, 1) == once


def test_hyperoracle_returns_the_same_verdicts_as_the_level_one_tower() -> None:
    # evaluate_tower is documented as resolving queries "across all finite
    # oracle levels", but it evaluates the same expression as a single level-one
    # tower and ignores the tower argument and each query's rank entirely.
    tower = OracleTower()
    queries = [ComputationalQuery(f"q{i}", i, complexity_rank=i % 4) for i in range(40)]
    results = Hyperoracle().evaluate_tower(tower, queries)
    for query in queries:
        assert results[query.program_id] == OracleTower().decide_halting(
            ComputationalQuery(query.program_id, query.input_val, complexity_rank=0), 1
        )


def test_conclusion_analysis_ascends_exactly_one_rank() -> None:
    # The rank arithmetic is the substantive part of analyze_conclusion; the
    # status it carries is whatever decide_halting returned.
    analyzer = ConclusionAnalysis()
    for rank in range(6):
        status, resolved = analyzer.analyze_conclusion(f"stmt_{rank}", base_rank=rank)
        assert resolved == rank + 1
        assert status is not HaltingStatus.UNDECIDABLE_AT_TIER
