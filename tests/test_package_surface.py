"""Tests for the packaging claims: ``dependencies = []`` and the export surface.

AGENTS.md names "never introduce required third-party runtime dependencies on
base import paths" as a prime directive, and ``pyproject.toml`` declares
``dependencies = []``. Nothing tested either. A stray ``import numpy`` at the top
of ``real_calculus.py`` would have passed every existing test and every gate,
because the development environment has the package installed -- and would then
fail for the first user who installed this one on its own terms.

That is the specific failure this module exists to catch, so the check is made
the way a user would experience it: import in a subprocess started with ``-S``,
which disables ``site`` and therefore removes site-packages from the path. Under
``-S`` a third-party import raises ``ModuleNotFoundError``, and the test fails
with the offending module named.

Version parity is deliberately not retested here; ``scripts/check_presentation.py``
already gates it across all five declaring files, and a second copy would drift.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import grounded_hypercalculi as package

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

SUBMODULES = [
    "hyper_calculus",
    "language_calculus",
    "meta_calculus",
    "oracle_calculus",
    "ordinal_calculus",
    "real_calculus",
]


def _run_isolated(body: str) -> subprocess.CompletedProcess[str]:
    """Run ``body`` in a subprocess with site-packages unavailable."""
    code = f"import sys; sys.path.insert(0, {str(SRC)!r})\n{body}"
    return subprocess.run(
        [sys.executable, "-S", "-c", code], capture_output=True, text=True, cwd=str(ROOT)
    )


def test_site_packages_really_are_unavailable_under_dash_s() -> None:
    """The control for every other test in this file.

    If ``-S`` did not actually hide third-party packages, each isolation test
    below would pass vacuously. This asserts the isolation is real, using a
    package that is installed in the development environment and must not be
    importable under ``-S``.
    """
    proc = _run_isolated("import sympy")
    assert proc.returncode != 0
    assert "No module named 'sympy'" in proc.stderr


def test_the_package_imports_with_no_third_party_packages_available() -> None:
    proc = _run_isolated("import grounded_hypercalculi as g; print(g.__version__)")
    assert proc.returncode == 0, f"importing the package needs something it does not declare:\n{proc.stderr}"
    assert proc.stdout.strip() == package.__version__


@pytest.mark.parametrize("name", SUBMODULES)
def test_each_submodule_imports_on_its_own_with_nothing_installed(name: str) -> None:
    """Checked per module, not only through ``__init__``.

    A module that ``__init__`` happens not to reach would otherwise be able to
    acquire a dependency unnoticed.
    """
    proc = _run_isolated(f"import grounded_hypercalculi.{name}")
    assert proc.returncode == 0, f"{name} needs an undeclared dependency:\n{proc.stderr}"


def test_importing_the_package_loads_no_third_party_module() -> None:
    """The precise form: diff ``sys.modules`` and name anything foreign.

    ``-S`` proves nothing foreign is *required*. This proves nothing foreign is
    *loaded*, which also catches an optional import that runs at module scope
    inside a ``try``.
    """
    body = (
        "before = set(sys.modules)\n"
        "import grounded_hypercalculi\n"
        "std = set(sys.stdlib_module_names)\n"
        "foreign = sorted(\n"
        "    m for m in set(sys.modules) - before\n"
        "    if m.split('.')[0] not in std and not m.startswith('grounded_hypercalculi')\n"
        ")\n"
        "print(','.join(foreign))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(SRC)!r})\n{body}"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "", f"importing the package loaded: {proc.stdout.strip()}"


def test_pyproject_still_declares_no_runtime_dependencies() -> None:
    """The tests above are only meaningful while this is what is promised."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "\ndependencies = []\n" in text


# --------------------------------------------------------------------------
# the export surface
# --------------------------------------------------------------------------


def test_every_exported_name_resolves() -> None:
    missing = [name for name in package.__all__ if not hasattr(package, name)]
    assert missing == []


def test_the_export_list_has_no_duplicates() -> None:
    duplicates = sorted({n for n in package.__all__ if package.__all__.count(n) > 1})
    assert duplicates == []


def test_a_star_import_yields_exactly_the_export_list() -> None:
    namespace: dict[str, object] = {}
    exec("from grounded_hypercalculi import *", namespace)  # noqa: S102
    starred = sorted(n for n in namespace if not n.startswith("__"))
    assert starred == sorted(package.__all__)


def test_every_name_the_package_imports_is_also_exported() -> None:
    """Closes a gap that this file's own negative control exposed.

    Deleting a name from ``__all__`` broke nothing: ``__init__`` still imports
    it, so ``from grounded_hypercalculi import ThatName``
    keeps working and every other test here kept passing. But the name silently disappears from ``import *`` and from
    any tool that reads ``__all__``, which is a real regression in the published
    surface.

    The invariant that catches it: every public attribute the package binds at
    module scope is either a submodule, ``annotations`` (leaked into the
    namespace by ``from __future__ import annotations``), or a name in
    ``__all__``.
    """
    import types

    exported = set(package.__all__)
    leaked = sorted(
        name
        for name, value in vars(package).items()
        if not name.startswith("_")
        and name not in exported
        and not isinstance(value, types.ModuleType)
        and name != "annotations"
    )
    assert leaked == []


def test_every_public_class_and_function_in_every_submodule_is_re_exported() -> None:
    """Measured, and currently true for all six modules.

    This is the test that keeps it true. A new public class added to a submodule
    and forgotten in ``__all__`` is reachable by its module path and invisible
    from the package, which is how an export list quietly stops describing the
    package it belongs to.
    """
    import importlib
    import inspect

    exported = set(package.__all__)
    unexported: dict[str, list[str]] = {}
    for name in SUBMODULES:
        module = importlib.import_module(f"grounded_hypercalculi.{name}")
        public = {
            attribute
            for attribute, value in vars(module).items()
            if not attribute.startswith("_")
            and getattr(value, "__module__", None) == module.__name__
            and (inspect.isclass(value) or inspect.isfunction(value))
        }
        if public - exported:
            unexported[name] = sorted(public - exported)
    assert unexported == {}
