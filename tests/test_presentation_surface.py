"""The public first impression is a checked repository surface."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_presentation_surface_has_no_drift() -> None:
    path = ROOT / "scripts/check_presentation.py"
    spec = importlib.util.spec_from_file_location("check_presentation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = module.run()
    assert errors == [], f"Presentation gate failures: {errors}"


def test_public_boundary_catches_private_coordinates_without_naming_them() -> None:
    path = ROOT / "scripts" / "check_presentation.py"
    spec = importlib.util.spec_from_file_location("check_presentation_boundaries", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    drive_path = "E:" + "\\" + "private-workspace" + "\\" + "secret.txt"
    windows_user = "C:" + "\\" + "Users" + "\\" + "admin" + "\\" + "token"
    private_locator = "evaluator" + "-vault://artifact"
    private_key = "-----BEGIN " + "RSA " + "PRIVATE KEY-----"
    github_token = "ghp_" + "A" * 36
    pypi_token = "pypi-" + "A" * 36

    local_model = "private-model" + ".gguf"
    deployment_field = "model" + "_path"
    business_id = "PRO" + "SP-12345"

    assert "drive-qualified local path" in module.public_boundary_violations(drive_path)
    assert "local user or home path" in module.public_boundary_violations(windows_user)
    assert "synthetic private locator" in module.public_boundary_violations(private_locator)
    assert "private key block" in module.public_boundary_violations(private_key)
    assert "GitHub token shape" in module.public_boundary_violations(github_token)
    assert "PyPI token shape" in module.public_boundary_violations(pypi_token)
    assert "local model artifact filename" in module.public_boundary_violations(local_model)
    assert "private deployment field" in module.public_boundary_violations(deployment_field)
    assert "business operations identifier" in module.public_boundary_violations(business_id)


def test_lineage_claim_gate_rejects_causal_upgrades_without_blocking_boundaries() -> None:
    path = ROOT / "scripts" / "check_presentation.py"
    spec = importlib.util.spec_from_file_location("check_presentation_lineage", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    causal_lineage = "causal" + " lineage"
    causal_ancestors = "causal" + " ancestors"
    causal_process = "causal" + " process"
    causal_contribution = "causally" + " contributed"
    for phrase in (
        causal_lineage,
        causal_ancestors,
        causal_process,
        causal_contribution,
    ):
        assert module.lineage_causality_violations(phrase)

    assert module.lineage_causality_violations("recorded lineage") == []
    assert module.lineage_causality_violations(
        "The recorded edge does not establish causal influence."
    ) == []


def test_build_pages_assembles_cleanly(tmp_path: Path) -> None:
    path = ROOT / "scripts/build_pages.py"
    spec = importlib.util.spec_from_file_location("build_pages", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    out_dir = tmp_path / "site"
    module.build(out_dir)
    assert (out_dir / "index.html").is_file()
