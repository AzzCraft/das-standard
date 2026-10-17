from copy import deepcopy
import importlib.util
from pathlib import Path
import shutil
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("das_module_validator", ROOT / "tools/validate_modules.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def inputs():
    return validator.load(ROOT / "standard_modules.json"), validator.load(ROOT / "migration/legacy_normative_baseline.json")


def test_independent_baseline_and_deterministic_navigation():
    catalog, baseline = inputs()
    validator.validate(catalog, baseline)
    assert len(baseline["sources"]) == 17
    assert len(baseline["units"]) == 479
    first = validator.render_views(catalog, baseline)
    assert first == validator.render_views(catalog, baseline)
    for path, expected in first.items():
        assert (ROOT / path).read_text() == expected


def test_generated_specification_links_resolve_inside_standalone_repo():
    catalog, baseline = inputs()
    text = validator.render_views(catalog, baseline)['SPECIFICATION.md']
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    for target in re.findall(r'\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)', text):
        if target.startswith(('https://', 'http://', 'mailto:')) or '{' in target:
            continue
        resolved = (ROOT / target).resolve()
        assert resolved.is_relative_to(ROOT) and resolved.exists(), target


@pytest.mark.parametrize("mutation", ["missing_unit", "duplicate_unit", "cycle", "unknown_dependency", "informative", "missing_source", "missing_rule", "duplicate_rule", "wrong_author", "missing_hfvi_dependency"])
def test_illegal_catalog_rejected(mutation):
    catalog, baseline = inputs()
    catalog = deepcopy(catalog)
    core = catalog["modules"][0]
    other = catalog["modules"][1]
    if mutation == "missing_unit": core["legacyUnitIds"].pop()
    elif mutation == "duplicate_unit": other["legacyUnitIds"].append(core["legacyUnitIds"][0])
    elif mutation == "cycle": core["dependsOn"].append(other["id"])
    elif mutation == "unknown_dependency": core["dependsOn"].append("das.unknown")
    elif mutation == "informative": core["effect"] = "informative"
    elif mutation == "missing_source": core["normativeSources"] = []
    elif mutation == "missing_rule": catalog["conditionalMappings"].pop()
    elif mutation == "duplicate_rule": catalog["conditionalMappings"].append(deepcopy(catalog["conditionalMappings"][0]))
    elif mutation == "wrong_author": catalog["conditionalMappings"][0]["authorRef"] = "standard_modules.json#/fake"
    elif mutation == "missing_hfvi_dependency": catalog["modules"][6]["dependsOn"] = ["das.core"]
    with pytest.raises(ValueError):
        validator.validate(catalog, baseline)


def test_legacy_must_removal_and_condition_change_rejected(tmp_path):
    catalog, baseline = inputs()
    shutil.copytree(ROOT, tmp_path / "standard")
    copy = tmp_path / "standard"
    source = copy / "SPECIFICATION.md"
    original = source.read_bytes()
    source.write_bytes(original.replace(b"MUST", b"MAY", 1))
    with pytest.raises(ValueError, match="body changed"):
        validator.validate(catalog, baseline, copy)
    source.write_bytes(original)
    manifest = validator.load(copy / "standard_manifest.json")
    manifest["conditionalRequirements"].pop()
    import json
    (copy / "standard_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="conditional obligation"):
        validator.validate(catalog, baseline, copy)


def test_shared_artifact_references_are_legal():
    catalog, baseline = inputs()
    for module in catalog["modules"]:
        assert "standard_manifest.schema.json" in module["requiredArtifactRefs"]
    validator.validate(catalog, baseline)


SHARED_REQUIREMENT_SOURCES = [
    ('das.architecture-modularity', 'DAS_STANDARD_CONTEXT_PACK.md'),
    ('das.architecture-modularity', 'appendices/appendix-c-project-master-doc-template.md'),
    ('das.contracts-compatibility', 'appendices/appendix-c-project-master-doc-template.md'),
    ('das.core', 'CHANGELOG.md'),
    ('das.core', 'DAS_STANDARD_CONTEXT_PACK.md'),
    ('das.core', 'appendices/appendix-c-project-master-doc-template.md'),
    ('das.core', 'appendices/appendix-e-multi-repo-contract-driven-standard.md'),
    ('das.governance.documentation', 'appendices/appendix-d-ui-spec-appendix-template.md'),
    ('das.governance.documentation', 'appendices/appendix-g-ai-product-engineering-principles-addendum.md'),
    ('das.governance.verification-release', 'DAS_STANDARD_CONTEXT_PACK.md'),
    ('das.governance.verification-release', 'appendices/appendix-c-project-master-doc-template.md'),
    ('das.governance.verification-release', 'appendices/appendix-e-multi-repo-contract-driven-standard.md'),
    ('das.interaction.standard-ui', 'appendices/appendix-c-project-master-doc-template.md'),
]


def test_repeated_requirements_keep_all_sources_in_each_owner_closure():
    catalog, baseline = inputs()
    modules = {module['id']: module for module in catalog['modules']}
    for owner, source in SHARED_REQUIREMENT_SOURCES:
        assert source in modules[owner]['normativeSources'], (owner, source)
    # Sharing a source must not duplicate ownership or alter original text.
    validator.validate(catalog, baseline)


@pytest.mark.parametrize('owner,source', SHARED_REQUIREMENT_SOURCES)
def test_repeated_requirement_source_cannot_be_removed_from_owner(owner, source):
    catalog, baseline = inputs()
    catalog = deepcopy(catalog)
    modules = {module['id']: module for module in catalog['modules']}
    # Keep every leaf, carrier, parent, source file and release artifact intact.
    # A declaration in a different module cannot cover this owner's reference.
    modules[owner]['normativeSources'] = [
        path for path in modules[owner]['normativeSources'] if path != source]
    with pytest.raises(ValueError, match='declared normative author'):
        validator.validate(catalog, baseline)


@pytest.mark.parametrize('prefix,positive,negative,activity,body', [
    ('das.ai-runtime-evaluation.data.', 'manifest-metadata-only',
     'no-raw-content-in-manifest', 'activity.dataset_manifest', 'metadata only'),
    ('das.governance.verification-release.platform.', 'generated-handwritten-separated',
     'no-hand-edited-generated-artifact', 'activity.repository_codegen',
     'clearly separated from hand-written code'),
])
def test_same_line_positive_and_negative_rules_keep_separate_force(prefix, positive, negative, activity, body):
    leaves = validator.load(ROOT / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    for criterion, force in ((positive, 'MUST'), (negative, 'MUST NOT')):
        leaf = by_id[prefix + criterion]
        assert validator.source_fragment(ROOT, leaf['strengthRef']) == force
        assert leaf['activation'] == {'op': 'fact', 'key': activity}
    reading = validator.render_views(*inputs())['modules/requirements.md']
    section = reading.split('## ' + prefix + positive + '\n', 1)[1].split('\n## ', 1)[0]
    assert '\nMUST ' + body + '\n' in section
    assert '\nMUST NOT ' + body + '\n' not in section


@pytest.mark.parametrize('prefix,criterion,other', [
    ('das.ai-runtime-evaluation.data.', 'manifest-metadata-only', 'no-raw-content-in-manifest'),
    ('das.ai-runtime-evaluation.data.', 'no-raw-content-in-manifest', 'manifest-metadata-only'),
    ('das.governance.verification-release.platform.', 'generated-handwritten-separated', 'no-hand-edited-generated-artifact'),
    ('das.governance.verification-release.platform.', 'no-hand-edited-generated-artifact', 'generated-handwritten-separated'),
])
def test_same_line_force_cannot_be_swapped(tmp_path, prefix, criterion, other):
    import json
    bundle = tmp_path / 'standard'
    shutil.copytree(ROOT, bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['criterion']: leaf for leaf in leaves['requirements']
             if leaf['id'].startswith(prefix)}
    by_id[criterion]['strengthRef'] = deepcopy(by_id[other]['strengthRef'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='reviewed leaf strength'):
        validator.validate_requirements(validator.load(bundle / 'standard_modules.json'),
                                        validator.load(bundle / 'migration/legacy_normative_baseline.json'), bundle)
