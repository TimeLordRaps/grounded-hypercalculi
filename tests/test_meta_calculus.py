import pytest
from grounded_hypercalculi.meta_calculus import (
    RewriteRule,
    RewriteSystem,
    shift_operator,
    trajectory_bisimilar,
)


def test_rewrite_system_and_trajectories():
    sys = RewriteSystem()
    sys.add_rule(RewriteRule("r1", "A", "B"))
    sys.add_rule(RewriteRule("r2", "B", "C"))

    traj = sys.trajectory("A", max_steps=5)
    assert traj == ["A", "B", "C"]

    # Shift operator
    shifted = shift_operator(traj, k=1)
    assert shifted == ["B", "C"]

    # Trajectory bisimulation
    assert trajectory_bisimilar(traj, ["A", "B", "C"])
    assert not trajectory_bisimilar(traj, ["A", "B"])


def test_rewrite_rule_conditional():
    # Only rewrite if length is greater than 3
    rule = RewriteRule("cond_r", "X", "Y", condition=lambda s: len(s) > 3)
    assert rule.apply("X") is None
    assert rule.apply("XXXX") == "YXXX"

