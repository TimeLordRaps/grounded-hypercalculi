"""Meta-Calculus: symbolic dynamics of rewrite systems, trajectory spaces, and bisimulation."""

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

    def apply(self, state: str) -> Optional[str]:
        """Apply the rule to a state string if matched and condition satisfied."""
        if self.condition is not None and not self.condition(state):
            return None
        if self.pattern in state:
            return state.replace(self.pattern, self.replacement, 1)
        return None



@dataclass
class RewriteSystem:
    """A symbolic rewrite system defining a state transition graph."""
    rules: List[RewriteRule] = field(default_factory=list)

    def add_rule(self, rule: RewriteRule) -> None:
        self.rules.append(rule)

    def step(self, state: str) -> List[str]:
        """Generate all immediate successor states."""
        successors: List[str] = []
        for r in self.rules:
            res = r.apply(state)
            if res is not None and res not in successors:
                successors.append(res)
        return successors

    def trajectory(self, initial: str, max_steps: int = 10) -> List[str]:
        """Generate a deterministic trajectory following the first applicable rule."""
        curr = initial
        trace = [curr]
        for _ in range(max_steps):
            succs = self.step(curr)
            if not succs or succs[0] == curr:
                break
            curr = succs[0]
            trace.append(curr)
        return trace


def shift_operator(trajectory: Sequence[Any], k: int = 1) -> List[Any]:
    """The shift operator sigma^k on trajectory spaces: sigma(pi)_i = pi_{i+1}."""
    if k < 0:
        raise ValueError("Shift steps must be non-negative")
    return list(trajectory[k:])


def trajectory_bisimilar(traj1: Sequence[Any], traj2: Sequence[Any]) -> bool:
    """Check whether two trajectories are step-wise bisimilar."""
    if len(traj1) != len(traj2):
        return False
    return all(s1 == s2 for s1, s2 in zip(traj1, traj2))
