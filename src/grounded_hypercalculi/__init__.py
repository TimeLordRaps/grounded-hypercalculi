"""Grounded Hypercalculi: A unified domain framework for extended computational and mathematical calculi."""

from __future__ import annotations

from .oracle_calculus import (
    ComputationalQuery,
    ConclusionAnalysis,
    HaltingStatus,
    Hyperoracle,
    LeapfrogComputation,
    OracleTower,
    TuringDegree,
)
from .language_calculus import (
    Alphabet,
    Grammar,
    MetamathDatabase,
    ProductionRule,
    QuotationNode,
    Symbol,
)
from .meta_calculus import (
    RewriteRule,
    RewriteSystem,
    shift_operator,
    trajectory_bisimilar,
)
from .hyper_calculus import (
    DerivationOperator,
    Permutation,
    PermutationGroup,
    commutator_bracket,
)
from .ordinal_calculus import (
    BoundedOrdinal,
    OMEGA,
    ONE,
    ZERO,
    VeblenHierarchy,
    ordinal_derivative,
    ordinal_difference,
)
from .real_calculus import (
    CauchySequence,
    DedekindCut,
    GroundedRational,
    SurrealGame,
    numerical_derivative,
    riemann_integral,
)

__version__ = "0.1.0"

__all__ = [
    # Oracle Calculus
    "ComputationalQuery",
    "ConclusionAnalysis",
    "HaltingStatus",
    "Hyperoracle",
    "LeapfrogComputation",
    "OracleTower",
    "TuringDegree",
    # Language Calculus
    "Alphabet",
    "Grammar",
    "MetamathDatabase",
    "ProductionRule",
    "QuotationNode",
    "Symbol",
    # Meta Calculus
    "RewriteRule",
    "RewriteSystem",
    "shift_operator",
    "trajectory_bisimilar",
    # Hyper Calculus
    "DerivationOperator",
    "Permutation",
    "PermutationGroup",
    "commutator_bracket",
    # Ordinal Calculus
    "BoundedOrdinal",
    "OMEGA",
    "ONE",
    "ZERO",
    "VeblenHierarchy",
    "ordinal_derivative",
    "ordinal_difference",
    # Real Calculus
    "CauchySequence",
    "DedekindCut",
    "GroundedRational",
    "SurrealGame",
    "numerical_derivative",
    "riemann_integral",
]

