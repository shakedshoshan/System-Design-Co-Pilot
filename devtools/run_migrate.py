"""Run Alembic with this repo's `.venv` Python.

Use this instead of `poetry run alembic` when another environment is active (e.g. Conda)
and the wrong `alembic` / interpreter gets used.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if sys.platform == "win32":
        py = root / ".venv" / "Scripts" / "python.exe"
    else:
        py = root / ".venv" / "bin" / "python"

    if not py.is_file():
        print("No .venv Python found. From the repo root run: poetry install", file=sys.stderr)
        raise SystemExit(1)

    ini = root / "apps" / "api" / "alembic.ini"
    if not ini.is_file():
        print(f"Missing Alembic config: {ini}", file=sys.stderr)
        raise SystemExit(1)

    api_dir = str(root / "apps" / "api")
    extra = list(sys.argv[1:])
    if not extra:
        print(
            "Usage: poetry run migrate <alembic-args>\n"
            "  Example: poetry run migrate upgrade head\n"
            "  Example: poetry run migrate current",
            file=sys.stderr,
        )
        raise SystemExit(2)

    env = os.environ.copy()
    # Prepend so `import app` in env.py never picks another repo's `app` package.
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{api_dir}{os.pathsep}{prev}" if prev else api_dir

    cmd = [str(py), "-m", "alembic", "-c", str(ini), *extra]
    raise SystemExit(subprocess.call(cmd, cwd=str(root), env=env))
