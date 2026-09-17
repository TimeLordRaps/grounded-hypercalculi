# Grounded Hypercalculi

[![CI](https://github.com/TimeLordRaps/grounded-hypercalculi/actions/workflows/ci.yml/badge.svg)](https://github.com/TimeLordRaps/grounded-hypercalculi/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

*Because there are more calculi than just maths'.*

A unified formal framework and computational library implementing extended mathematical, symbolic, structural, and computational calculi.

---

## 1. The Six Formal Calculi

1. **Language Calculus** (`language_calculus.py`):
   - Formal syntax trees, alphabets, productions, and formal grammars (`Symbol`, `Alphabet`, `ProductionRule`, `Grammar`).
   - Reflexive non-well-founded quotation graphs (`QuotationNode.self_quoting`) under Aczel's Anti-Foundation Axiom (AFA).
   - Reverse-Polish-Notation (RPN) formal proof verifier for Metamath databases (`MetamathDatabase`) with sound Modus Ponens deduction.

2. **Meta-Calculus** (`meta_calculus.py`):
   - Symbolic dynamics of term rewrite systems (`RewriteRule`, `RewriteSystem`).
   - Infinite trajectory spaces $\mathcal{S}^\omega$, shift operators $\sigma$ (`shift_operator`), and coalgebraic trajectory bisimulation (`trajectory_bisimilar`).

3. **Hyper-Calculus** (`hyper_calculus.py`):
   - Canonical permutation representations and composition (`Permutation`).
   - Finite permutation groups, closure generation, group order, and action orbits (`PermutationGroup`).
   - Linear derivation operators on functional spaces satisfying the Leibniz product rule (`DerivationOperator.leibniz_check`).
   - Lie commutator brackets $[D_1, D_2] = D_1 \circ D_2 - D_2 \circ D_1$ preserving semantic Noether invariants (`commutator_bracket`).

4. **Ordinal Calculus** (`ordinal_calculus.py`):
   - Exact transfinite arithmetic below $\omega^\omega$ in Cantor Normal Form (`BoundedOrdinal`, `OMEGA`, `ZERO`, `ONE`).
   - Exact left subtraction ($\beta + \gamma = \alpha \implies \gamma = \alpha.\mathrm{left\_sub}(\beta)$).
   - Discrete difference operators $\Delta F(\alpha) = F(\alpha + 1) - F(\alpha)$ (`ordinal_difference`).
   - Ordinal derivative fixed-point enumeration (`ordinal_derivative`) failing closed on non-convergent stages.
   - Veblen hierarchies $\phi_\alpha(\beta)$ (`VeblenHierarchy`).

5. **Real Analysis Calculus** (`real_calculus.py`):
   - Exact grounded rational arithmetic with ordering and division (`GroundedRational`).
   - Dedekind cuts ($L, R$) of rationals with containment testing and constants (`DedekindCut.sqrt_two`).
   - Conway Surreal numbers $\{L | R\}$ supporting transfinite numbers and canonical infinitesimals $\epsilon = 1/\omega$ (`SurrealGame`, `SurrealGame.infinitesimal`), with strict numeric validation.
   - Cauchy sequences of rationals generating the continuum with convergence checks and canonical limits (`CauchySequence.euler_e`, `CauchySequence.geometric_series`).
   - Central difference numerical derivatives (`numerical_derivative`) and Riemann midpoint integration (`riemann_integral`).

6. **Oracle Calculus** (`oracle_calculus.py`):
   - Turing degrees and Turing jumps $A \mapsto A'$ (`TuringDegree`).
   - $\omega$-towers of halting problem oracles deciding computational queries (`OracleTower`, `ComputationalQuery`).
   - Trans-omega leapfrog computations runnable in unit time ($O(\omega^\omega)$ contracted via closed-form limits) (`LeapfrogComputation`).
   - Hyperoracles equipped with hyperjumps ($\Pi^1_1$-comprehension) deciding entire oracle towers simultaneously (`Hyperoracle`).
   - Conclusion analysis resolving self-referential diagonal queries by ascending oracle tiers (`ConclusionAnalysis`).

---

## 2. Position in the TimeLord Formal Ecosystem

`grounded-hypercalculi` operates in synergy with adjacent formal repositories:

- **`hypermath`**: Primitive foundational algebraic kernel, quadrilateral filtration (syntax $\sim\sim$, abstraction $\sim=$, substance $=~$, semantics $==$), and Lean 4 formal bridge.
- **`ordinatics`**: Ordinal-based metalanguage and stratified truth stage evaluation constructed up from `hypermath`.
- **`grounded-hyperset-theory`**: Aczel's Anti-Foundation Axiom (AFA), Accessible Pointed Graphs (APGs), circular sets, and bisimulation quotienting.
- **`grounded-hypercalculi`**: The unified domain language and execution engine for all formal calculi.
- **`verifier`**: Verification standard language (`VSTD`), two-axis ladder, refutation certificates, and presentation discipline.

---

## 3. Quickstart

```python
import grounded_hypercalculi as gh

# 1. Ordinal arithmetic below omega^omega
alpha = gh.OMEGA + gh.BoundedOrdinal.from_int(5)  # omega + 5
gamma = alpha.left_sub(gh.BoundedOrdinal.from_int(3))
assert gamma == alpha  # 3 + (omega + 5) = omega + 5

# 2. Hyper-Calculus: S_3 permutation group
p1 = gh.Permutation({1: 2, 2: 1})
p2 = gh.Permutation({2: 3, 3: 2})
s3 = gh.PermutationGroup(generators=[p1, p2])
assert s3.order() == 6
assert s3.orbit(1) == {1, 2, 3}

# 3. Real Analysis: Cauchy sequences and Surreal infinitesimals
e_seq = gh.CauchySequence.euler_e()
assert e_seq.is_cauchy()
print(f"e approx: {e_seq.limit(10):.5f}")  # 2.71828

eps = gh.SurrealGame.infinitesimal()
assert 0.0 < eps.value < 0.5

# 4. Oracle Calculus: Halting decisions across oracle tiers
tower = gh.OracleTower()
query = gh.ComputationalQuery("collatz_conjecture", 27, complexity_rank=0)
assert tower.decide_halting(query, oracle_level=0) == gh.HaltingStatus.UNDECIDABLE_AT_TIER
assert tower.decide_halting(query, oracle_level=1) in (gh.HaltingStatus.HALTS, gh.HaltingStatus.LOOPS)
```

---

## 4. Verification and Conformance

```bash
# Run the complete test suite
python -m pytest -q

# Run presentation and boundary gate
python scripts/check_presentation.py

# Verify pure standard library import purity
PYTHONPATH=src python -S -c "import grounded_hypercalculi as gh; print(gh.__version__)"

# Verify build reproducibility across platforms
python scripts/release_artifacts.py compare PATH_TO_LINUX_ARTIFACTS PATH_TO_WINDOWS_ARTIFACTS
```

---

## 5. License

Apache License 2.0. See [LICENSE](LICENSE).
