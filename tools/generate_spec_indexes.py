#!/usr/bin/env python3
"""Generate complete deterministic indexes from SPECIFICATION.md headings."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Resolve the adjacent helper explicitly; these maintenance scripts support -I.
import importlib.util
_io_spec = importlib.util.spec_from_file_location("das_standard_io", Path(__file__).with_name("standard_io.py"))
standard_io = importlib.util.module_from_spec(_io_spec)
_io_spec.loader.exec_module(standard_io)

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^## (?:([0-9]+)\. )?(.+)$")
CLAUSE = re.compile(r"^#{3,6} ([0-9]+\.[0-9]+(?:\.[0-9]+)*) (.+)$")


def slug(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return value.replace(" ", "-")


def payloads() -> tuple[dict, dict]:
    text = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")
    chapters = []
    clauses = []
    fence = None
    in_chapter = False
    for line in text.splitlines():
        fenced = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fenced:
            marker = fenced.group(1)
            if fence is None: fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence): fence = None
            continue
        if fence is not None:
            continue
        if line == "#### Edition acceptance obligations (generated)":
            break
        chapter_match = CHAPTER.match(line)
        if chapter_match:
            number, title = chapter_match.groups()
            in_chapter = number is not None
            if number is not None:
                chapters.append({
                    "id": f"ch-{number}", "title": title,
                    "file": f"SPECIFICATION.md#{number}-{slug(title)}", "roles": ["all"],
                })
            continue
        clause_match = CLAUSE.match(line)
        if clause_match and in_chapter:
            number, title = clause_match.groups()
            clauses.append({
                "id": f"cl-{number}", "chapter": f"ch-{number.split('.', 1)[0]}",
                "title": title, "file": f"SPECIFICATION.md#{number.replace('.', '')}-{slug(title)}",
                "keywords": [], "gateLabels": [],
            })
    appendices = []
    for path in sorted((ROOT / "appendices").glob("appendix-*.md")):
        match = re.match(r"appendix-([a-z]+)-(.+)\.md$", path.name)
        if match:
            appendix_id, name = match.groups()
            appendices.append({
                "id": f"appendix-{appendix_id}", "title": name.replace("-", " ").title(),
                "file": path.relative_to(ROOT).as_posix(),
            })
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    identifier = r'(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)'
    pattern = (r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)'
               + r'(?:-' + identifier + r'(?:\.' + identifier + r')*)?'
               + r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?')
    if not re.fullmatch(pattern, version):
        raise ValueError("invalid authoritative Standard VERSION")
    common = {"schemaVersion": "1.0.0", "standardVersion": version}
    chapter_payload = {**common, "$schema": "./chapter_index.schema.json", "chapters": chapters, "appendices": appendices}
    clause_payload = {**common, "$schema": "./clause_index.schema.json", "clauses": clauses}
    return chapter_payload, clause_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = list(zip((ROOT / "chapter_index.json", ROOT / "clause_index.json"), payloads()))
    if not args.check:
        standard_io.preflight_outputs([path for path, _ in expected])
    stale = []
    for path, payload in expected:
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                stale.append(path.name)
        else:
            standard_io.write_text(path, rendered)
    if stale:
        raise SystemExit("stale generated indexes: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
