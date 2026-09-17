# Contributing to Grounded Hypercalculi

Contributions are welcome when they make formal calculi models more precise,
computationally sound, mathematically grounded, or easier to integrate without
introducing required runtime dependencies.

## Required for a normative change

- Identify the affected calculus domain (Language, Meta, Hyper, Ordinal, Real, or Oracle);
- State compatibility effects and mathematical invariants preserved;
- Include a falsification condition;
- Maintain zero required third-party runtime dependencies;
- Add tests that fail before the change and pass after it;
- Ensure 100% passing tests (`pytest -q`) and presentation gate passage.

Unless explicitly stated otherwise, a contribution intentionally submitted for
inclusion in this repository is provided under the Apache License 2.0.

## Commits

Commits in this repository are expected to be GPG-signed (`git commit -S`).
Automated contributors must not bypass signing. A commit signature binds bytes
to a signing key.

## Feedback

Use GitHub Issues for mathematical counterexamples, edge cases, and bug reports.
Send security details only through the private route documented in [`SECURITY.md`](SECURITY.md).
