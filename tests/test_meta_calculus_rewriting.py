"""The one-step relation must contain every one-step rewrite.

`step` is documented "all immediate successor states" and returned one successor
per rule, rewriting only the leftmost match. For `a -> b` it gave `step("aa") ==
["ba"]`, so `"ab"` -- a single rewrite away -- was unreachable from `"aa"` by any
number of steps. Reachability, joinability and confluence were all being computed
over a proper subgraph of the real relation.

The successor tests are differential: `step` is checked against the one-step
relation written out directly from its definition, over every state of a small
alphabet, rather than against hand-listed expected values.

The `characterises` tests pin what `trajectory_bisimilar` is a function of. It is
not bisimulation and its name says otherwise; the name is public API on a
released version, so these tests record the gap rather than close it.
"""

from __future__ import annotations

import itertools

import pytest

from grounded_hypercalculi.meta_calculus import (
    RewriteRule,
    RewriteSystem,
    shift_operator,
    trajectory_bisimilar,
)


def one_step_relation(state: str, pattern: str, replacement: str) -> set[str]:
    """Every string obtained by rewriting exactly one occurrence of `pattern`.

    Written from the definition, independently of the implementation, so that a
    disagreement points at one of them rather than at a shared assumption.
    """
    width = len(pattern)
    return {
        state[:i] + replacement + state[i + width:]
        for i in range(len(state) - width + 1)
        if state[i:i + width] == pattern
    }


# ============================================================================
# 1. step() against the relation it is supposed to be
# ============================================================================


@pytest.mark.parametrize("pattern, replacement", [("a", "b"), ("aa", "b"), ("a", "aa"), ("ab", "ba")])
def test_step_agrees_with_the_one_step_relation_on_every_short_state(
    pattern: str, replacement: str
) -> None:
    system = RewriteSystem([RewriteRule("r", pattern, replacement)])
    for length in range(6):
        for letters in itertools.product("ab", repeat=length):
            state = "".join(letters)
            assert set(system.step(state)) == one_step_relation(state, pattern, replacement), state


def test_a_rule_matching_twice_contributes_two_successors() -> None:
    system = RewriteSystem([RewriteRule("a2b", "a", "b")])
    assert set(system.step("aa")) == {"ba", "ab"}
    assert set(system.step("aaa")) == {"baa", "aba", "aab"}


def test_overlapping_occurrences_are_both_steps() -> None:
    # "aaa" has a redex for "aa" at index 0 and at index 1. They overlap, and
    # each is a legitimate single step.
    system = RewriteSystem([RewriteRule("r", "aa", "b")])
    assert set(system.step("aaa")) == {"ba", "ab"}


def test_several_rules_all_contribute() -> None:
    system = RewriteSystem([RewriteRule("a2x", "a", "x"), RewriteRule("b2y", "b", "y")])
    assert set(system.step("ab")) == {"xb", "ay"}


def test_duplicate_successors_appear_once() -> None:
    # Two rules that happen to produce the same result on this state.
    system = RewriteSystem([RewriteRule("r1", "ab", "z"), RewriteRule("r2", "ab", "z")])
    assert system.step("ab") == ["z"]


def test_a_state_with_no_redex_has_no_successors() -> None:
    assert RewriteSystem([RewriteRule("r", "a", "b")]).step("bbb") == []
    assert RewriteSystem([]).step("anything") == []


def test_a_conditional_rule_contributes_nothing_when_the_condition_fails() -> None:
    rule = RewriteRule("cond", "a", "b", condition=lambda s: len(s) > 3)
    assert rule.apply_all("aa") == []
    assert set(rule.apply_all("aaaa")) == {"baaa", "abaa", "aaba", "aaab"}


# ============================================================================
# 2. What the missing successors cost
# ============================================================================


def _reachable(system: RewriteSystem, start: str) -> set[str]:
    seen, frontier = {start}, [start]
    while frontier:
        state = frontier.pop()
        for successor in system.step(state):
            if successor not in seen:
                seen.add(successor)
                frontier.append(successor)
    return seen


def test_reachability_finds_every_state_it_should() -> None:
    system = RewriteSystem([RewriteRule("a2b", "a", "b")])
    assert _reachable(system, "aa") == {"aa", "ab", "ba", "bb"}


def test_the_system_is_confluent_and_that_is_now_visible() -> None:
    # a -> b has the diamond property: from "aa" the two one-step results "ba"
    # and "ab" both rewrite to "bb". Joinability is a statement about the
    # successors of a state, so it could not even be asked while one of the two
    # was missing from the relation.
    system = RewriteSystem([RewriteRule("a2b", "a", "b")])
    successors = system.step("aa")
    assert len(successors) == 2
    joins = [set(system.step(s)) for s in successors]
    assert joins[0] & joins[1] == {"bb"}


def test_negative_control_leftmost_only_steps_never_reach_the_other_redex() -> None:
    # The replaced body: one successor per rule, leftmost match.
    def legacy_step(system: RewriteSystem, state: str) -> list[str]:
        successors: list[str] = []
        for rule in system.rules:
            result = rule.apply(state)
            if result is not None and result not in successors:
                successors.append(result)
        return successors

    system = RewriteSystem([RewriteRule("a2b", "a", "b")])
    assert legacy_step(system, "aa") == ["ba"], "only the leftmost redex"

    seen, frontier = {"aa"}, ["aa"]
    while frontier:
        state = frontier.pop()
        for successor in legacy_step(system, state):
            if successor not in seen:
                seen.add(successor)
                frontier.append(successor)
    assert seen == {"aa", "ba", "bb"}
    assert "ab" not in seen, "one rewrite away from the start, and unreachable"


# ============================================================================
# 3. trajectory
# ============================================================================


def test_trajectory_is_unchanged_by_the_wider_successor_relation() -> None:
    # step(s)[0] is still the leftmost redex of the earliest applicable rule, so
    # the deterministic trace is bit-identical to before.
    system = RewriteSystem([RewriteRule("a2b", "a", "b")])
    assert system.trajectory("aaa", max_steps=5) == ["aaa", "baa", "bba", "bbb"]


def test_a_trajectory_that_ends_is_shorter_than_the_budget() -> None:
    system = RewriteSystem([RewriteRule("r1", "A", "B"), RewriteRule("r2", "B", "C")])
    trace = system.trajectory("A", max_steps=5)
    assert trace == ["A", "B", "C"]
    assert len(trace) < 5 + 1, "which is how the caller knows it was not cut off"


def test_a_trajectory_cut_off_by_the_budget_fills_it_exactly() -> None:
    cycling = RewriteSystem([RewriteRule("f", "ab", "ba"), RewriteRule("b", "ba", "ab")])
    for budget in (3, 5, 9):
        assert len(cycling.trajectory("ab", max_steps=budget)) == budget + 1


def test_a_longer_cycle_is_not_a_stopping_condition_unless_asked() -> None:
    cycling = RewriteSystem([RewriteRule("f", "ab", "ba"), RewriteRule("b", "ba", "ab")])
    assert cycling.trajectory("ab", max_steps=9) == ["ab", "ba"] * 5
    assert cycling.trajectory("ab", max_steps=9, stop_on_repeat=True) == ["ab", "ba", "ab"]


def test_stop_on_repeat_leaves_an_acyclic_trajectory_alone() -> None:
    system = RewriteSystem([RewriteRule("r1", "A", "B"), RewriteRule("r2", "B", "C")])
    assert system.trajectory("A", 5, stop_on_repeat=True) == system.trajectory("A", 5)


def test_a_zero_budget_gives_the_initial_state_alone() -> None:
    system = RewriteSystem([RewriteRule("r", "a", "b")])
    assert system.trajectory("a", max_steps=0) == ["a"]


def test_a_negative_budget_is_refused() -> None:
    # It previously returned [initial], which is also what a budget of zero and
    # a terminating trajectory return.
    system = RewriteSystem([RewriteRule("r", "a", "b")])
    with pytest.raises(ValueError, match="non-negative"):
        system.trajectory("a", max_steps=-1)


# ============================================================================
# 4. A rule must have a left-hand side
# ============================================================================


def test_an_empty_pattern_is_refused() -> None:
    with pytest.raises(ValueError, match="empty pattern"):
        RewriteRule("eps", "", "X")


def test_negative_control_an_empty_pattern_grew_the_state_forever() -> None:
    # "" occurs in every string, and str.replace("", X, 1) prepends, so the rule
    # applied to its own output and the trace ended only at the budget.
    state = "abc"
    for _ in range(5):
        assert "" in state
        state = state.replace("", "X", 1)
    assert state == "XXXXXabc"


def test_a_rule_whose_pattern_equals_its_replacement_terminates() -> None:
    # Applicable forever, but the successor equals the state, so the self-loop
    # check ends the trace at once.
    system = RewriteSystem([RewriteRule("id", "a", "a")])
    assert system.trajectory("aaa", max_steps=99) == ["aaa"]


# ============================================================================
# 5. What trajectory_bisimilar actually decides
# ============================================================================


def test_characterises_it_is_list_equality() -> None:
    import random

    random.seed(7)
    for _ in range(2000):
        left = [random.choice("abc") for _ in range(random.randint(0, 4))]
        right = [random.choice("abc") for _ in range(random.randint(0, 4))]
        assert trajectory_bisimilar(left, right) == (list(left) == list(right))


def test_characterises_it_takes_no_transition_system() -> None:
    # Bisimilarity is a property of the branching structure two states sit in.
    # This function is handed two sequences and nothing else, so no function of
    # its inputs can be it -- the same argument that applies to a halting
    # predicate whose input carries no program.
    import inspect

    parameters = list(inspect.signature(trajectory_bisimilar).parameters)
    assert parameters == ["traj1", "traj2"]


def test_characterises_two_states_that_are_not_bisimilar_are_called_bisimilar() -> None:
    # "ab" under `halts` has no successor after one step. "ab" under `cycles`
    # steps forever. No bisimulation relates them. Their traces truncated at one
    # step are equal, and that is what gets compared.
    halts = RewriteSystem([RewriteRule("f", "ab", "ba")])
    cycles = RewriteSystem([RewriteRule("f", "ab", "ba"), RewriteRule("b", "ba", "ab")])

    assert halts.step("ba") == []
    assert cycles.step("ba") == ["ab"]

    left = halts.trajectory("ab", max_steps=1)
    right = cycles.trajectory("ab", max_steps=1)
    assert left == right == ["ab", "ba"]
    assert trajectory_bisimilar(left, right) is True


def test_traces_of_different_lengths_are_not_equal() -> None:
    assert trajectory_bisimilar(["A", "B", "C"], ["A", "B"]) is False


# ============================================================================
# 6. The shift operator
# ============================================================================


def test_the_shift_drops_the_first_k_states() -> None:
    trace = ["s0", "s1", "s2", "s3"]
    assert shift_operator(trace, 0) == trace
    assert shift_operator(trace, 1) == ["s1", "s2", "s3"]
    assert shift_operator(trace, 3) == ["s3"]


def test_shifting_past_the_end_is_not_invertible() -> None:
    # On an infinite trajectory the shift is a bijection. On a finite trace it
    # is not: every k at or past the length gives the same empty result, so k
    # cannot be recovered from it.
    trace = ["s0", "s1", "s2"]
    assert shift_operator(trace, 3) == []
    assert shift_operator(trace, 4) == []
    assert shift_operator(trace, 100) == []


def test_a_negative_shift_is_refused() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        shift_operator(["s0"], -1)
