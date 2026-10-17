"""A content edition must preserve old obligations and bind its new author/view."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator
import pytest

ROOT = Path(__file__).resolve().parents[1]


def module_at(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = module_at('edition_validator', 'tools/validate_modules.py')
indexes = module_at('edition_indexes', 'tools/generate_spec_indexes.py')


def inputs(root):
    return validator.load(root / 'standard_modules.json'), validator.load(root / 'migration/legacy_normative_baseline.json')


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / 'standard'
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    return root


def test_all_original_bytes_are_recovered_without_resampling_baseline():
    catalog, baseline = inputs(ROOT)
    validator.validate(catalog, baseline)
    assert catalog['standardVersion'] == '1.5.0-beta.1'
    for source in baseline['sources']:
        original = validator.legacy_source(ROOT, source)
        assert hashlib.sha256(original.encode()).hexdigest() == source['sha256']
    assert len(baseline['units']) == 479
    assert hashlib.sha256((ROOT / 'tests/compat/v1.4.0/standard_manifest.json').read_bytes()).hexdigest() == '64c16351258c9f34624197062e054f0e1441c29ac41959d3f5fbd5e7a72cf2a2'
    assert validator.render_views(catalog, baseline) == validator.render_views(catalog, baseline)
    for relative, text in validator.render_views(catalog, baseline).items():
        assert (ROOT / relative).read_text() == text


def test_current_templates_and_addenda_bind_the_current_edition():
    version = (ROOT / 'VERSION').read_text().strip()
    templates = (ROOT / 'appendices/appendix-m-doc-family-governance-and-module-doc-templates.md').read_text()
    assert templates.count('**Governing standard:** Docs as Software (DAS) Standard v' + version) == 8
    for relative in ('DAS_DEPLOYMENT_ADDENDUM.md', 'DAS_GOVERNANCE_COLLABORATION.md'):
        text = (ROOT / relative).read_text()
        assert 'subordinate to the Docs as Software (DAS) Standard v' + version + '.' in text
        assert 'Governing standard:' in text
    prompt = (ROOT / 'templates/prompts/generate_master_doc_from_PRD.md').read_text()
    assert '**Standard:** Docs as Software (DAS) Standard v' + version + '.' in prompt


@pytest.mark.parametrize('fault', ['stale-template', 'wrong-governing-version', 'stale-prompt', 'weaken-addendum'])
def test_edition_binding_cannot_waive_norms_or_restore_stale_templates(bundle, fault):
    version = (bundle / 'VERSION').read_text().strip()
    path = bundle / {'stale-template': 'appendices/appendix-m-doc-family-governance-and-module-doc-templates.md',
                     'wrong-governing-version': 'DAS_DEPLOYMENT_ADDENDUM.md',
                     'stale-prompt': 'templates/prompts/generate_master_doc_from_PRD.md',
                     'weaken-addendum': 'DAS_GOVERNANCE_COLLABORATION.md'}[fault]
    text = path.read_text()
    if fault == 'weaken-addendum': changed = text.replace('There MUST be a single', 'There MAY be a single', 1)
    else: changed = text.replace('v' + version, 'v9.0.0' if fault == 'wrong-governing-version' else 'v1.4.0', 1)
    assert changed != text
    path.write_text(changed)
    with pytest.raises(ValueError): validator.validate(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['old_must', 'old_bullet', 'old_context', 'missing_boundary', 'duplicate_boundary',
                                  'new_owner', 'missing_section', 'missing_case', 'renamed_case', 'missing_export',
                                  'claim_qualification'])
def test_edition_cannot_hide_loss_or_change_of_obligations(bundle, fault):
    catalog, baseline = inputs(bundle)
    manifest_path = bundle / 'standard_manifest.json'
    manifest = validator.load(manifest_path)
    if fault in {'old_must', 'old_bullet', 'missing_boundary', 'duplicate_boundary'}:
        path = bundle / 'SPECIFICATION.md'; text = path.read_text()
        if fault == 'old_must': text = text.replace('MUST', 'MAY', 1)
        elif fault == 'old_bullet': text = text.replace('which repo(s)', 'optional repository', 1)
        elif fault == 'missing_boundary': text = text.replace(validator.EDITION_MARKER, '', 1)
        else: text += validator.EDITION_MARKER
        path.write_text(text)
    elif fault == 'old_context':
        path = bundle / 'DAS_STANDARD_CONTEXT_PACK.md'; path.write_text(path.read_text().replace('**MUST:**', '**MAY:**', 1))
    elif fault == 'new_owner':
        core = next(m for m in catalog['modules'] if m['id'] == 'das.core')
        security = next(m for m in catalog['modules'] if m['id'] == 'das.security-agent')
        core['clauseIds'].remove('cl-13.2'); security['clauseIds'].append('cl-13.2')
    elif fault == 'missing_section':
        path = bundle / 'modules/edition-1.5.md'; path.write_text(path.read_text().replace('### 13.11 ', '#### Removed section ', 1))
    elif fault in {'missing_case', 'renamed_case'}:
        path = bundle / 'modules/acceptance-1.5.md'; text = path.read_text()
        text = text.replace('| A01.1 |', '| A99.1 |' if fault == 'renamed_case' else '| omitted |', 1)
        path.write_text(text)
    elif fault == 'missing_export': manifest['requiredArtifacts'].remove('modules/edition-1.5.md')
    else: manifest['extensions']['qualificationEligible'] = True
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError): validator.validate(catalog, baseline, bundle)


def test_generated_tail_has_only_one_author(bundle):
    path = bundle / 'SPECIFICATION.md'
    original = path.read_text()
    prefix, tail = original.split(validator.EDITION_MARKER)
    path.write_text(prefix + validator.EDITION_MARKER + tail.replace('Agent', 'unapproved actor', 1))
    result = subprocess.run([sys.executable, '-I', '-B', 'tools/validate_modules.py', '--check'],
                            cwd=bundle, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert 'stale generated module view: SPECIFICATION.md' in result.stdout + result.stderr
    catalog, baseline = inputs(bundle)
    path.write_text(validator.render_views(catalog, baseline, bundle)['SPECIFICATION.md'])
    validator.validate(catalog, baseline, bundle)
    assert path.read_text() == original


@pytest.mark.parametrize('version', ['1.5.0-beta..1', '1.5.0-beta.01', '01.5.0-beta.1', '1.5.0-beta.1+'])
def test_authoritative_version_rejects_noncanonical_prereleases(bundle, monkeypatch, version):
    (bundle / 'VERSION').write_text(version + '\n'); monkeypatch.setattr(indexes, 'ROOT', bundle)
    with pytest.raises(ValueError, match='invalid authoritative'): indexes.payloads()


@pytest.mark.parametrize('version', ['1.4.0', '1.5.0-beta.1', '1.5.0-beta.10', '1.5.0-beta.1+build.2'])
def test_id_registry_schema_accepts_historical_and_new_versions(version):
    registry = deepcopy(validator.load(ROOT / 'ids/standard_ids.json')); registry['standardVersion'] = version
    Draft202012Validator(validator.load(ROOT / 'standard_ids.schema.json')).validate(registry)


def test_each_template_declares_normative_and_informative_portions():
    catalog = validator.load(ROOT / 'template_catalog.json')
    for template in catalog['templates']:
        assert 'Normative portions:' in template['notes']
        assert 'Informative portions:' in template['notes']
