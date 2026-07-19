"""DAS - repo-local commercial Go/No-Go gate shim.

Delegates to the canonical suite commercial gate while preserving a repo-local
entrypoint for the implementation matrix.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def _load_checker():
    workspace = pathlib.Path(__file__).resolve().parents[3]
    path = workspace / "das-suite" / "tools" / "release" / "check_commercial_gonogo.py"
    spec = importlib.util.spec_from_file_location("das_suite_check_commercial_gonogo", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical commercial gate from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_IMPL = _load_checker()


def evaluate(root: str | pathlib.Path = "."):
    return _IMPL.evaluate(pathlib.Path(root))


def main(argv: list[str]) -> int:
    return _IMPL.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
