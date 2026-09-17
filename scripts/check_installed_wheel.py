"""Check imports and representative calls from a clean, non-editable wheel install."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def run(command: list[str], *, cwd: Path, timeout: int = 180) -> None:
    print(
        f"START installed-wheel check: {Path(command[0]).name} {' '.join(command[1:3])}",
        flush=True,
    )
    subprocess.run(command, cwd=cwd, check=True, timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()

    wheels = sorted(args.wheel_dir.resolve().glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected exactly one subject wheel in {args.wheel_dir}, found {len(wheels)}")

    wheel = str(wheels[0])

    with tempfile.TemporaryDirectory(prefix="installed-wheel-ghc-") as temporary:
        root = Path(temporary)
        environment = root / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

        run([str(python), "-m", "pip", "install", "--no-deps", wheel], cwd=root)
        run([str(python), "-m", "pip", "check"], cwd=root)

        probe = (
            "import importlib, pathlib, sys; "
            "module = importlib.import_module('grounded_hypercalculi'); "
            "assert pathlib.Path(module.__file__).resolve().is_relative_to("
            "pathlib.Path(sys.prefix).resolve()), 'import did not come from the isolated environment'; "
            "deg0 = module.TuringDegree(0); "
            "assert deg0.is_computable; "
            "deg1 = deg0.jump(); "
            "assert deg1.rank == 1; "
            "tower = module.OracleTower(); "
            "q = module.ComputationalQuery('test', 1); "
            "assert tower.decide_halting(q, 1) in (module.HaltingStatus.HALTS, module.HaltingStatus.LOOPS); "
            "leap = module.LeapfrogComputation(1); "
            "assert leap.leapfrog_step(0, lambda s, i: s + 1, 10) == 10; "
            "ord1 = module.BoundedOrdinal.from_int(1); "
            "assert (ord1 + module.OMEGA) == module.OMEGA; "
            "rat = module.GroundedRational(1, 2); "
            "assert rat.to_float() == 0.5; "
            "print('PASS: installed grounded_hypercalculi wheel is importable and usable')"
        )
        run([str(python), "-I", "-c", probe], cwd=root, timeout=30)


if __name__ == "__main__":
    main()
