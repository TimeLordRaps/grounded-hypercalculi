# Governance

## Current Phase

`grounded-hypercalculi` is founder-maintained formal mathematics and computational logic work.
Tyler Roost (TimeLordRaps) is the primary maintainer and release editor.

## Releases and Lifecycle States

- **Implemented Base**: A calculus model has executable reference implementations, typed abstractions, and passing test suites.
- **Experimental**: The vocabulary and bounded representations exist, but formal bridge verification is ongoing.
- **Challenged**: Mathematical evidence or counterexample demonstrates an edge case in current implementation.
- **Superseded**: An additive revision replaces an earlier formulation while preserving historical version records.

Repository releases use semantic versioning (`vMAJOR.MINOR.PATCH`).
Released artifacts published to PyPI and GitHub Releases are immutable.

## Decision Rights

TimeLordRaps maintains project direction, release authority, and architectural stewardship across
the TimeLord formal ecosystem (`hypermath`, `ordinatics`, `grounded-hyperset-theory`, `grounded-hypercalculi`, `verifier`).
All production distributions publish via OIDC Trusted Publishing under automated GitHub Actions workflows.
