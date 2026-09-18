"""Oracle Calculus: hypercomputation, trans-omega leapfrog computations, and oracle towers.

Oracle calculus formalizes:
1. Turing Degrees and Turing Jumps: A |-> A' representing the halting problem relative to oracle A.
2. omega-Towers of Halting Problems: Sequences 0, 0', 0'', ..., 0^(omega), ..., 0^(alpha) where each
   tier decides the halting problem of the lower tiers.
3. Leapfrog Computations: Evaluation of a staged state trajectory to a terminal conclusion,
   under a declared stage budget.
4. Hyperoracles: Oracles equipped with hyperjumps (Kleene's O / Pi^1_1-complete truth), standing
   above the finite tiers of the tower.
5. Conclusion Analysis: Lifting a self-referential query to the next oracle rank, so that a
   diagonal statement is answered one tier above the one it talks about.

What is modelled and what is computed
-------------------------------------
The tier arithmetic in this module is real: which rank an oracle must exceed to
address a query, how a jump raises a degree, and how a self-referential query is
lifted are all computed from the stated hierarchy, and are tested as such.

The HALTS/LOOPS verdicts are not. Halting is undecidable, and no
ComputationalQuery carries a program in any case -- it carries a label, an
integer, a description and a rank -- so there is nothing for a decision
procedure to read. Where this module must produce a verdict it derives one
deterministically from a hash of the query's label, which makes results
reproducible and carries no information about whether anything halts. Read a
verdict as an opaque, stable token attached to a label, never as evidence about
a program. See tests/test_oracle_calculus_semantics.py, which pins exactly this.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


def _deterministic_hash(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


# Default ceiling on stages LeapfrogComputation will evaluate in one call. The
# operator refuses past it rather than extrapolating from a sample.
_DEFAULT_STAGE_BUDGET = 1_000_000



class HaltingStatus(Enum):
    """Verdict of a computation with respect to an oracle tier."""
    HALTS = "HALTS"
    LOOPS = "LOOPS"
    UNDECIDABLE_AT_TIER = "UNDECIDABLE_AT_TIER"


@dataclass(frozen=True)
class TuringDegree:
    """A Turing degree representing an equivalence class of computational complexity."""
    rank: int
    name: str = ""

    def __post_init__(self) -> None:
        if self.rank < 0:
            raise ValueError("Turing degree rank must be non-negative")

    @property
    def is_computable(self) -> bool:
        """Degree 0 is the class of computable / recursive functions."""
        return self.rank == 0

    def jump(self) -> TuringDegree:
        """The Turing jump operation A |-> A'."""
        next_name = f"{self.name}'" if self.name else f"0^({self.rank + 1})"
        return TuringDegree(self.rank + 1, next_name)

    def __lt__(self, other: TuringDegree) -> bool:
        return self.rank < other.rank

    def __le__(self, other: TuringDegree) -> bool:
        return self.rank <= other.rank


@dataclass(frozen=True)
class ComputationalQuery:
    """A program or proposition query submitted to an oracle machine."""
    program_id: str
    input_val: int
    description: str = ""
    complexity_rank: int = 0


@dataclass
class OracleTower:
    """An omega-tower of halting problem oracles.
    
    Level 0: Empty oracle (standard Turing machines).
    Level 1: Halting oracle 0' deciding standard Turing machines.
    Level n+1: Halting oracle 0^(n+1) deciding machines with oracle 0^(n).
    Level omega: Effective join of all finite levels.
    """
    max_level: int = 10
    _decided_cache: Dict[Tuple[int, str, int], HaltingStatus] = field(default_factory=dict)

    def decide_halting(self, query: ComputationalQuery, oracle_level: int) -> HaltingStatus:
        """Return this tower's verdict for a query addressed at ``oracle_level``.

        UNDECIDABLE_AT_TIER is a real result: it is returned exactly when
        ``oracle_level <= query.complexity_rank``, which is the stated condition
        for a tier to be too low to address the query, and it holds for every
        query regardless of its label.

        HALTS and LOOPS are not results. They are a deterministic placeholder,
        derived from a hash of ``program_id`` and ``input_val``, and they say
        nothing about whether any program halts -- ``query`` does not contain a
        program to ask about. The verdict is stable across calls and towers, so
        it is reproducible; it is not evidence. Renaming a query changes it.

        Raises:
            ValueError: ``oracle_level`` is negative.
        """
        if oracle_level < 0:
            raise ValueError("Oracle level must be non-negative")
        
        # A problem of complexity rank k requires an oracle of level > k
        if oracle_level <= query.complexity_rank:
            return HaltingStatus.UNDECIDABLE_AT_TIER

        cache_key = (oracle_level, query.program_id, query.input_val)
        if cache_key in self._decided_cache:
            return self._decided_cache[cache_key]

        # Deterministic simulation of the oracle decision
        # In oracle calculus, the oracle machine at level k+1 has an oracle tape that
        # instantly evaluates the characteristic function of the halting problem at level k.
        status = HaltingStatus.HALTS if (_deterministic_hash(f"{query.program_id}:{query.input_val}") % 2 == 0) else HaltingStatus.LOOPS
        self._decided_cache[cache_key] = status
        return status


@dataclass(frozen=True)
class LeapfrogComputation:
    """Staged state-progression operator.

    Evaluates a transition rule stage by stage from an initial state to a
    requested stage count, and refuses past a declared budget.

    This operator does not contract a derivation into unit time. An arbitrary
    ``Callable`` exposes no algebraic structure to contract, and the closed form
    this class previously extrapolated -- one probe step scaled by the stage
    count -- is the sequence's value only for ``s -> s + c``. Returning a wrong
    value quickly is not an acceleration, so the stages are evaluated instead.
    """
    dimension: int
    contraction_factor: float = 1.0

    def leapfrog_step(
        self,
        initial_state: Any,
        transition_rule: Callable[[Any, int], Any],
        ordinal_stages: int,
        *,
        max_evaluated_stages: int = _DEFAULT_STAGE_BUDGET,
    ) -> Any:
        """Return the state reached after ``ordinal_stages`` applications of the rule.

        Stage ``i`` is ``transition_rule(state, i)``, so the result is the rule
        composed with itself ``ordinal_stages`` times starting from
        ``initial_state``.

        No closed form is assumed. An arbitrary ``Callable`` carries no algebraic
        structure the operator can read, so there is nothing to contract: the
        stages are evaluated. The earlier implementation sampled a single step,
        took ``delta = transition_rule(s0, 0) - s0`` and returned
        ``s0 + delta * ordinal_stages``, which is the sequence's value only when
        the rule is ``s -> s + c`` for a ``c`` independent of both the state and
        the stage index. Under ``s -> s / 2`` from ``1.0`` over ten stages that
        extrapolation returned ``-4.0``, for a sequence that is positive and
        decreasing towards zero; under ``s -> (s + 1) % 7`` it returned ``10``,
        which is not in the rule's codomain at all.

        A caller who does possess a closed form for a particular rule should
        apply it and pass the resulting stage count, rather than have this
        operator guess one from a two-point sample.

        Args:
            initial_state: The stage-zero state. Any type the rule accepts.
            transition_rule: ``(state, stage_index) -> next_state``.
            ordinal_stages: How many stages to evaluate. Must be non-negative.
            max_evaluated_stages: Evaluation budget. Beyond it the operator
                refuses rather than substituting an unverified extrapolation.

        Raises:
            ValueError: ``ordinal_stages`` is negative, or exceeds
                ``max_evaluated_stages``. Exceeding the budget is a refusal, not
                a verdict that the stage sequence diverges -- the value is
                unknown to this operator, not established to be anything.
        """
        if ordinal_stages < 0:
            raise ValueError("Ordinal stages must be non-negative")
        if max_evaluated_stages < 0:
            raise ValueError("Stage budget must be non-negative")
        if ordinal_stages == 0:
            return initial_state
        if ordinal_stages > max_evaluated_stages:
            raise ValueError(
                f"ordinal_stages {ordinal_stages} exceeds the evaluation budget "
                f"{max_evaluated_stages}; no closed form is established for an "
                f"arbitrary transition rule, so the stages would have to be "
                f"evaluated. Raise max_evaluated_stages to spend the steps, or "
                f"contract the sequence yourself and pass the reduced count."
            )

        state = initial_state
        for stage_index in range(ordinal_stages):
            state = transition_rule(state, stage_index)
        return state


@dataclass
class Hyperoracle:
    """A hyperoracle equipped with hyperjumps (Kleene's O / Pi^1_1-comprehension).

    Models an oracle standing above every finite tier of the arithmetic
    hierarchy (Sigma^0_n).

    Its verdicts carry the same caveat as ``OracleTower.decide_halting``: they
    are deterministic placeholders keyed on a query label, not decisions.
    ``evaluate_tower`` currently evaluates the same expression as a level-one
    tower, and consults neither the ``tower`` argument nor each query's rank.
    """
    power_rank: str = "Pi_1_1"

    def evaluate_tower(self, tower: OracleTower, queries: Sequence[ComputationalQuery]) -> Dict[str, HaltingStatus]:
        """Return a placeholder verdict for each query, keyed by program_id.

        Not a decision over the tower: ``tower`` is unused, each query's rank is
        ignored, and the verdicts are the label-keyed placeholders described on
        ``OracleTower.decide_halting``. Queries sharing a ``program_id`` collapse
        to one entry in the returned mapping.
        """
        results: Dict[str, HaltingStatus] = {}
        for q in queries:
            # Placeholder verdict -- see the class docstring. Deterministic so
            # that results are reproducible, and informative about nothing.
            status = HaltingStatus.HALTS if (_deterministic_hash(f"{q.program_id}:{q.input_val}") % 2 == 0) else HaltingStatus.LOOPS
            results[q.program_id] = status
        return results

    def solve_hyperhalting(self, oracle_machine_id: str) -> bool:
        """Return a deterministic placeholder flag for a machine identifier.

        Named for the hyperhalting problem this position in the hierarchy would
        address; it does not address it. The value is a hash of the identifier
        and is true for roughly two thirds of identifiers, which is a property
        of the hash, not of any machine.
        """
        return (_deterministic_hash(oracle_machine_id) % 3) != 0



@dataclass
class ConclusionAnalysis:
    """Conclusion analysis operator: fixed-point closure of self-referential oracle queries.
    
    Given a self-referential proposition P that queries its own halting status,
    conclusion analysis lifts the query to rank(P) + 1, resolving the diagonal
    impasses without paradoxical oscillation.
    """
    tower: OracleTower = field(default_factory=OracleTower)

    def analyze_conclusion(self, statement_id: str, base_rank: int = 0) -> Tuple[HaltingStatus, int]:
        """Resolve a self-referential proposition by ascending the minimal necessary oracle rank."""
        query = ComputationalQuery(program_id=statement_id, input_val=0, complexity_rank=base_rank)
        required_oracle_level = base_rank + 1
        status = self.tower.decide_halting(query, oracle_level=required_oracle_level)
        return status, required_oracle_level
