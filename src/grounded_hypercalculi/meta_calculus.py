"""Meta-Calculus: symbolic dynamics of string rewrite systems and trajectory traces.

What is here: ``RewriteRule`` and ``RewriteSystem`` over states that are plain
strings, the one-step successor relation, deterministic trajectory traces, the
shift operator on a trace, and a trace comparison.

What is *not* here, despite earlier wording. There is no Coxeter word-homotopy.
Trajectory spaces are not infinite: a trajectory is a finite list produced under
a step budget. And ``trajectory_bisimilar`` is not bisimulation -- it compares
two finite traces for equality, takes no transition system, and therefore cannot
be a function of the branching structure that bisimilarity is about. See its
docstring for what it does decide and what that is worth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class RewriteRule:
    """A transition rule in a symbolic rewrite system."""
    name: str
    pattern: str
    replacement: str
    condition: Optional[Callable[[Any], bool]] = None

    def __post_init__(self) -> None:
        # An empty pattern occurs in every string, including the rule's own
        # output, so the rule is always applicable and the state grows forever:
        # "abc" -> "Xabc" -> "XXabc", ending only at the step budget. That is not
        # a rewrite rule, and it makes every termination question vacuous.
        if not self.pattern:
            raise ValueError(
                f"rule {self.name!r} has an empty pattern, which matches every "
                f"state including its own output; a rewrite rule must have a "
                f"non-empty left-hand side"
            )

    def apply(self, state: str) -> Optional[str]:
        """Rewrite the leftmost occurrence of the pattern, or None.

        Returns None when the condition fails or the pattern does not occur.
        This is the leftmost redex only; ``apply_all`` gives every one-step
        result.
        """
        if self.condition is not None and not self.condition(state):
            return None
        if self.pattern in state:
            return state.replace(self.pattern, self.replacement, 1)
        return None

    def apply_all(self, state: str) -> List[str]:
        """Every one-step rewrite of ``state`` by this rule, leftmost first.

        A rule may match a state in more than one place, and each match is a
        distinct step of the rewrite relation. For ``a -> b`` the state ``"aa"``
        rewrites to both ``"ba"`` and ``"ab"``; taking only the first loses the
        second permanently, since no sequence of leftmost-only steps reaches it.

        Overlapping occurrences are included: for ``aa -> b`` the state ``"aaa"``
        has a redex at index 0 and at index 1, and both are steps.
        """
        if self.condition is not None and not self.condition(state):
            return []
        results: List[str] = []
        width = len(self.pattern)
        start = 0
        while True:
            index = state.find(self.pattern, start)
            if index < 0:
                break
            rewritten = state[:index] + self.replacement + state[index + width:]
            if rewritten not in results:
                results.append(rewritten)
            start = index + 1
        return results



@dataclass
class RewriteSystem:
    """A symbolic rewrite system defining a state transition graph."""
    rules: List[RewriteRule] = field(default_factory=list)

    def add_rule(self, rule: RewriteRule) -> None:
        self.rules.append(rule)

    def step(self, state: str) -> List[str]:
        """Every immediate successor of ``state`` under the one-step relation.

        A rule contributes one successor per place it matches, not one per rule.
        Ordering is rule order, then leftmost redex, and duplicates are dropped
        while keeping first appearance -- so ``step(s)[0]`` is unchanged from
        when this returned only the leftmost rewrite of each rule, and
        ``trajectory`` is unaffected.

        It previously returned one successor per rule. For ``a -> b``,
        ``step("aa")`` was ``["ba"]``: ``"ab"`` is a one-step rewrite of ``"aa"``
        and was not reachable from it by any number of steps. Anything computed
        over that relation -- reachability, joinability, confluence -- was
        computed over a proper subgraph of the real one.
        """
        successors: List[str] = []
        for rule in self.rules:
            for result in rule.apply_all(state):
                if result not in successors:
                    successors.append(result)
        return successors

    def trajectory(
        self,
        initial: str,
        max_steps: int = 10,
        *,
        stop_on_repeat: bool = False,
    ) -> List[str]:
        """The trace from ``initial``, following the first successor each step.

        "First" is ``step(state)[0]``: the leftmost redex of the earliest rule
        that applies. The trace includes ``initial``, so it has at most
        ``max_steps + 1`` entries.

        Stopping is ambiguous by construction and the caller has to read it off
        the length. A trace **shorter** than ``max_steps + 1`` ended on its own,
        having reached a state with no successor or a self-loop. A trace of
        exactly ``max_steps + 1`` entries usually means the budget ran out with
        the trajectory still moving -- but not always, since a trajectory that
        happens to end on that step looks identical. Call again with a larger
        ``max_steps`` to tell them apart, or pass ``stop_on_repeat``.

        Only self-loops end the trace; a longer cycle does not. ``ab -> ba`` with
        ``ba -> ab`` runs to the budget and returns ``max_steps + 1`` alternating
        states. With ``stop_on_repeat=True`` the trace stops the first time a
        state recurs, which makes the whole infinite orbit readable from a finite
        trace: the repeated state marks where the cycle closes.

        Raises:
            ValueError: if ``max_steps`` is negative. It previously returned
                ``[initial]``, which is what a terminating trajectory also
                returns.
        """
        if max_steps < 0:
            raise ValueError("max_steps must be non-negative")
        curr = initial
        trace = [curr]
        seen = {curr}
        for _ in range(max_steps):
            succs = self.step(curr)
            if not succs or succs[0] == curr:
                break
            curr = succs[0]
            trace.append(curr)
            if stop_on_repeat:
                if curr in seen:
                    break
                seen.add(curr)
        return trace


def shift_operator(trajectory: Sequence[Any], k: int = 1) -> List[Any]:
    """Drop the first ``k`` states: sigma^k(pi)_i = pi_{i+k}.

    On a genuinely infinite trajectory the shift is a bijection. On the finite
    traces this module produces it is not: a trace of length n shifted by n or
    more gives ``[]``, and every k past the end gives the same ``[]``, so the
    shift is not invertible and k is not recoverable from the result.
    """
    if k < 0:
        raise ValueError("Shift steps must be non-negative")
    return list(trajectory[k:])


def trajectory_bisimilar(traj1: Sequence[Any], traj2: Sequence[Any]) -> bool:
    """Whether two traces are equal: same length, same states in the same order.

    This is not bisimulation, and the name predates the observation. Two states
    are bisimilar when every step of one is matched by a step of the other with
    bisimilar results, which is a property of the *branching structure* of a
    transition system. This function receives two sequences and no transition
    system, so no function of its inputs can be bisimilarity -- the same argument
    that applies to a halting predicate taking no program.

    It is exactly ``list(traj1) == list(traj2)``, which has been checked against
    2000 random pairs. What that decides is worth something: two deterministic
    traces of equal length agree pointwise. What it does not decide is whether
    the states they start from behave alike. Take ``ab`` under a system whose
    only rule is ``ab -> ba``, and ``ab`` under a system with ``ab -> ba`` and
    ``ba -> ab``. One halts after a step and one runs forever, so the two states
    are not bisimilar; their traces truncated at one step are both
    ``["ab", "ba"]`` and this returns True.

    Comparing traces is therefore sound only against the prefix they cover, and
    a trace cut off by a step budget covers less than it appears to.
    """
    if len(traj1) != len(traj2):
        return False
    return all(s1 == s2 for s1, s2 in zip(traj1, traj2))
