import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError
from tests._root_contract import repository_root_for_test_file

ROOT = repository_root_for_test_file(__file__)
spec = importlib.util.spec_from_file_location("review_release_contract", ROOT / "tools/validate_release_contract.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.mark.parametrize("defect", ["version", "missing", "duplicate", "unsupported-pin"])
def test_sbom_semantics_reject_even_when_outer_digests_are_recomputed(tmp_path, monkeypatch, defect):
    for name in ["requirements-verify.txt", "SBOM.spdx.json", "release_snapshot_manifest.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    (tmp_path / "release").mkdir()
    shutil.copy2(ROOT / "release/release_report.json", tmp_path / "release/release_report.json")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    validator.check_sbom_dependencies()
    path = tmp_path / "SBOM.spdx.json"
    sbom = json.loads(path.read_text())
    item = next(p for p in sbom["packages"] if p["name"] == "pytest")
    if defect == "version":
        item["versionInfo"] = "0.0.0"
    elif defect == "missing":
        sbom["packages"].remove(item)
    elif defect == "duplicate":
        sbom["packages"].append(dict(item))
    else:
        (tmp_path / "requirements-verify.txt").write_text("pytest>=9\n")
    path.write_text(json.dumps(sbom))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    report_path = tmp_path / "release/release_report.json"
    report = json.loads(report_path.read_text())
    report["artifacts"]["sbom"]["sha256"] = digest
    report_path.write_text(json.dumps(report))
    snapshot_path = tmp_path / "release_snapshot_manifest.json"
    snapshot = json.loads(snapshot_path.read_text())
    for row in snapshot["artifacts"]:
        if row["path"] in {"SBOM.spdx.json", "requirements-verify.txt", "release/release_report.json"}:
            row["sha256"] = hashlib.sha256((tmp_path / row["path"]).read_bytes()).hexdigest()
    joined = "\n".join(f"{r['path']}:{r['sha256']}" for r in sorted(snapshot["artifacts"], key=lambda r: r["path"]))
    snapshot["bundleDigest"] = hashlib.sha256(joined.encode()).hexdigest()
    snapshot_path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):
        validator.check_sbom_dependencies()


def test_actual_manifest_helper_rejects_wrong_structure_and_version(tmp_path, monkeypatch):
    for name in ["VERSION", "standard_manifest.json", "standard_manifest.schema.json", "tooling_lock.schema.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    validator.check_manifest_artifacts()
    path = tmp_path / "standard_manifest.json"
    original = json.loads(path.read_text())
    for payload in [{"standardVersion": "0.0.0", "unrelatedNote": "1.5.0-beta.1"}, {**original, "standardVersion": "0.0.0"}]:
        path.write_text(json.dumps(payload))
        with pytest.raises((ValueError, ValidationError)):
            validator.check_manifest_artifacts()
    path.write_text(json.dumps(original))
    (tmp_path / "tooling_lock.json").write_text("{}")
    with pytest.raises(ValidationError):
        validator.check_manifest_artifacts()


def test_all_edition_author_fragments_exist_and_missing_fragment_rejects(tmp_path, monkeypatch):
    validator.check_author_links()
    (tmp_path / "modules").mkdir()
    for name in ["modules/requirements.md", "modules/edition-1.5.md", "standard_requirements.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    path = tmp_path / "modules/edition-1.5.md"
    path.write_text(path.read_text().replace('<a id="shared-contracts"></a>', ''))
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="unresolved normative author"):
        validator.check_author_links()


def test_diff_helper_parses_supported_calls_and_propagates_git_errors(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/diff_standard", scripts / "diff_standard")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "SPECIFICATION.md").write_text("old\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "SPECIFICATION.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "fixture"], check=True)
    for args in [["HEAD"], ["HEAD", "HEAD"], ["HEAD", "--stat"], ["HEAD", "HEAD", "--stat"]]:
        run = subprocess.run(["bash", str(scripts / "diff_standard"), *args], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    for args in [["HEAD", "nonexistent-ref"], ["--bad"], ["HEAD", "HEAD", "extra"]]:
        run = subprocess.run(["bash", str(scripts / "diff_standard"), *args], capture_output=True, text=True)
        assert run.returncode != 0


@pytest.mark.parametrize("version,valid", [
    ("01.5.0", False), ("1.5.0-beta..1", False), ("1.5.0-01", False),
    ("１.５.０", False), ("1.5.0-", False), ("1.5.0+", False),
    ("0.0.0", True), ("1.5.0", True), ("1.5.0-beta.1", True),
    ("1.5.0+build.001", True), ("1.5.0-beta.1+build.001", True),
])
def test_manifest_version_uses_strict_release_semver(tmp_path, monkeypatch, version, valid):
    for name in ["standard_manifest.json", "standard_manifest.schema.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    (tmp_path / "VERSION").write_text(version + "\n")
    manifest = json.loads((tmp_path / "standard_manifest.json").read_text())
    manifest["standardVersion"] = version
    (tmp_path / "standard_manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    if valid:
        validator.check_manifest_artifacts()
    else:
        with pytest.raises(ValueError, match="invalid VERSION"):
            validator.check_manifest_artifacts()
    # Keep acceptance aligned with the actual release workflow's Bash grammar.
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    grammar = workflow.split("semver='")[1].split("'", 1)[0]
    check = subprocess.run(["bash", "-c", '[[ "$1" =~ ^v${2}$ ]]', "semver-case", "v" + version, grammar])
    assert (check.returncode == 0) is valid


def _io_helper():
    spec = importlib.util.spec_from_file_location('test_standard_io', ROOT / 'tools/standard_io.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


@pytest.mark.parametrize('raw', ['{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
                                  '{"a":1,"a":2}', '{"a":1,"\\u0061":2}'])
def test_strict_json_rejects_ambiguous_or_non_json_inputs(raw):
    with pytest.raises(ValueError):
        _io_helper().loads(raw)


def test_strict_json_preserves_legal_extensions():
    assert _io_helper().loads('{"x":[null,true,1.25,"NaN","Infinity"]}') == {'x':[None,True,1.25,'NaN','Infinity']}


@pytest.mark.parametrize('linked', ['symlink','hardlink','parent'])
def test_generated_output_preserves_external_aliases(tmp_path, linked):
    import os
    helper = _io_helper()
    outside = tmp_path / 'external'; outside.mkdir()
    sentinel = outside / 'value'; sentinel.write_bytes(b'external')
    root = tmp_path / 'root'; root.mkdir()
    target = root / 'output'
    if linked == 'symlink': target.symlink_to(sentinel)
    elif linked == 'hardlink': os.link(sentinel,target)
    else:
        (root / 'parent').symlink_to(outside, target_is_directory=True)
        target = root / 'parent/value'
    with pytest.raises(ValueError): helper.write_text(target,'changed')
    assert sentinel.read_bytes() == b'external'


def test_generated_output_replace_failure_preserves_old_bytes(tmp_path, monkeypatch):
    helper = _io_helper()
    target = tmp_path / 'output'; target.write_bytes(b'old')
    def refuse(*args): raise OSError('injected replace failure')
    monkeypatch.setattr(helper.os,'replace',refuse)
    with pytest.raises(OSError): helper.write_text(target,'new')
    assert target.read_bytes() == b'old'
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize('tool,output', [
    ('generate_content_snapshot.py','release_snapshot_manifest.json'),
    ('generate_spec_indexes.py','clause_index.json'),
    ('validate_modules.py','modules/README.md'),
])
@pytest.mark.parametrize('kind', ['symlink','hardlink','ordinary'])
def test_real_generators_refuse_output_aliases(tmp_path,tool,output,kind):
    import os
    import shutil
    import subprocess
    import sys
    bundle = tmp_path / 'standard'; bundle.mkdir()
    for rel in json.loads((ROOT/'standard_manifest.json').read_text())['requiredArtifacts']:
        target=bundle/rel; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/rel,target)
    target=bundle/output
    before=target.read_bytes()
    outside=tmp_path/'sentinel';outside.write_bytes(b'external')
    if kind!='ordinary':
        target.unlink()
        if kind=='symlink':target.symlink_to(outside)
        else:os.link(outside,target)
    chapter_before=(bundle/'chapter_index.json').read_bytes()
    result=subprocess.run([sys.executable,'-B',str(bundle/'tools'/tool)],capture_output=True,text=True)
    if kind=='ordinary':
        assert result.returncode==0,result.stdout+result.stderr
        assert target.read_bytes()==before
    else:
        assert result.returncode!=0
        assert any(word in result.stdout+result.stderr for word in ("symlink", "hardlink", "hard link", "linked", "non-private regular")), result.stdout+result.stderr
        assert (bundle/'chapter_index.json').read_bytes()==chapter_before
    assert outside.read_bytes()==b'external'


def test_numbered_subclauses_and_independent_anchor_gold():
    chapters=json.loads((ROOT/'chapter_index.json').read_text())['chapters']
    clauses=json.loads((ROOT/'clause_index.json').read_text())['clauses']
    by_id={entry['id']:entry for entry in chapters+clauses}
    required=[f'cl-{prefix}.{n}' for prefix,count in [('4.2',2),('4.4',10),('4.5',2),('6.7',5),('6.8',7),('13.20',3),('13.21',4)] for n in range(1,count+1)]
    assert len(required)==33
    assert set(required)<=set(by_id)
    assert len(clauses)==120 and len({x['id'] for x in clauses})==120
    assert by_id['cl-7.3']['file']=='SPECIFICATION.md#73-determinism--replay-tiers-required'
    assert by_id['ch-4']['file']=='SPECIFICATION.md#4-canonical-contracts-and-naming-cross-boundary--persisted'
    assert by_id['cl-4.4.1']['chapter']=='ch-4'
    gold={
      'ch-4':'4-canonical-contracts-and-naming-cross-boundary--persisted',
      'ch-8':'8-backend--orchestrator-engineering-ai-product-engineering-principles',
      'ch-9':'9-project-documentation-requirements-master-doc--doc-families--ui-spec',
      'ch-12':'12-ddd--bdd-integration-domain--behavior-as-first-class-artifacts',
      'cl-3.3':'33-recommended-multi-repo-baseline-topology-b--hybrid',
      'cl-4.5':'45-design-system-contracts-tokens--components',
      'cl-7.3':'73-determinism--replay-tiers-required',
      'cl-7.9':'79-refactoring--migration-patterns',
      'cl-9.4':'94-package--library--worker--infra-module-docs-model',
      'cl-9.8':'98-multi-party--multi-company-documentation-governance-humans--tools',
    }
    for identity,fragment in gold.items():
        assert by_id[identity]['file']=='SPECIFICATION.md#'+fragment



def test_canonical_catalog_and_role_enums_use_current_manifest(monkeypatch):
    manifest=json.loads((ROOT/'standard_manifest.json').read_text())
    original=validator.load
    def wrong_catalog(name):
        value=original(name)
        if name=='template_catalog.json':value['standardVersion']='1.4.0'
        return value
    monkeypatch.setattr(validator,'load',wrong_catalog)
    with pytest.raises(ValueError,match='catalog version'):
        validator.check_templates(manifest)
    roles=set(manifest['enums']['repoRoles'])
    assert set(original('verify_registry.schema.json')['properties']['repoRole']['enum'])==roles
    assert set(original('suite_lock.schema.json')['$defs']['moduleLock']['properties']['role']['enum'])==roles


def test_report_registry_dates_and_closure_required_semantics(tmp_path, monkeypatch):
    import copy
    from jsonschema import Draft202012Validator, FormatChecker
    for data_name, schema_name in [('verify_registry.json','verify_registry.schema.json'), ('verify_report.example.json','verify_report.schema.json'), ('local_extension_manifest.example.json','local_extension_manifest.schema.json'), ('suite_version_closure.example.json','suite_version_closure.schema.json')]:
        data = json.loads((ROOT / data_name).read_text())
        schema = json.loads((ROOT / schema_name).read_text())
        check = Draft202012Validator(schema, format_checker=FormatChecker())
        check.validate(data)
        bad = []
        if data_name == 'verify_registry.json':
            for key in ['owners', 'scope']:
                item = copy.deepcopy(data); del item['gates'][0][key]; bad.append(item)
        elif data_name == 'verify_report.example.json':
            item = copy.deepcopy(data); del item['toolchain']; bad.append(item)
            for value in ['not-a-timestamp', '2026-02-30T00:00:00Z', None, 7]:
                item = copy.deepcopy(data); item['startedAt'] = value; bad.append(item)
            item = copy.deepcopy(data);item['overallOutcome']='pass'
            for gate in item['gates']: gate.update(expected=True, executed=False, outcome='not_run')
            bad.append(item)
            item = copy.deepcopy(data);item['overallOutcome']='pass';item['gates'][0].update(expected=True, failureOnNoResults=True,artifactCount=0);bad.append(item)
        elif data_name == 'local_extension_manifest.example.json':
            item=copy.deepcopy(data);item['extensions'][0]['reviewDate']='not-a-date';bad.append(item)
        else:
            for value in ['missing',True,'false',None]:
                item=copy.deepcopy(data)
                if value=='missing': del item['refs']['standard']['floating']
                else:item['refs']['standard']['floating']=value
                bad.append(item)
        for item in bad:
            with pytest.raises(ValidationError):check.validate(item)
        # Exercise the same helper used by content schemas, not just schema construction.
        shutil.copy2(ROOT/schema_name,tmp_path/schema_name)
        path=tmp_path/data_name;path.write_text(json.dumps(bad[0]))
        monkeypatch.setattr(validator,'ROOT',tmp_path)
        with pytest.raises(ValidationError):validator.validate(data_name,schema_name)


def test_content_inventory_closes_reading_links_and_required_inputs(tmp_path):
    manifest=json.loads((ROOT/'standard_manifest.json').read_text())
    for name in manifest['requiredArtifacts']:
        if name.endswith('.md'):
            target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    validator.standard_io.validate_content_inventory(tmp_path,manifest)
    for omitted in ['VERSION','citation.cff','GOVERNANCE.md','.github/workflows/release.yml']:
        changed=dict(manifest,requiredArtifacts=[p for p in manifest['requiredArtifacts'] if p != omitted])
        with pytest.raises(ValueError,match='omitted|omits'):
            validator.standard_io.validate_content_inventory(tmp_path,changed)


def test_verify_build_identity_belongs_to_content_root(tmp_path):
    import os, sys, venv
    import jsonschema, pytest, rfc3339_validator
    environment = tmp_path / 'env'
    venv.EnvBuilder(with_pip=False).create(environment)
    site_packages=next((environment/'lib').glob('python*/site-packages'))
    # Explicitly reuse the installed test dependencies; this tests Git identity,
    # not the separately pinned release dependency environment.
    roots=sorted({str(Path(module.__file__).resolve().parent.parent) for module in (jsonschema,pytest)})
    roots.append(str(Path(rfc3339_validator.__file__).resolve().parent))
    (site_packages/'review-dependencies.pth').write_text('\n'.join(roots)+'\n')
    env={**os.environ,'PYTHON':str(environment/'bin/python'), 'GIT_CEILING_DIRECTORIES':str(tmp_path)}
    def copy(root):
        for rel in json.loads((ROOT/'standard_manifest.json').read_text())['requiredArtifacts']:
            path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,path)
    def git(root,*args):
        return subprocess.check_output(['git','-C',str(root),*args],env=env,stderr=subprocess.STDOUT,text=True).strip()
    independent=tmp_path/'independent';copy(independent)
    def verify(root,expected):
        proc=subprocess.run(['bash','scripts/verify','--gate','schemas'],cwd=root,env=env,text=True,capture_output=True)
        assert proc.returncode==0,proc.stdout+proc.stderr
        assert f'verify: buildRef={expected}\n' in proc.stdout,proc.stdout
    content='content:v'+(ROOT/'VERSION').read_text().strip()
    verify(independent,content)
    parent=tmp_path/'outer';parent.mkdir();git(parent,'init','-q');git(parent,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','outer')
    nested=parent/'content';copy(nested);verify(nested,content)
    git(independent,'init','-q');git(independent,'add','.');git(independent,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','content')
    identity='git:'+git(independent,'rev-parse','HEAD');verify(independent,identity)
    worktree=tmp_path/'worktree';git(independent,'worktree','add','--detach',str(worktree),'HEAD');verify(worktree,identity)
