"""Actual shipped entrypoints must reject corrupt inputs in every Python mode."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle(tmp_path):
    destination = tmp_path / 'standard'
    manifest = json.loads((ROOT / 'standard_manifest.json').read_text())
    for relative in sorted(set(manifest['requiredArtifacts']) | {'release_snapshot_manifest.json'}):
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


def change_json(bundle, relative, mutate):
    path = bundle / relative
    value = json.loads(path.read_text())
    mutate(value)
    path.write_text(json.dumps(value, indent=2) + '\n')


def run_tool(bundle, gate, optimized):
    arguments = [sys.executable, '-B']
    if optimized:
        arguments.append('-O')
    return subprocess.run([*arguments, 'tools/validate_release_contract.py', '--gate', gate],
                          cwd=bundle, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('fault,gate', [
    ('snapshot_hash', 'release-snapshot'),
    ('id_version', 'bundle-files'),
    ('missing_template_metadata', 'bundle-files'),
    ('missing_enum_definition', 'schemas'),
    ('altered_current_fixture', 'compat-release'),
])
def test_corrupt_bundle_rejected_without_debug_assertions(bundle, fault, gate, optimized):
    if fault == 'snapshot_hash':
        change_json(bundle, 'release_snapshot_manifest.json',
                    lambda value: value['artifacts'][0].update(sha256='0' * 64))
    elif fault == 'id_version':
        change_json(bundle, 'ids/standard_ids.json', lambda value: value.update(standardVersion='0.0.0'))
    elif fault == 'missing_template_metadata':
        catalog = json.loads((bundle / 'template_catalog.json').read_text())
        path = bundle / next(item['artifactPath'] for item in catalog['templates'] if item['docType'] == 'master_doc')
        text = path.read_text()
        assert '- **Doc ID**:' in text
        path.write_text(text.replace('- **Doc ID**:', '- **Omitted Doc ID**:'))
    elif fault == 'missing_enum_definition':
        change_json(bundle, 'standard_manifest.json', lambda value: value['gateCadenceDefinitions'].pop('pre_release'))
    else:
        version = (bundle / 'VERSION').read_text().strip()
        change_json(bundle, f'tests/compat/v{version}/standard_manifest.json',
                    lambda value: value.update(standardId='wrong-standard'))
    result = run_tool(bundle, gate, optimized)
    assert result.returncode != 0, result.stdout + result.stderr


@pytest.mark.parametrize('optimized', [False, True])
def test_valid_bundle_remains_readable(bundle, optimized):
    result = run_tool(bundle, 'all', optimized)
    assert result.returncode == 0, result.stdout + result.stderr


def run_entry(bundle, **environment):
    env = {**os.environ, 'PYTHON': sys.executable, 'PYTHONDONTWRITEBYTECODE': '1', **environment}
    return subprocess.run(['bash', 'scripts/verify', '--gate', 'compat-release'], cwd=bundle,
                          env=env, capture_output=True, text=True, timeout=45)


def test_compatibility_window_cannot_be_bypassed_by_optimization(bundle):
    change_json(bundle, 'release/release_report.json',
                lambda value: value['compatibilityWindow'].update(minReadableVersion='0.0.0'))
    result = run_entry(bundle, PYTHONOPTIMIZE='1')
    assert result.returncode != 0, result.stdout + result.stderr
    assert 'verify: PASS' not in result.stdout


def test_entry_isolates_python_environment_and_still_verifies(bundle, tmp_path):
    attacker = tmp_path / 'untrusted-imports'; attacker.mkdir()
    marker = tmp_path / 'import-executed'
    (attacker / 'sitecustomize.py').write_text(
        'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n')
    result = run_entry(bundle, PYTHONPATH=str(attacker), PYTHONUSERBASE=str(attacker))
    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists(), 'untrusted startup code executed before validation'
    assert result.stdout.count('verify: PASS') == 1


def test_failed_child_never_emits_final_success(bundle):
    (bundle / 'tools/generate_spec_indexes.py').write_text('raise SystemExit(73)\n')
    result = run_entry(bundle)
    assert result.returncode == 73, result.stdout + result.stderr
    assert 'verify: PASS' not in result.stdout


@pytest.mark.parametrize('fault', ['valid', 'wrong-type', 'missing-example', 'missing-schema', 'invalid-schema'])
def test_remediation_uses_actual_schema_and_required_inputs(tmp_path, monkeypatch, fault):
    from tests import test_remediation_specs as remediation
    from jsonschema import SchemaError, ValidationError
    pairs = ['suite_version_closure', 'tooling_lock', 'local_extension_manifest']
    for stem in pairs:
        (tmp_path / (stem + '.example.json')).write_text('{"id": 1}')
        (tmp_path / (stem + '.schema.json')).write_text(json.dumps({
            'type': 'object', 'required': ['id'], 'properties': {'id': {'type': 'integer'}}}))
    first = pairs[0]
    if fault == 'wrong-type': (tmp_path / (first + '.example.json')).write_text('{"id": "wrong"}')
    elif fault == 'missing-example': (tmp_path / (first + '.example.json')).unlink()
    elif fault == 'missing-schema': (tmp_path / (first + '.schema.json')).unlink()
    elif fault == 'invalid-schema': (tmp_path / (first + '.schema.json')).write_text('{"type": 7}')
    monkeypatch.setattr(remediation, 'ROOT', tmp_path)
    case = remediation.StandardRemediationSpecTests()
    if fault == 'valid':
        case.test_v9_01_example_validates_against_schema()
    else:
        with pytest.raises((AssertionError, SchemaError, ValidationError)):
            case.test_v9_01_example_validates_against_schema()


def test_bundle_fixture_copies_declared_current_bytes_only(tmp_path, monkeypatch):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'standard_manifest.json').write_text('{"requiredArtifacts": ["tool"]}')
    (source / 'release_snapshot_manifest.json').write_text('{}')
    (source / 'tool').write_bytes(b'current dirty bytes'); (source / 'tool').chmod(0o755)
    (source / '.venv').mkdir(); (source / '.venv/unrelated').write_text('do not copy')
    monkeypatch.setattr(sys.modules[__name__], 'ROOT', source)
    destination = bundle.__wrapped__(tmp_path / 'result')
    assert (destination / 'tool').read_bytes() == b'current dirty bytes'
    assert (destination / 'tool').stat().st_mode & 0o777 == 0o755
    assert not (destination / '.venv').exists()
