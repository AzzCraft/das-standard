from __future__ import annotations

import json
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import pytest

from tests._root_contract import repository_root_for_test_file


ROOT = repository_root_for_test_file(__file__)


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_current_compat_fixture_is_the_canonical_manifest_copy() -> None:
    manifest = _load("standard_manifest.json")
    version = (ROOT / 'VERSION').read_text().strip()
    fixture = _load(f"tests/compat/v{version}/standard_manifest.json")
    assert fixture == manifest


def test_release_contract_validator_checks_governed_template_surface() -> None:
    proc = subprocess.run(
        [sys.executable, "-I", "-B", "tools/validate_release_contract.py", "--gate", "bundle-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_verify_registry_matches_the_four_implemented_gates() -> None:
    registry = _load("verify_registry.json")
    default = registry["defaultVerifyCommand"]
    gates = {
        item["command"].split()[-1]
        for item in registry["gates"]
        if item["command"].startswith(default + " --gate ")
    }
    assert gates == {"bundle-files", "schemas", "release-snapshot", "compat-release"}


def _content_generator(root, monkeypatch):
    spec = importlib.util.spec_from_file_location('content_generator', ROOT / 'tools/generate_content_snapshot.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    monkeypatch.setattr(generator, 'ROOT', root)
    monkeypatch.setattr(generator, 'OUTPUT', root / 'release_snapshot_manifest.json')
    root.mkdir()
    (root / 'VERSION').write_bytes(b'1.5.0-beta.1\n')
    (root / 'SPECIFICATION.md').write_bytes('规则 MUST 保留。\n'.encode())
    manifest = dict(requiredArtifacts=['VERSION', 'SPECIFICATION.md', 'standard_manifest.json',
                                      'release_snapshot_manifest.json'], releasedAt='2026-10-06')
    (root / 'standard_manifest.json').write_text(json.dumps(manifest))
    rendered = json.dumps(generator.build(), indent=2, ensure_ascii=False) + '\n'
    generator.OUTPUT.write_text(rendered)
    return generator, rendered


def test_content_zip_rebuilds_exact_members_without_source_tree_or_mtime_identity(tmp_path, monkeypatch):
    import os
    import zipfile
    generator, rendered = _content_generator(tmp_path / 'source', monkeypatch)
    first, second = tmp_path / 'first.zip', tmp_path / 'second.zip'
    generator.archive(first, rendered)
    assert first.stat().st_mode & 0o777 == 0o600
    os.utime(generator.ROOT / 'SPECIFICATION.md', (1000000000, 1000000000))
    generator.archive(second, rendered)
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as zipped:
        names = sorted(row['path'] for row in json.loads(rendered)['artifacts'])
        names = sorted([*names, 'release_snapshot_manifest.json'])
        assert zipped.namelist() == names
        for name in names:
            assert zipped.read(name) == (generator.ROOT / name).read_bytes()
            assert zipped.getinfo(name).date_time == (1980, 1, 1, 0, 0, 0)
    with pytest.raises(FileExistsError):
        generator.archive(first, rendered)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize('fault', ['stale', 'changed-member', 'symlink', 'source-output', 'oversized'])
def test_content_zip_refuses_invalid_input_without_publishing_output(tmp_path, monkeypatch, fault):
    generator, rendered = _content_generator(tmp_path / 'source', monkeypatch)
    output = tmp_path / 'content.zip'
    if fault == 'stale': generator.OUTPUT.write_text(rendered + '\n')
    elif fault == 'changed-member': (generator.ROOT / 'SPECIFICATION.md').write_bytes(b'changed')
    elif fault == 'symlink':
        body = generator.ROOT / 'SPECIFICATION.md'
        outside = tmp_path / 'outside'; outside.write_bytes(body.read_bytes())
        body.unlink(); body.symlink_to(outside)
    elif fault == 'source-output': output = generator.ROOT / 'content.zip'
    else:
        body = generator.ROOT / 'SPECIFICATION.md'; body.write_bytes(b'x' * (4 * 1024 * 1024 + 1))
        rendered = json.dumps(generator.build(), indent=2, ensure_ascii=False) + '\n'
        generator.OUTPUT.write_text(rendered)
    with pytest.raises(SystemExit): generator.archive(output, rendered)
    assert not output.exists()


@pytest.mark.parametrize('nested',[False,True])
def test_content_zip_refuses_output_parent_alias(tmp_path,monkeypatch,nested):
    generator,rendered=_content_generator(tmp_path/'source',monkeypatch)
    real=tmp_path/'real';real.mkdir();(real/'nested').mkdir()
    alias=tmp_path/'alias';alias.symlink_to(real,target_is_directory=True)
    output=(alias/'nested' if nested else alias)/'content.zip'
    with pytest.raises(SystemExit):generator.archive(output,rendered)
    assert not output.exists()


@pytest.mark.parametrize('replacement',['symlink','directory'])
def test_content_zip_refuses_output_parent_replacement_during_packaging(tmp_path,monkeypatch,replacement):
    import zipfile
    generator,rendered=_content_generator(tmp_path/'source',monkeypatch)
    parent=tmp_path/'output';parent.mkdir();retained=tmp_path/'retained'
    original=zipfile.ZipFile.writestr;changed=[]
    def replace_parent(self,*args,**kwargs):
        if not changed:
            parent.rename(retained)
            if replacement=='symlink':parent.symlink_to(generator.ROOT,target_is_directory=True)
            else:parent.mkdir()
            changed.append(True)
        return original(self,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,'writestr',replace_parent)
    with pytest.raises(SystemExit):generator.archive(parent/'content.zip',rendered)
    assert changed==[True]
    assert not (parent/'content.zip').exists() and not (retained/'content.zip').exists()
    assert not (generator.ROOT/'content.zip').exists()


@pytest.mark.parametrize('fault', ['linked-body','duplicate-member','undeclared-member','unsafe-path'])
def test_standard_content_snapshot_rejects_noncanonical_or_external_member_closure(tmp_path, monkeypatch, fault):
    spec=importlib.util.spec_from_file_location('snapshot_validator',ROOT/'tools/validate_release_contract.py')
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    snapshot=_load('release_snapshot_manifest.json');manifest=_load('standard_manifest.json')
    for row in snapshot['artifacts']:
        target=tmp_path/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row['path'],target)
    shutil.copyfile(ROOT/'release_snapshot_manifest.json',tmp_path/'release_snapshot_manifest.json')
    monkeypatch.setattr(validator,'ROOT',tmp_path)
    validator.check_snapshot_registry(manifest)
    if fault=='linked-body':
        body=tmp_path/'SPECIFICATION.md';outside=tmp_path.parent/(tmp_path.name+'-outside-body')
        body.rename(outside);body.symlink_to(outside)
    elif fault=='duplicate-member':snapshot['artifacts'].append(dict(snapshot['artifacts'][0]))
    elif fault=='undeclared-member':
        path=tmp_path/'TEST-undeclared.txt';path.write_bytes(b'TEST undeclared member')
        snapshot['artifacts'].append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),artifactClass='supporting',required=True))
    else:
        row=next(row for row in snapshot['artifacts'] if row['path']=='SPECIFICATION.md')
        absolute=str(tmp_path/'SPECIFICATION.md');row['path']=absolute
        manifest['requiredArtifacts']=[absolute if name=='SPECIFICATION.md' else name for name in manifest['requiredArtifacts']]
    snapshot['artifacts'].sort(key=lambda row:row['path'])
    joined='\n'.join(f"{row['path']}:{row['sha256']}" for row in snapshot['artifacts']).encode()
    snapshot['bundleDigest']=hashlib.sha256(joined).hexdigest()
    (tmp_path/'release_snapshot_manifest.json').write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):validator.check_snapshot_registry(manifest)


def test_definition_classes_keep_models_distinct_from_exact_exchange_and_examples():
    spec = importlib.util.spec_from_file_location('definition_validator', ROOT / 'tools/validate_release_contract.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.check_definition_classes()


@pytest.mark.parametrize('fault', ['missing-class', 'example-as-required-wire', 'model-as-example',
                                 'closed-schema-as-model', 'duplicate-classification', 'missing-minimum-guard'])
def test_definition_classification_cannot_drop_minima_or_silently_force_example_layout(tmp_path, monkeypatch, fault):
    spec = importlib.util.spec_from_file_location('definition_validator', ROOT / 'tools/validate_release_contract.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    path = tmp_path / 'modules/edition-1.5.md'; path.parent.mkdir()
    text = (ROOT / 'modules/edition-1.5.md').read_text()
    if fault == 'missing-class': text = text.replace('`normative_semantic_model` | 保留已有', '| 保留已有', 1)
    elif fault == 'example-as-required-wire':
        text = text.replace('JSON 展示为 `informative_example`', 'JSON 展示为 `normative_reference_contract`', 1)
    elif fault == 'model-as-example': text = text.replace('| `normative_semantic_model` |', '| `informative_example` |', 1)
    elif fault == 'closed-schema-as-model':
        text = text.replace('| `normative_reference_contract` |', '| `normative_semantic_model` |', 1)
    elif fault == 'duplicate-classification':
        row = next(line for line in text.splitlines() if line.startswith('| ErrorEnvelope、'))
        text = text.replace(row, row + '\n' + row, 1)
    else: text = text.replace('文档分类不得撤销已有 required 字段语义。', '', 1)
    assert text != (ROOT / 'modules/edition-1.5.md').read_text(), 'mutation did not exercise the intended source'
    path.write_text(text)
    monkeypatch.setattr(validator, 'ROOT', tmp_path)
    with pytest.raises(ValueError): validator.check_definition_classes()


@pytest.mark.parametrize('fault', [
    'missing-copy', 'changed-bytes', 'missing-identity', 'duplicate-identity',
    'unknown-identity', 'redirected-path', 'not-required', 'qualified', 'wrong-author',
    'wrong-dialect', 'external-reference', 'unresolved-reference', 'duplicate-field',
    'wrong-inner-identity', 'nested-scope', 'dynamic-reference',
])
def test_standalone_reference_closure_rejects_missing_or_rebound_inputs(tmp_path, monkeypatch, fault):
    spec = importlib.util.spec_from_file_location('release_validator', ROOT / 'tools/validate_release_contract.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    shutil.copytree(ROOT / 'contracts', tmp_path / 'contracts')
    monkeypatch.setattr(validator, 'ROOT', tmp_path)
    manifest = _load('standard_manifest.json')
    validator.check_reference_contracts(manifest)
    reference = manifest['extensions']['referenceContracts']
    item = next(item for item in reference['schemas'] if item['contractIdentity'] == 'das-approved-facts/v1')
    path = tmp_path / item['path']
    if fault == 'missing-copy': path.unlink()
    elif fault == 'changed-bytes': path.write_bytes(path.read_bytes() + b' ')
    elif fault == 'missing-identity': reference['schemas'].remove(item)
    elif fault == 'duplicate-identity': reference['schemas'][-1] = dict(item)
    elif fault == 'unknown-identity': item['contractIdentity'] = 'das-bundle/v1'
    elif fault == 'redirected-path': item['path'] = '../outside.schema.json'
    elif fault == 'not-required': manifest['requiredArtifacts'].remove(item['path'])
    elif fault == 'qualified': reference['qualificationEligible'] = True
    elif fault == 'wrong-author': reference['authorRepo'] = 'candidate/self'
    else:
        schema = json.loads(path.read_bytes())
        if fault == 'wrong-dialect': schema['$schema'] = 'http://json-schema.org/draft-07/schema#'
        elif fault == 'external-reference': schema['$ref'] = 'https://unapproved.invalid/rule'
        elif fault == 'unresolved-reference': schema['$ref'] = '#/$defs/missing'
        elif fault == 'wrong-inner-identity': schema['properties']['contractIdentity']['const'] = 'das-bundle/v1'
        elif fault == 'nested-scope': schema['$defs']['fact']['$id'] = 'https://unapproved.invalid/scope'
        elif fault == 'dynamic-reference': schema['$dynamicRef'] = '#unapproved'
        data = json.dumps(schema).encode()
        if fault == 'duplicate-field': data = b'{"title":"duplicate",' + data[1:]
        path.write_bytes(data)
        # A correct newly calculated digest must not mask semantic/schema drift.
        item['sha256'] = hashlib.sha256(data).hexdigest()
    with pytest.raises(ValueError):
        validator.check_reference_contracts(manifest)
