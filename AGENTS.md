# AGENTS.md

Working rules for automated contributors to Grounded Hypercalculi. Read this before editing anything.

## 0. Before you touch anything

High-risk couplings are enforced by CI and the conformance gate:

| If you are changing... | You must also... |
|---|---|
| the version, anywhere | bump all four: `pyproject.toml`, `src/grounded_hypercalculi/__init__.py`, `CITATION.cff`, `.zenodo.json`, and ensure a dated `## X.Y.Z - YYYY-MM-DD` heading exists in `CHANGELOG.md` |
| dependencies | keep `dependencies = []` in `pyproject.toml`; new tooling belongs only in optional extras (`test`, `release`, `dev`). Pure `python -S` stdlib smoke must always pass |
| boundary phrasing in `README.md` or specifications | verify against the presentation gate (`python scripts/check_presentation.py`) |
| release scripts | verify cross-platform reproducibility (`scripts/release_artifacts.py compare`) |

Before you propose a change:

```bash
python -m pytest -q
python scripts/check_presentation.py
PYTHONPATH=src python -S -c "import grounded_hypercalculi; print(grounded_hypercalculi.__version__)"
```

## 1. What this repository is

`grounded-hypercalculi` is the formal domain library and execution engine for extended mathematical, symbolic, and computational calculi. It standardizes six extended calculi:

1. **Language Calculus**: Formal syntax trees, alphabet specifications, context-free production rules, reflexive non-well-founded quotation graphs under Aczel's Anti-Foundation Axiom (AFA), and verified Metamath RPN proof validation.
2. **Meta-Calculus**: Symbolic dynamics of term rewrite systems, infinite trajectory spaces $\mathcal{S}^\omega$, shift operators $\sigma$, coalgebraic trajectory bisimulation, and Coxeter word-homotopy.
3. **Hyper-Calculus**: Automorphism groups $\mathrm{Aut}(G)$ over semantic state spaces, permutation groups, Lie derivation algebras with Leibniz product rule and Lie commutator brackets preserving semantic Noether invariants.
4. **Ordinal Calculus**: Exact transfinite arithmetic below $\omega^\omega$, left subtraction, discrete difference operators $\Delta F$, normal functions, ordinal derivatives $F'$ enumerating fixed points, and Veblen hierarchies.
5. **Real Analysis Calculus**: Continuum constructions grounded in hyperset ordinals, Dedekind cuts, Cauchy rational sequences, and Conway Surreal numbers supporting transfinite numbers and infinitesimals $\epsilon = 1/\omega$.
6. **Oracle Calculus**: Hypercomputation, trans-omega leapfrog computations ($O(\omega^\omega)$ in unit time), $\omega$-towers of halting oracles $\mathcal{H}_\alpha$, hyperoracles, and contractive conclusion analysis.

### 1.1 The TimeLord Formal Ecosystem

`grounded-hypercalculi` operates in close synergy with adjacent repositories:

- `hypermath`: Primitive foundational algebraic kernel, quadrilateral filtration (syntax $\sim\sim$, abstraction $\sim=$, substance $=~$, semantics $==$), and Lean 4 formal bridge.
- `ordinatics`: Ordinal-based metalanguage and stratified truth stage evaluation constructed up from `hypermath`.
- `grounded-hyperset-theory`: Aczel's Anti-Foundation Axiom (AFA), Accessible Pointed Graphs (APGs), circular non-well-founded sets, and bisimulation quotienting.
- `grounded-hypercalculi`: The execution engine and domain calculus layer.
- `verifier`: The verification domain language (`VSTD`), two-axis ladder, refutation certificates, and presentation standard.

## 2. Prime directive

> Changes that strengthen a claim without stronger evidence are non-conforming.

Specifically, never:
- soften an uncomputable or looping result into an unjustified pass;
- introduce required third-party runtime dependencies on base import paths;
- bypass the isolated wheel smoke check;
- weaken assertions or remove tests to make a suite pass.

## 3. Environment and commands

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/check_presentation.py
python -m compileall -q src scripts
```

Stdlib-purity smoke (mirroring the `stdlib-smoke` CI job):

```bash
PYTHONPATH=src python -S -c "import grounded_hypercalculi; print(grounded_hypercalculi.__version__)"
```

Release artifact verification:

```bash
python scripts/release_artifacts.py build --ref HEAD --release 0.1.0 --output-dir dist
python scripts/release_artifacts.py verify dist/grounded-hypercalculi-0.1.0.manifest.json
python -m twine check dist/*.whl dist/*.tar.gz
python scripts/check_release_boundary.py dist/*.zip dist/*.whl dist/*.tar.gz
python scripts/check_installed_wheel.py --wheel-dir dist
```

Cross-platform release artifact comparison:

```bash
python scripts/release_artifacts.py compare PATH_TO_LINUX_ARTIFACTS PATH_TO_WINDOWS_ARTIFACTS
```

## 4. Invariants that must not be broken

1. **Zero required runtime dependencies**: `dependencies = []` is strictly enforced. The entire library runs on pure standard library Python 3.10+.
2. **LF line endings**: `.gitattributes` forces `eol=lf`. Build reproducibility fails if line endings diverge across platforms.
3. **Version parity**: `pyproject.toml`, `src/grounded_hypercalculi/__init__.py`, `CITATION.cff`, `.zenodo.json`, and `CHANGELOG.md` must agree exactly.
4. **Reproducible multi-platform builds**: Linux and Windows release builds generated by `scripts/release_artifacts.py` must be byte-identical.
5. **Private/public boundary**: Never commit local filesystem paths, drive roots, personal home directory references, secret tokens, private key blocks, or personal email addresses.

## 5. Conventions

- Python `>=3.10`.
- All modules open with `from __future__ import annotations`.
- Type annotations across all public functions and classes.
- Immutable/frozen dataclasses where applicable.
- Full docstrings describing mathematical and operational semantics.

## 6. Safety

Never commit private keys, tokens, or credential material. All test anchors are mock/emulator only.
Report vulnerabilities through private repository channels described in [`SECURITY.md`](SECURITY.md).
