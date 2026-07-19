"""DAS - repo-local redaction checker shim.

Delegates to the canonical suite redaction validator while defaulting the
workspace root to the multi-repo checkout.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys


def _load_checker():
    workspace = pathlib.Path(__file__).resolve().parents[3]
    path = workspace / "das-suite" / "tools" / "security" / "check_redaction.py"
    spec = importlib.util.spec_from_file_location("das_suite_check_redaction", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical checker from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def evaluate(path: pathlib.Path, workspace_root: pathlib.Path | None = None) -> dict[str, object]:
    root = workspace_root or pathlib.Path(__file__).resolve().parents[3]
    target = pathlib.Path(path)
    return _load_checker().evaluate(root, target)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write("usage: check_redaction <packet.json> [workspace_root]\n")
        return 2
    path = pathlib.Path(argv[1])
    workspace_root = pathlib.Path(argv[2]) if len(argv) > 2 else None
    payload = evaluate(path, workspace_root)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
