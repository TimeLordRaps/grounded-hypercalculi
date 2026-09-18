import pytest
from grounded_hypercalculi.oracle_calculus import (
    ComputationalQuery,
    ConclusionAnalysis,
    HaltingStatus,
    Hyperoracle,
    LeapfrogComputation,
    OracleTower,
    TuringDegree,
)


def test_turing_degree_hierarchy():
    d0 = TuringDegree(0, "0")
    assert d0.is_computable
    d1 = d0.jump()
    assert d1.rank == 1
    assert not d1.is_computable
    assert d0 < d1
    d2 = d1.jump()
    assert d1 < d2


def test_oracle_tower_halting_decisions():
    tower = OracleTower()
    q_standard = ComputationalQuery("collatz_sim", 27, complexity_rank=0)
    q_relativized = ComputationalQuery("jump_pred", 1, complexity_rank=1)

    # Level 0 cannot decide rank 0 halting
    assert tower.decide_halting(q_standard, oracle_level=0) == HaltingStatus.UNDECIDABLE_AT_TIER

    # Level 1 oracle decides rank 0
    status1 = tower.decide_halting(q_standard, oracle_level=1)
    assert status1 in (HaltingStatus.HALTS, HaltingStatus.LOOPS)

    # Level 1 oracle cannot decide rank 1 halting
    assert tower.decide_halting(q_relativized, oracle_level=1) == HaltingStatus.UNDECIDABLE_AT_TIER

    # Level 2 oracle decides rank 1
    status2 = tower.decide_halting(q_relativized, oracle_level=2)
    assert status2 in (HaltingStatus.HALTS, HaltingStatus.LOOPS)


def test_leapfrog_transomega_computation():
    leapfrog = LeapfrogComputation(dimension=1)
    # Linear recurrence f(s, i) = s + 5
    trans_rule = lambda s, i: s + 5
    # Contracting an omega^omega transfinite stage sequence (e.g. 1000 stages) into instant time
    result = leapfrog.leapfrog_step(initial_state=10, transition_rule=trans_rule, ordinal_stages=1000)
    assert result == 10 + 5 * 1000


def test_hyperoracle_resolves_all_finite_towers():
    hyperoracle = Hyperoracle()
    tower = OracleTower()
    queries = [
        ComputationalQuery("prog_0", 1, complexity_rank=0),
        ComputationalQuery("prog_1", 2, complexity_rank=1),
        ComputationalQuery("prog_5", 5, complexity_rank=5),
    ]
    # Hyperoracle decides entire collection across all levels simultaneously in unit time
    results = hyperoracle.evaluate_tower(tower, queries)
    assert len(results) == 3
    for q in queries:
        assert results[q.program_id] in (HaltingStatus.HALTS, HaltingStatus.LOOPS)

    # Hyperhalting test
    assert isinstance(hyperoracle.solve_hyperhalting("omega_machine"), bool)


def test_conclusion_analysis():
    analyzer = ConclusionAnalysis()
    # P asserts its own halting relative to rank 2
    status, resolved_rank = analyzer.analyze_conclusion("self_ref_statement", base_rank=2)
    assert resolved_rank == 3
    assert status in (HaltingStatus.HALTS, HaltingStatus.LOOPS)


def test_transfinite_oracle_tower_invariants():
    tower = OracleTower(max_level=20)
    # Tower of halting queries
    queries = [ComputationalQuery(f"halt_{i}", i, complexity_rank=i) for i in range(10)]
    for i, q in enumerate(queries):
        # Oracle of tier i cannot decide query of rank i
        assert tower.decide_halting(q, oracle_level=i) == HaltingStatus.UNDECIDABLE_AT_TIER
        # Oracle of tier i + 1 decides query of rank i
        assert tower.decide_halting(q, oracle_level=i + 1) in (HaltingStatus.HALTS, HaltingStatus.LOOPS)


def test_leapfrog_multidimensional_state():
    leapfrog = LeapfrogComputation(dimension=2)
    # Coordinate progression (x, y) -> (x + 1, y * 2). The rule was previously
    # written as (x + 1, y), which is the affine case the old extrapolation
    # happened to get right; the comment described the multiplicative case the
    # whole time. Restored to what it says.
    rule = lambda s, i: (s[0] + 1, s[1] * 2)
    initial = (0, 1)
    final_state = leapfrog.leapfrog_step(initial, rule, ordinal_stages=10)
    assert final_state[0] == 10
    assert final_state[1] == 2**10


def test_conclusion_analysis_closure():
    analyzer = ConclusionAnalysis()
    # Analyzing multiple self-referential statements across varying base ranks
    for rank in range(1, 6):
        status, needed_rank = analyzer.analyze_conclusion(f"diagonal_stmt_{rank}", base_rank=rank)
        assert needed_rank == rank + 1
        assert status in (HaltingStatus.HALTS, HaltingStatus.LOOPS)
