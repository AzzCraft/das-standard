"""Strict JSON parsing and bounded, non-destructive generated-file writes."""
from __future__ import annotations

import json
import math
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import stat
import tempfile


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def loads(raw):
    # These maintenance contracts use finite binary64 decimals. JSON permits
    # larger exponents, but silently converting them to infinity changes data.
    def finite_float(token):
        value = float(token)
        mantissa = token.lower().split('e', 1)[0]
        if not math.isfinite(value) or (value == 0 and any(c in '123456789' for c in mantissa)):
            raise ValueError("JSON decimal exceeds the finite binary64 range")
        try:
            if Decimal(str(value)) != Decimal(token):
                raise ValueError("JSON decimal loses value in binary64 round-trip")
        except InvalidOperation as exc:
            raise ValueError("JSON decimal is outside the supported numeric domain") from exc
        return value
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_constant,
                      parse_float=finite_float)


def preflight_outputs(paths):
    for path in paths:
        path = Path(path).absolute()
        for parent in path.parents:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f"unsafe generated output parent: {parent}")
        if path.is_symlink():
            raise ValueError(f"linked generated output: {path}")
        if path.exists():
            info = path.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError(f"non-private regular generated output: {path}")


def write_text(path, text):
    path = Path(path)
    preflight_outputs([path])
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        preflight_outputs([path])
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_content_inventory(root, manifest):
    """Check the content profile, not existence in the larger source checkout."""
    import posixpath
    import re
    from urllib.parse import unquote, urlsplit
    members = set(manifest['requiredArtifacts'])
    required = {'VERSION', 'SPECIFICATION.md', 'standard_manifest.json', 'scripts/verify', 'verify_registry.json', 'tools/validate_release_contract.py', 'tools/standard_io.py', 'requirements-verify.txt', '.github/workflows/verify.yml'}
    missing = required - members
    if missing:
        raise ValueError(f'required repo-canonical content omitted: {sorted(missing)}')
    for name in members:
        if not name.endswith('.md'):
            continue
        text = (root / name).read_text(encoding='utf-8')
        text = re.sub(r'(?ms)^```[^\n]*\n.*?^```\s*$', '', text)
        for target in re.findall(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"\n]*")?\)', text):
            uri = urlsplit(target.strip('<>'))
            if uri.scheme or uri.netloc or not uri.path:
                continue
            member = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(uri.path)))
            if member not in members and not any(m.startswith(member.rstrip('/') + '/') for m in members):
                raise ValueError(f'content navigation omits {name} -> {member}')
