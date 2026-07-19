"""DAS - repo-local license matrix checker shim.

Delegates to the canonical suite license-matrix validator while keeping the
repo-local documentation path as the default target.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys


def _load_checker():
    workspace = pathlib.Path(__file__).resolve().parents[3]
    path = workspace / "das-suite" / "tools" / "legal" / "check_license_matrix.py"
    spec = importlib.util.spec_from_file_location("das_suite_check_license_matrix", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical checker from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def evaluate(path: pathlib.Path | None = None):
    target = path or pathlib.Path(__file__).resolve().parents[2] / "docs" / "legal" / "LICENSE_MATRIX.md"
    return _load_checker().evaluate(target)


def main(argv: list[str]) -> int:
    path = pathlib.Path(argv[1]) if len(argv) > 1 else None
    result = evaluate(path)
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
