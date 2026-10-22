#!/usr/bin/env python3
"""Release self-conformance checks for the shipped DAS Standard bundle."""
from __future__ import annotations

# Direct CLI use has the same dependency isolation as scripts/verify.
import sys
if __name__ == "__main__" and not sys.flags.isolated:
    import os
    os.execv(sys.executable, [sys.executable, "-I", "-B", __file__, *sys.argv[1:]])
import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

# Resolve the adjacent helper explicitly; these maintenance scripts support -I.
import importlib.util
_io_spec = importlib.util.spec_from_file_location("das_standard_io", Path(__file__).with_name("standard_io.py"))
standard_io = importlib.util.module_from_spec(_io_spec)
_io_spec.loader.exec_module(standard_io)

ROOT = Path(__file__).resolve().parents[1]
VALID_GATES = {"all", "bundle-files", "schemas", "release-snapshot", "compat-release"}
REFERENCE_CONTRACTS = {
    "das-http-declaration/v1": "http_declaration.schema.json",
    "das-http-inventory/v1": "http_inventory.schema.json",
    "das-verification-plan/v1": "verification_plan.schema.json",
    "das-verification-evidence/v1": "verification_evidence.schema.json",
    "das-action-decision/v1": "action_decision.schema.json",
    "das-integration-plan/v1": "integration_plan.schema.json",
    "das-integration-receipt/v1": "integration_receipt.schema.json",
    "das-completion/v1": "completion.schema.json",
    **{'das-' + name.replace('_', '-') + '/v1': name + '.schema.json'
       for name in ('analysis_task_binding', 'analysis_verification_plan',
                    'analysis_verification_evidence', 'analysis_action_decision', 'analysis_completion',
                    'version_verification_plan', 'version_verification_evidence', 'version_action_decision')},
    'das-approved-facts-check/v1': 'approved_facts_check.schema.json',
    'das-bundle-resolution/v1': 'bundle_resolution.schema.json',
    'das-context-pack/v1': 'context_pack.schema.json',
    "das-approved-facts/v1": "approved_facts.schema.json",
    "das-approved-facts-preview-input/v1": "approved_facts_preview_input.schema.json",
    "das-candidate-binding/v1": "candidate_binding.schema.json",
    "das-version-tree-plan/v1": "version_tree_plan.schema.json",
    "das-version-switch-receipt/v1": "version_switch_receipt.schema.json",
    "das-resource-action-intent/v1": "resource_action_intent.schema.json",
    "das-action-authorization/v1": "action_authorization.schema.json",
    "das-bundle-preview-input/v1": "bundle_preview_input.schema.json",
    "das-bundle-preview/v1": "bundle_preview.schema.json",
    "das-bundle-preview-input/v2": "bundle_preview_input_v2.schema.json",
    "das-bundle-preview/v2": "bundle_preview_v2.schema.json",
    "das-bundle-preview-input/v3": "bundle_preview_input_v3.schema.json",
    "das-bundle-preview/v3": "bundle_preview_v3.schema.json",
    "das-approved-facts-check/v2": "approved_facts_check_v2.schema.json",
    "das-bundle-resolution/v2": "bundle_resolution_v2.schema.json",
    "das-context-pack/v2": "context_pack_v2.schema.json",
    "das-text-delta/v1": "text_delta.schema.json",
    "das-text-delta-end/v1": "text_delta_end.schema.json",
}

def check_definition_classes() -> None:
    """Enforce S04's explicit labels in its single normative Markdown author.

    This establishes classification, not a producer's lossless mapping proof.
    No duplicate registry or new schema is needed for the document table.
    """
    text = (ROOT / 'modules/edition-1.5.md').read_text(encoding='utf-8')
    section = text.split('<a id="s04"></a>', 1)[-1].split('<a id="s05"></a>', 1)[0]
    expected = {
        'ErrorEnvelope、Diagnostics、Budget、RunManifest、PipelineResult、JobEnvelope、DatasetManifest、EvalReport': 'normative_semantic_model',
        'AnnotatedContent / CitationSet': 'normative_semantic_model',
        '现有 StreamFrame': 'normative_semantic_model',
        '标准 manifest、registry/report、locks 等已有正式 schema': 'normative_reference_contract',
        '新授权、证据绑定和受保护完成交换对象': 'normative_reference_contract',
    }
    found = {}
    for line in section.splitlines():
        if not line.startswith('|') or line.startswith(('| 对象 |', '|---')):
            continue
        fields = [field.strip() for field in line.split('|')[1:-1]]
        if len(fields) != 3 or fields[0] in found:
            raise ValueError('definition classification is missing, malformed or duplicated')
        found[fields[0]] = fields[1].strip('`')
    if found != expected or any(phrase not in section for phrase in (
            '文档分类不得撤销已有 required 字段语义。',
            '上述语义模型中的 JSON 展示为 `informative_example`',
            '不据此强制示例字段布局；其中已声明的最低信息义务仍须保留。')):
        raise ValueError('definition classification changed model, exact-contract or minimum-information semantics')

def check_reference_contracts(manifest: dict) -> None:
    """Check the selected reference profile offline in the standalone bundle.

    These hashes check content closure, not independent approval. Actual payload
    validation, exact numbers and native signatures remain the tools' contract.
    """
    reference = manifest['extensions'].get('referenceContracts', {})
    if (set(reference) != {'authorRepo', 'authorPath', 'use', 'qualificationEligible', 'schemas'}
            or reference['authorRepo'] != 'cadence-oss/cadence-protocol'
            or reference['authorPath'] != 'schemas/das_v1_5'
            or reference['use'] != 'reference_only' or reference['qualificationEligible'] is not False):
        raise ValueError('reference contract provenance or nonqualification boundary changed')
    records = reference['schemas']
    if (not isinstance(records, list) or len(records) != len(REFERENCE_CONTRACTS)
            or any(not isinstance(item, dict) or set(item) != {'contractIdentity', 'path', 'sha256'} for item in records)):
        raise ValueError('reference contract inventory is incomplete or malformed')
    identities, schema_ids = set(), set()
    required = set(manifest['requiredArtifacts'])
    for item in records:
        identity = item['contractIdentity']
        if identity not in REFERENCE_CONTRACTS or identity in identities:
            raise ValueError('unknown or duplicate reference contract identity')
        identities.add(identity)
        relative = 'contracts/das_v1_5/' + REFERENCE_CONTRACTS[identity]
        if item['path'] != relative or relative not in required:
            raise ValueError('reference contract path is absent from required artifacts')
        path = ROOT / relative
        if (not path.is_file() or any(parent.is_symlink() for parent in (path, path.parent, path.parent.parent))):
            raise ValueError('reference contract is not a local regular file: ' + relative)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('reference contract digest mismatch: ' + relative)
        def unique(pairs):
            value = {}
            for name, field in pairs:
                if name in value:
                    raise ValueError('duplicate reference schema member')
                value[name] = field
            return value
        schema = standard_io.loads(data)
        if (schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema'
                or not isinstance(schema.get('$id'), str) or schema['$id'] in schema_ids
                or schema.get('properties', {}).get('contractIdentity', {}).get('const') != identity):
            raise ValueError('reference schema dialect or identity mismatch')
        schema_ids.add(schema['$id'])
        Draft202012Validator.check_schema(schema)
        pending = [schema]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                if ('$vocabulary' in node or '$dynamicRef' in node
                        or (node is not schema and '$id' in node)):
                    raise ValueError('unapproved reference schema vocabulary or resolution scope')
                if '$ref' in node:
                    ref = node['$ref']
                    if not isinstance(ref, str) or not ref.startswith('#/'):
                        raise ValueError('reference schema cannot fetch external rules')
                    target = schema
                    try:
                        for token in ref[2:].split('/'):
                            target = target[token.replace('~1', '/').replace('~0', '~')]
                    except (KeyError, TypeError):
                        raise ValueError('unresolved local reference schema pointer') from None
                    if not isinstance(target, (dict, bool)):
                        raise ValueError('reference schema pointer does not address a schema')
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)

def load(rel: str) -> dict:
    return standard_io.loads((ROOT / rel).read_text(encoding="utf-8"))

def validate(data_rel: str, schema_rel: str) -> None:
    value = load(data_rel)
    Draft202012Validator(load(schema_rel), format_checker=FormatChecker()).validate(value)
    if schema_rel == 'suite_version_closure.schema.json':
        check_package_versions(value)

def check_package_versions(closure):
    for component, field in [('standard', 'standardVersion'), ('suite', 'suiteVersion'),
                             ('factory', 'factoryVersion'), ('verifyRuntime', 'verifyRuntimeVersion'),
                             ('policyPack', 'policyPackVersion')]:
        ref = closure.get('refs', {}).get(component, {})
        if ref.get('kind') != 'package' or ref.get('pinType') != 'version' or field not in closure:
            continue
        def package_version(value):
            return re.sub(r'-(alpha|beta|rc)\.(\d+)', lambda m: {'alpha':'a','beta':'b','rc':'rc'}[m[1]]+m[2], value)
        if package_version(closure[field]) != package_version(ref['pinValue']):
            raise ValueError(f'{component}: {field} differs from package pinValue')

def headings(text: str) -> list[tuple[int, int, str]]:
    result = []
    for index, line in enumerate(text.splitlines()):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((index, len(match.group(1)), match.group(2)))
    return result

def normalize(value: str) -> str:
    value = re.sub(r"\s+#+\s*$", "", value.strip())
    value = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s+", "", value)
    return re.sub(r"\s+", " ", value).strip().lower()

def slug(value: str) -> str:
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return re.sub(r"[\s-]+", "-", value).strip("-")

def section(text: str, title: str, by_slug: bool = False) -> str:
    lines = text.splitlines()
    if by_slug:
        marker = f'<a id="{title}"></a>'
        for index, line in enumerate(lines):
            if line.strip() == marker:
                return "\n".join(lines[index:])
    expected = title if by_slug else normalize(title)
    selected = None
    for index, level, heading in headings(text):
        candidate = slug(heading) if by_slug else normalize(heading)
        if candidate == expected:
            selected = index, level
            break
    if selected is None:
        raise ValueError(f"missing section or anchor: {title}")
    start, level = selected
    end = next((index for index, other_level, _ in headings(text) if index > start and other_level <= level), len(lines))
    return "\n".join(lines[start:end])

def metadata_fields(text: str) -> set[str]:
    fields = set()
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+(?:\*\*)?([^:*]+?)(?:\*\*)?:\s*", line)
        if match:
            fields.add(match.group(1).strip())
    return fields

def check_enum_definitions(manifest: dict) -> None:
    bindings = {
        "gateCadences": "gateCadenceDefinitions",
        "gateEnforcementClasses": "gateEnforcementDefinitions",
        "repoRoles": "repoRoleDefinitions",
        "toolClasses": "toolClassDefinitions",
        "toolPlacementTargets": "toolPlacementDefinitions",
        "verifyGateKinds": "verifyGateKindDefinitions",
        "moduleStates": "moduleStateDefinitions",
        "releaseSnapshotKinds": "releaseSnapshotKindDefinitions",
        "verifyReportOutcomes": "gateOutcomeDefinitions",
    }
    for enum_name, definitions_name in bindings.items():
        if not (set(manifest['enums'][enum_name]) == set(manifest[definitions_name])):
            raise ValueError(f'{definitions_name} must exactly define {enum_name}')

def check_templates(manifest: dict) -> None:
    roles = set(manifest['enums']['repoRoles'])
    if set(load('verify_registry.schema.json')['properties']['repoRole']['enum']) != roles or set(load('suite_lock.schema.json')['$defs']['moduleLock']['properties']['role']['enum']) != roles:
        raise ValueError('registry/suite-lock roles differ from canonical repoRoles')
    catalog = load("template_catalog.json")
    if catalog.get("standardVersion") != (ROOT / "VERSION").read_text().strip() or catalog.get("standardVersion") != manifest["standardVersion"]:
        raise ValueError("canonical template catalog version differs from VERSION/manifest")
    catalog = catalog["templates"]
    if not ({item['docType'] for item in catalog} == set(manifest['docTypes'])):
        raise ValueError("template catalog must cover every declared document type")
    if not (len({item['docType'] for item in catalog}) == len(catalog)):
        raise ValueError("template catalog has duplicate document types")
    for item in catalog:
        path = ROOT / item["artifactPath"]
        if not (path.is_file()):
            raise ValueError(f"missing template artifact: {item['artifactPath']}")
        body = section(path.read_text(encoding="utf-8"), item["sectionAnchor"], by_slug=True)
        missing = set(manifest["requiredDocMetadata"][item["docType"]]) - metadata_fields(section(body, "Document Control"))
        if missing:
            raise ValueError(f"template {item['docType']} missing metadata: {sorted(missing)}")
        present = {normalize(title) for _, _, title in headings(body)}
        missing = [
            name
            for name in manifest["requiredSections"][item["docType"]]
            if not any(actual == normalize(name) or actual.startswith(normalize(name) + " ") for actual in present)
        ]
        if missing:
            raise ValueError(f"template {item['docType']} missing sections: {missing}")

def check_addenda(manifest: dict) -> None:
    for ref_name in ("deploymentAddendum", "governanceAddendum"):
        path = ROOT / manifest["normativeArtifactRefs"][ref_name]
        text = path.read_text(encoding="utf-8")
        missing = set(manifest["requiredDocMetadata"]["normative_addendum"]) - metadata_fields(section(text, "Document Control"))
        if missing:
            raise ValueError(f'{path.name} missing metadata: {sorted(missing)}')
        present = {normalize(title) for _, _, title in headings(text)}
        missing = [name for name in manifest["requiredSections"]["normative_addendum"] if normalize(name) not in present]
        if missing:
            raise ValueError(f'{path.name} missing sections: {missing}')

def check_ids_and_context(manifest: dict) -> None:
    chapters = {item["id"] for item in load("chapter_index.json")["chapters"]}
    clauses = {item["id"] for item in load("clause_index.json")["clauses"]}
    appendices = {f"A-{item['id'].split('-', 1)[1].upper()}" for item in load("chapter_index.json")["appendices"]}
    ids = load("ids/standard_ids.json")
    if not (ids['standardVersion'] == manifest['standardVersion']):
        raise ValueError("Standard ID registry version differs from manifest")
    if not (set(ids['appendixIds']) == appendices):
        raise ValueError("Standard ID registry omits or adds an appendix identity")
    contracts = load("context_packs/contracts-and-naming.json")["summary"].lower()
    if not ('compatibility mode by default' in contracts and 'refactor mode only' in contracts and ('strict or tolerant' not in contracts)):
        raise ValueError("contracts Context Pack lost its declared compatibility/refactor semantics")
    evidence = load("context_packs/verification-and-evidence.json")
    if not (evidence['chapters'] == ['ch-10']):
        raise ValueError("verification Context Pack has an incorrect chapter mapping")
    if not ('offline-first' not in evidence['summary'].lower() and 'signing' not in evidence['summary'].lower()):
        raise ValueError("verification Context Pack claims undeclared offline/signing requirements")
    for path in (ROOT / "context_packs").glob("*.json"):
        pack = standard_io.loads(path.read_text(encoding="utf-8"))
        if not (pack['standardVersion'] == manifest['standardVersion']):
            raise ValueError("standard contract check failed: pack['standardVersion'] == manifest['standardVersion']")
        if not (set(pack['chapters']) <= chapters):
            raise ValueError("standard contract check failed: set(pack['chapters']) <= chapters")
        if not (set(pack['clauses']) <= clauses):
            raise ValueError("standard contract check failed: set(pack['clauses']) <= clauses")

def check_snapshot_registry(manifest: dict) -> None:
    standard_io.validate_content_inventory(ROOT, manifest)
    snapshot = load("release_snapshot_manifest.json")
    names = [item["path"] for item in snapshot["artifacts"]]
    required = manifest["requiredArtifacts"]
    if (names != sorted(set(names)) or len({name.casefold() for name in names}) != len(names)
            or len(required) != len(set(required))
            or set(names) != set(required) - {"release_snapshot_manifest.json"}
            or "release_snapshot_manifest.json" in names):
        raise ValueError('snapshot member inventory must exactly close the required non-circular content')
    if (snapshot['standardVersion'] != manifest['standardVersion']
            or snapshot['standardManifestVersion'] != manifest['standardVersion']):
        raise ValueError('snapshot edition differs from the Standard manifest')
    registry = load("verify_registry.json")
    default = registry["defaultVerifyCommand"]
    prefix = shlex.split(default)
    if prefix not in (["./scripts/verify"], ["./scripts/verify", "--full"]):
        raise ValueError('registry default command must use the supported verify grammar')
    actual = []
    for item in registry['gates']:
        argv = shlex.split(item['command'])
        if len(argv) != len(prefix) + 2 or argv[:-2] != prefix or argv[-2] != '--gate':
            raise ValueError('registry command must exactly select one supported gate')
        actual.append(argv[-1])
    if len(actual) != 4 or set(actual) != {'bundle-files', 'schemas', 'release-snapshot', 'compat-release'}:
        raise ValueError(f'registry gate mismatch: {sorted(actual)}')
    for item in snapshot["artifacts"]:
        name = item['path']
        if (not name or name.startswith('/') or '\\' in name or ':' in name
                or any(ord(char) < 32 or ord(char) == 127 for char in name)
                or any(part in ('', '.', '..') for part in name.split('/'))
                or item['required'] is not True or not re.fullmatch(r'[0-9a-f]{64}', item['sha256'])):
            raise ValueError('noncanonical required snapshot member')
        path = ROOT
        for part in name.split('/'):
            path = path / part
            if path.is_symlink(): raise ValueError('snapshot member cannot traverse a symlink')
        if not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError(f"snapshot artifact missing: {item['path']}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if not (actual_hash == item['sha256']):
            raise ValueError(f"snapshot hash mismatch: {item['path']}")
    joined = "\n".join(f"{item['path']}:{item['sha256']}" for item in sorted(snapshot["artifacts"], key=lambda value: value["path"]))
    if not (hashlib.sha256(joined.encode()).hexdigest() == snapshot['bundleDigest']):
        raise ValueError("standard contract check failed: hashlib.sha256(joined.encode()).hexdigest() == snapshot['bundleDigest']")

def check_compat(manifest: dict) -> None:
    check_sbom_dependencies()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    fixture = ROOT / "tests" / "compat" / f"v{version}" / "standard_manifest.json"
    if not (fixture.is_file()):
        raise ValueError(f'missing current compatibility fixture: {fixture.relative_to(ROOT)}')
    if not (standard_io.loads(fixture.read_text(encoding='utf-8')) == manifest):
        raise ValueError('current compatibility fixture must exactly copy the canonical manifest')
    for item in load('tests/compat/compat_window.json')['fixtures']:
        payload = load(item['path'])
        if item['version'] == '1.1.0':
            # The 1.1 record is an explicit adapter, not a full manifest.
            # Validate its whole recorded shape, including source identity.
            source_fields = {
                'repository': {'type': 'string', 'format': 'uri'},
                'tag': {'const': 'v1.1.0'},
                **{key: {'type': 'string', 'pattern': '^[0-9a-f]{40}$'} for key in ('commit', 'tree')},
                **{key: {'type': 'string', 'pattern': '^[0-9a-f]{64}$'} for key in ('specificationSha256', 'licenseSha256')},
            }
            properties = {
                'schemaVersion': {'const': '1.0.0'},
                'fixtureKind': {'const': 'historical-compatibility-adapter'},
                'standardVersion': {'const': '1.1.0'},
                'requiredArtifacts': {'type': 'array', 'minItems': 1, 'uniqueItems': True, 'items': {'type': 'string', 'minLength': 1}},
                'normativeArtifactRefs': {'type': 'object', 'minProperties': 1, 'additionalProperties': {'type': 'string', 'minLength': 1}},
                'historicalSource': {'type': 'object', 'required': list(source_fields), 'properties': source_fields, 'additionalProperties': False},
            }
            schema = {'type': 'object', 'required': list(properties), 'properties': properties, 'additionalProperties': False}
        else:
            # The full 1.4/current fixtures share the shipped manifest contract.
            schema = load('standard_manifest.schema.json')
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
        Draft202012Validator({'properties': {'standardVersion': {'const': item['version']}}}).validate(payload)

def check_sbom_dependencies() -> None:
    pins = {}
    for raw in (ROOT / 'requirements-verify.txt').read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.+-]*)', line)
        if not match:
            raise ValueError('unsupported verification dependency declaration')
        name = re.sub(r'[-_.]+', '-', match[1]).lower()
        if name in pins:
            raise ValueError('duplicate verification dependency')
        pins[name] = match[2]
    packages = load('SBOM.spdx.json')['packages']
    for name, version in pins.items():
        matches = [p for p in packages if re.sub(r'[-_.]+', '-', p['name']).lower() == name]
        if len(matches) != 1 or matches[0].get('versionInfo') != version:
            raise ValueError('SBOM direct dependency mismatch: ' + name)

def check_author_links() -> None:
    text = (ROOT / 'modules/requirements.md').read_text(encoding='utf-8')
    links = re.findall(r'\[Normative author\]\(([^)]+)\)', text)
    if len(links) != len(load('standard_requirements.json')['editionRequirements']):
        raise ValueError('edition author link count differs from leaf count')
    for link in set(links):
        name, separator, anchor = link.partition('#')
        path = ROOT / 'modules' / name
        if not separator or not path.is_file() or anchor not in re.findall(r'<a\s+id="([^"]+)"\s*>', path.read_text(encoding='utf-8')):
            raise ValueError('unresolved normative author fragment: ' + link)

def check_manifest_artifacts() -> None:
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?', version):
        raise ValueError('invalid VERSION')
    validate('standard_manifest.json', 'standard_manifest.schema.json')
    if load('standard_manifest.json')['standardVersion'] != version:
        raise ValueError('standard_manifest standardVersion differs from VERSION')
    for name in ('suite_version_closure', 'tooling_lock', 'local_extension_manifest'):
        path = ROOT / (name + '.json')
        if path.exists():
            validate(name + '.json', name + '.schema.json')

def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--gate", choices=sorted(VALID_GATES), default="all")
    mode.add_argument("--manifest-artifacts-only", action="store_true")
    args = parser.parse_args()
    if args.manifest_artifacts_only:
        check_manifest_artifacts()
        return 0
    manifest = load("standard_manifest.json")
    if not (manifest['interactionProfiles'] == manifest['enums']['interactionProfiles']):
        raise ValueError("standard contract check failed: manifest['interactionProfiles'] == manifest['enums']['interactionProfiles']")
    if not (manifest['gateCadences'] == manifest['enums']['gateCadences']):
        raise ValueError("standard contract check failed: manifest['gateCadences'] == manifest['enums']['gateCadences']")
    check_enum_definitions(manifest)
    if args.gate in {"all", "bundle-files"}:
        check_author_links()
        check_definition_classes()
        check_reference_contracts(manifest)
        check_templates(manifest)
        check_addenda(manifest)
        check_ids_and_context(manifest)
    if args.gate in {"all", "schemas"}:
        check_reference_contracts(manifest)
        for data, schema in (
            ("standard_manifest.example.json", "standard_manifest.schema.json"),
            ("chapter_index.json", "chapter_index.schema.json"),
            ("clause_index.json", "clause_index.schema.json"),
            ("ids/standard_ids.json", "standard_ids.schema.json"),
        ):
            validate(data, schema)
    if args.gate in {"all", "release-snapshot"}:
        check_snapshot_registry(manifest)
    if args.gate in {"all", "compat-release"}:
        check_compat(manifest)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
