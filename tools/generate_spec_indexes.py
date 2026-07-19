#!/usr/bin/env python3
"""Generate complete deterministic indexes from SPECIFICATION.md headings."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^## (?:([0-9]+)\. )?(.+)$")
CLAUSE = re.compile(r"^### ([0-9]+\.[0-9]+(?:\.[0-9]+)?) (.+)$")


def slug(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", value).strip("-")


def payloads() -> tuple[dict, dict]:
    text = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")
    chapters = []
    clauses = []
    for line in text.splitlines():
        chapter_match = CHAPTER.match(line)
        if chapter_match:
            number, title = chapter_match.groups()
            if number is not None:
                chapters.append({
                    "id": f"ch-{number}", "title": title,
                    "file": f"SPECIFICATION.md#{number}-{slug(title)}", "roles": ["all"],
                })
            continue
        clause_match = CLAUSE.match(line)
        if clause_match:
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
    common = {"$schema": "https://das-standard.dev/schemas/{name}", "schemaVersion": "1.0.0", "standardVersion": "1.4.0"}
    chapter_payload = {**common, "$schema": common["$schema"].format(name="chapter_index.schema.json"), "chapters": chapters, "appendices": appendices}
    clause_payload = {**common, "$schema": common["$schema"].format(name="clause_index.schema.json"), "clauses": clauses}
    return chapter_payload, clause_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = zip((ROOT / "chapter_index.json", ROOT / "clause_index.json"), payloads())
    stale = []
    for path, payload in expected:
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                stale.append(path.name)
        else:
            path.write_text(rendered, encoding="utf-8")
    if stale:
        raise SystemExit("stale generated indexes: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
