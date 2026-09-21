# Grounded Hypercalculi

[![CI](https://github.com/TimeLordRaps/grounded-hypercalculi/actions/workflows/ci.yml/badge.svg)](https://github.com/TimeLordRaps/grounded-hypercalculi/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

*Because there are more calculi than just maths'.*

A unified formal framework and computational library implementing extended mathematical, symbolic, structural, and computational calculi.

**Preprint:** *The Six Grounded Hypercalculi: An Integrated Framework for Relativized Oracles, Metasystem Reflection, and Hypercomputation* ([PDF](paper/paper.pdf), [source](paper/paper.tex)) --- version 0.2.0, September 18, 2026.

The paper states each calculus's capability boundary explicitly, including the points at which a component returns a deterministic placeholder rather than a decision. Receipt emission under the Verifier Standard is specified there as the intended verification interface and is **not implemented**; no result in the paper rests on it.

---

## 1. The Six Formal Calculi

1. **Language Calculus** (`language_calculus.py`):
   - Formal syntax trees, alphabets, productions, and formal grammars (`Symbol`, `Alphabet`, `ProductionRule`, `Grammar`).
   - Reflexive non-well-founded quotation graphs (`QuotationNode.self_quoting`) under Aczel's Anti-Foundation Axiom (AFA).
   - Reverse-Polish-Notation (RPN) proof checker (`MetamathDatabase`) for a Metamath-style
     fragment: hypotheses, axioms, cited theorems and modus ponens. Hypotheses are matched
     literally rather than by substitution, so it rejects some proofs a full Metamath
     verifier accepts, and licenses no step whose hypotheses were not supplied.

2. **Meta-Calculus** (`meta_calculus.py`):
   - Symbolic dynamics of string rewrite systems (`RewriteRule`, `RewriteSystem`).
     `step` returns every one-step successor, one per place a rule matches rather
     than one per rule, so reachability and joinability are computed over the whole
     relation.
   - Finite trajectory traces under a declared step budget, and the shift operator
     $\sigma$ on them (`shift_operator`). Traces are finite lists, not points of
     $\mathcal{S}^\omega$, and the shift is not invertible past the end of one.
   - Trace comparison (`trajectory_bisimilar`). **This is trace equality, not
     bisimulation**: it receives two sequences and no transition system, so it cannot
     be a function of the branching structure bisimilarity is about. The name is
     public API on a released version; see the docstring for what it does decide.

3. **Hyper-Calculus** (`hyper_calculus.py`):
   - Canonical permutation representations and composition (`Permutation`).
   - Finite permutation groups from explicit generators, with closure generation, group
     order, and action orbits (`PermutationGroup`). The closure is enumerated under a
     declared budget and refuses past it; orbits are computed directly from the
     generators, so they are available for groups far too large to enumerate.
   - Derivation operators over a caller-supplied map on functions, with a pointwise
     Leibniz check (`DerivationOperator.leibniz_check`). The Leibniz rule is *tested* at
     a point, not enforced at construction: the operator holds whatever map it is given.
   - Lie commutator brackets (`commutator_bracket`):
     $$[D_1, D_2] = D_1 \circ D_2 - D_2 \circ D_1$$
     The bracket of two derivations is itself a derivation, which general linear
     operators do not satisfy; this is tested rather than asserted.

4. **Ordinal Calculus** (`ordinal_calculus.py`):
   - Exact transfinite arithmetic below $\omega^\omega$ in Cantor Normal Form (`BoundedOrdinal`, `OMEGA`, `ZERO`, `ONE`).
   - Exact left subtraction $\beta + \gamma = \alpha \implies \gamma = \alpha - \beta$ (`alpha.left_sub(beta)`).
   - Discrete difference operators $\Delta F(\alpha) = F(\alpha + 1) - F(\alpha)$ (`ordinal_difference`).
   - Ordinal derivative fixed-point enumeration (`ordinal_derivative`) failing closed on non-convergent stages.
   - Veblen hierarchies $\varphi_\alpha(\beta)$ on the $\alpha = 0$ row, $\varphi_0(\beta) = \omega^\beta$; higher rows start at $\varepsilon_0$ and are refused as unrepresentable (`VeblenHierarchy`).

5. **Real Analysis Calculus** (`real_calculus.py`):
   - Exact grounded rational arithmetic with ordering and division (`GroundedRational`).
   - Dedekind cuts $(L, R)$ of rationals with containment testing and constants (`DedekindCut.sqrt_two`). A cut carrying only bounds refuses membership questions inside them rather than answering False.
   - Conway Surreal numbers $\{L \mid R\}$ valued by the simplicity rule, with strict numeric validation (`SurrealGame`). Options are floats, so transfinite and genuinely infinitesimal games are outside this representation; `SurrealGame.infinitesimal` is a finite truncation of $\epsilon$ whose value is $1/8$.
   - Cauchy sequences of rationals generating the continuum, with canonical limits and a windowed screen for the Cauchy criterion (`CauchySequence.euler_e`, `CauchySequence.geometric_series`). The screen is evidence in both directions and a proof in neither; see `is_cauchy`.
   - Central difference numerical derivatives (`numerical_derivative`) and Riemann midpoint integration (`riemann_integral`).

6. **Oracle Calculus** (`oracle_calculus.py`):
   - Turing degrees and Turing jumps $A \mapsto A^\prime$ (`TuringDegree`).
   - $\omega$ towers of halting problem oracles, computing which tier is required to address a query (`OracleTower`, `ComputationalQuery`).
   - Staged trans-omega state progressions evaluated to a terminal conclusion under a declared stage budget (`LeapfrogComputation`).
   - Hyperoracles equipped with hyperjumps ($\Pi_1^1$ comprehension), standing above the finite tiers (`Hyperoracle`).

   The tier arithmetic is computed. The `HALTS`/`LOOPS` verdicts are deterministic placeholders keyed on a query's label: halting is undecidable, and a `ComputationalQuery` carries no program to examine. Treat a verdict as a stable token, never as evidence about a program.
   - Conclusion analysis resolving self-referential diagonal queries by ascending oracle tiers (`ConclusionAnalysis`).

---

## 2. Position in the TimeLord Formal Ecosystem

`grounded-hypercalculi` operates in synergy with adjacent formal repositories:

- **`hypermath`**: Primitive foundational algebraic kernel, quadrilateral filtration (syntax $\approx$, abstraction $\simeq$, substance $\cong$, semantics $\equiv$), and Lean 4 formal bridge.
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
