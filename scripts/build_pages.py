#!/usr/bin/env python3
"""Assemble documentation into the GitHub Pages artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PagesBuildError(RuntimeError):
    pass


def build(output: Path) -> Path:
    """Build into a new or empty directory and return the output path."""
    output = output.resolve()
    if output == ROOT:
        raise PagesBuildError("Pages output cannot be the repository root")
    if output.exists() and any(output.iterdir()):
        raise PagesBuildError(f"refusing to merge into non-empty Pages output: {output}")
    if output.exists():
        output.rmdir()

    if not DOCS.is_dir():
        raise PagesBuildError(f"documentation source directory missing: {DOCS}")

    shutil.copytree(DOCS, output)
    if not (output / "index.html").is_file():
        raise PagesBuildError("built pages artifact is missing index.html")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = build(args.output)
        print(f"[PAGES OK] documentation site assembled into {out}")
    except PagesBuildError as exc:
        print(f"[PAGES FAIL] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
