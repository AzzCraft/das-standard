#!/usr/bin/env python3
"""Check logical module ownership against the independent pre-migration baseline.

Preserve the independent 1.4 body while adding a single 1.5 normative author.
Only declared edition metadata and generated, append-only views may differ.
Complete executable leaf applicability is still a separate migration gate.
"""
from __future__ import annotations

# Direct CLI use has the same dependency isolation as scripts/verify.
import sys
if __name__ == "__main__" and not sys.flags.isolated:
    import os
    os.execv(sys.executable, [sys.executable, "-I", "-B", __file__, *sys.argv[1:]])

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator

# Resolve the adjacent helper explicitly; these maintenance scripts support -I.
import importlib.util
_io_spec = importlib.util.spec_from_file_location("das_standard_io", Path(__file__).with_name("standard_io.py"))
standard_io = importlib.util.module_from_spec(_io_spec)
_io_spec.loader.exec_module(standard_io)

ROOT = Path(__file__).resolve().parents[1]
# Reviewed pre-migration input from 6d90333aea16987fc490570746fb5f93c930b970.
# Consumer-provided hashes cannot establish this independent denominator:
# co-editing baseline, catalog and leaves must still fail. An intentional new
# baseline needs a separately reviewed update of this pin.
# Capture pin is immutable; public content-equivalent v1.4.0 blobs are documented in README.md.
LEGACY_BASELINE_SHA256 = 'd0c337fd2dc69b9343b6ddc500b0c4209947dca5288f3b6a017662abc7081caf'
MODULE_IDS = {
    "das.core", "das.architecture-modularity", "das.contracts-compatibility",
    "das.ai-runtime-evaluation", "das.interaction.headless", "das.interaction.standard-ui",
    "das.interaction.hfvi", "das.governance.documentation", "das.governance.verification-release",
    "das.security-agent",
}
EDITION_MARKER = '\n<!-- DAS-GENERATED-EDITION-1.5: tools/validate_modules.py -->\n'
CONTEXT_MARKER = '\n<!-- DAS-GENERATED-CONTEXT-1.5: tools/validate_modules.py -->\n'
# Independent assignment denominator: section numbers are navigation parents,
# not a claim that every paragraph/subcondition has become an executable leaf.
EDITION_OWNERS = {
    **{number: 'das.core' for number in (1, 2, 3, 18)},
    **{number: 'das.contracts-compatibility' for number in (4, 5, 6, 7, 8, 15)},
    **{number: 'das.security-agent' for number in (9, 10, 11, 12, 13, 20)},
    14: 'das.governance.documentation', 16: 'das.interaction.standard-ui',
    17: 'das.ai-runtime-evaluation', 19: 'das.governance.verification-release',
    21: 'das.governance.verification-release',
}
ACCEPTANCE_COUNTS = (3, 3, 2, 3, 3, 2, 2, 3, 7, 3, 6, 4, 3, 5, 5, 6,
                     5, 8, 8, 7, 3, 5, 3, 2, 5, 3, 9, 3, 2, 2, 7, 4)


def edition_metadata(root, path):
    """Exact edition bindings, with reversible original literals and line IDs.

    Historical inclusion notes and versioned compatibility examples stay old.
    Only current governing headers, relationships and template instructions
    follow VERSION; no general version replacement can rewrite requirements.
    """
    template_header = '- **Governing standard:** Docs as Software (DAS) Standard v1.4.0'
    if path == 'appendices/appendix-m-doc-family-governance-and-module-doc-templates.md':
        originals = {index - 1: template_header for index in (12, 37, 70, 106, 134, 162, 190, 218)}
    elif path == 'DAS_DEPLOYMENT_ADDENDUM.md':
        originals = {7: template_header, 8: '- **Last updated:** 2026-04-06',
            35: "This addendum is subordinate to the Docs as Software (DAS) Standard v1.4.0. It extends the standard's deployment and operations guidance without changing the governing conformance, precedence, or verification rules in the main specification."}
    elif path == 'DAS_GOVERNANCE_COLLABORATION.md':
        originals = {7: '- Last updated: 2026-04-06',
            35: "This addendum is subordinate to the Docs as Software (DAS) Standard v1.4.0. It elaborates the governance guidance in §9.1 and §9.6 without changing the main standard's conformance, precedence, or verification rules.",
            303: 'Governing standard: Docs as Software (DAS) Standard v1.4.0'}
    elif path == 'templates/prompts/generate_master_doc_from_PRD.md':
        originals = {3: '**Standard:** Docs as Software (DAS) Standard v1.4.0.'}
    else:
        originals = {}
    if not originals:
        return {}
    version = (root / 'VERSION').read_text().strip()
    date = load(root / 'standard_manifest.json')['releasedAt']
    return {index: (text.replace('v1.4.0', 'v' + version).replace('2026-04-06', date), text)
            for index, text in originals.items()}


def legacy_source(root, source):
    """Recover old bytes with a deliberately narrow metadata/view allowance.

    The independent baseline is never regenerated from the changed body. All
    original lines (including headings, bullets and conditions) must still hash
    to that baseline after these exact, reversible edition changes.
    """
    raw = local_file(root, source['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() == source['sha256']:
        return raw.decode('utf-8')
    path = source['path']
    text = raw.decode('utf-8')
    version = (root / 'VERSION').read_text().strip()
    date = load(root / 'standard_manifest.json')['releasedAt']
    marker = {'SPECIFICATION.md': EDITION_MARKER, 'DAS_STANDARD_CONTEXT_PACK.md': CONTEXT_MARKER,
              'CHANGELOG.md': '\n<!-- DAS-EDITION-1.5-CHANGELOG -->\n'}.get(path)
    if marker is not None:
        if text.count(marker) != 1:
            raise ValueError(f'legacy normative body changed without its declared edition boundary: {path}')
        text = text.split(marker, 1)[0]
    if path == 'SPECIFICATION.md':
        replacements = {
            4: (f'[![Version: v{version}](https://img.shields.io/badge/Version-v{version}-blue.svg)](CHANGELOG.md)',
                '[![Version: v1.4.0](https://img.shields.io/badge/Version-v1.4.0-blue.svg)](CHANGELOG.md)'),
            9: (f'**Last updated:** {date}', '**Last updated:** 2026-04-06'),
        }
    elif path == 'DAS_STANDARD_CONTEXT_PACK.md':
        replacements = {
            0: (f'# DAS Standard Context Pack (v{version})', '# DAS Standard Context Pack (v1.4.0)'),
            7: (f'- Last updated: {date}', '- Last updated: 2026-04-06'),
            8: (f'- Scope: Read-optimized quick reference for humans and AI agents working from the DAS v{version} content candidate.',
                '- Scope: Read-optimized quick reference for humans and AI agents working from the DAS v1.4.0 release bundle.'),
        }
    else:
        replacements = edition_metadata(root, path)
    lines = text.splitlines(keepends=True)
    for index, (current, original) in replacements.items():
        if lines[index] != current + '\n':
            raise ValueError(f'undeclared legacy metadata change: {path}:{index + 1}')
        lines[index] = original + '\n'
    text = ''.join(lines)
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != source['sha256']:
        raise ValueError(f'legacy normative body changed before extraction: {path}')
    return text

# Reviewed against the independent 1.4 body, not inferred from the new catalog.
# The five required fields include independently checkable sub-obligations;
# a breaking impact alone triggers its compatibility plan. Sequencing requires
# both documentation and enforcement. The original normative text stays author.
LEGACY_LEAVES = (
    ('repo-scope', 1859, 'which repo(s)'),
    ('module-scope', 1859, 'which module(s)'),
    ('contract-surface-scope', 1859, 'which contract surfaces'),
    ('contract-impact', 1860, 'none/additive/breaking'),
    ('breaking-compatibility-plan', 1860, 'compatibility plan'),
    ('determinism-tier', 1861, 'declared tier'),
    ('replay-expectation', 1861, 'whether replay is expected'),
    ('budgets', 1862, None),
    ('verification-commands', 1863, 'exact `verify` commands'),
    ('verification-outcomes', 1863, 'expected outcomes'),
    ('document-sequencing', 1875, 'documented in the Master Doc'),
    ('enforce-sequencing', 1875, 'enforced via the integration harness'),
)

# Independently reviewed against the unchanged §2.3/§2.4 carriers. A text unit
# is not a leaf: the L0 paragraph contains three obligations, and the headless
# inventory lists five distinct fields. Actual activity/profile facts determine
# applicability; successful checks, permissions and exemptions are not facts.
PROFILE_LEAVES = (
    ('conformance-one', '0005', 106, 'exactly one profile', 'MUST', ()),
    ('conformance-explicit-new-document', '0005', 107, 'state the declaration explicitly', 'MUST', ('activity.new_or_adopted_document',)),
    ('conformance-legacy-declaration', '0005', 108, 'materialize an explicit profile', 'SHOULD', ('document.legacy_v1_3_conformant',)),
    ('external-compatibility', '0005', 109, 'Compatibility Mode', 'MUST', ('activity.external_or_persisted_surface',)),
    ('external-fixtures', '0005', 109, 'fixture-backed', 'MUST', ('activity.external_or_persisted_surface',)),
    ('conformance-evolution', '0005', 110, 'evolve profiles over time', 'SHOULD', ()),
    ('conformance-enum-source', '0005', 111, 'source the allowed enum from `standard_manifest.json`', 'SHOULD', ('activity.tooling',)),
    ('l0-deferred-scope', '0007', 127, 'what is intentionally deferred', 'MUST', ('profile.l0',)),
    ('l0-debt-owner', '0007', 127, 'who owns that debt', 'MUST', ('profile.l0',)),
    ('l0-revisit-trigger', '0007', 127, 'when/why it will be revisited (date or explicit trigger)', 'MUST', ('profile.l0',)),
    ('interaction-one', '0009', 141, 'exactly one interaction profile', 'MUST', ()),
    ('interaction-explicit-new-document', '0009', 142, 'state the declaration explicitly', 'MUST', ('activity.new_or_adopted_document',)),
    ('interaction-legacy-declaration', '0009', 143, 'materialize an explicit interaction profile', 'SHOULD', ('document.legacy_v1_3_conformant',)),
    ('headless-note', '0009', 144, 'Headless Surface Note', 'MUST', ('profile.headless',)),
    ('headless-pointer-link', '0009', 145, 'link to the governing Headless Surface Note', 'MUST', ('profile.headless', 'activity.headless_pointer_doc')),
    ('headless-operator-surface', '0009', 146, 'operator surface', 'MUST', ('profile.headless',)),
    ('headless-cli-api-surfaces', '0009', 146, 'CLI/API surfaces', 'MUST', ('profile.headless',)),
    ('headless-job-runtime-surfaces', '0009', 146, 'job/runtime surfaces', 'MUST', ('profile.headless',)),
    ('headless-packet-export-surfaces', '0009', 146, 'packet/export surfaces', 'MUST', ('profile.headless',)),
    ('headless-no-screen-reason', '0009', 146, 'why no screen inventory exists', 'MUST', ('profile.headless',)),
    ('ui-spec', '0009', 147, 'UI Spec Appendix', 'MUST', ('profile.standard_ui', 'profile.hfvi')),
    ('hfvi-section', '0009', 148, '§6.8', 'MUST', ('profile.hfvi',)),
    ('hfvi-appendix', '0009', 148, 'Appendix K', 'MUST', ('profile.hfvi',)),
    ('interaction-enum-source', '0009', 149, 'source the allowed enum from `standard_manifest.json`', 'SHOULD', ('activity.tooling',)),
    ('hfvi-contract-surfaces', '0009', 150, 'treat interaction surfaces as contract surfaces', 'SHOULD', ('profile.hfvi',)),
)


# Explicit old manifest fields and publication/extension duties. These tuples
# are reviewed against the pinned source, not inferred from matching keywords.
# Enumeration/definition list children inherit the MUST at line 184. Optional
# mechanisms retain their real presence condition; no check/permission is a fact.
MANIFEST_LEAVES = (
    ('machine-readable-release', '0010', 154, 'ship machine-readable artifacts', 'MUST', ('activity.standard_release',)),
    ('self-describing-release', '0010', 154, 'self-describing enough to be locked, mirrored, and verified', 'MUST', ('activity.standard_release',)),
    *[(name, '0010', line, phrase, 'MUST', ('activity.standard_release', 'standard.repo_canonical'))
      for name, line, phrase in (
          ('artifact-version', 158, '`VERSION`'), ('artifact-changelog', 159, '`CHANGELOG.md`'),
          ('artifact-specification', 160, '`SPECIFICATION.md`'), ('artifact-self-verify', 161, '`scripts/verify`'),
          ('artifact-ci', 162, '`.github/workflows/verify.yml`'),
          ('artifact-manifest', 163, '`standard_manifest.json`'),
          ('artifact-manifest-schema', 164, '`standard_manifest.schema.json`'),
          ('artifact-suite-closure-schema', 165, '`suite_version_closure.schema.json`'),
          ('artifact-suite-lock-schema', 166, '`suite_lock.schema.json`'),
          ('artifact-tooling-lock-schema', 167, '`tooling_lock.schema.json`'),
          ('artifact-extension-schema', 168, '`local_extension_manifest.schema.json`'),
          ('artifact-verify-registry-schema', 169, '`verify_registry.schema.json`'),
          ('artifact-verify-report-schema', 170, '`verify_report.schema.json`'),
          ('artifact-release-snapshot-schema', 171, '`release_snapshot_manifest.schema.json`'),
          ('artifact-template-catalog', 172, '`template_catalog.json`'),
          ('artifact-template-schema', 173, '`template_catalog.schema.json`'),
          ('artifact-verify-registry', 174, '`verify_registry.json`'),
          ('artifact-release-snapshot', 175, '`release_snapshot_manifest.json`'))],
    ('published-required-paths', '0011', 179, 'physically exist in the published release bundle at the declared relative path', 'MUST', ('activity.standard_release',)),
    ('published-link-closure', '0011', 181, 'resolve inside the release bundle', 'MUST', ('activity.standard_release',)),
    *[(name, '0011', 182, phrase, 'SHOULD', ('activity.standard_release',))
      for name, phrase in (('release-check-required-paths', '`requiredArtifacts`'),
                           ('release-check-normative-refs', '`normativeArtifactRefs`'),
                           ('release-check-supporting-refs', '`supportingArtifactRefs`'))],
    ('manifest-version', '0012', 186, '`standardVersion`', 'MUST', ('activity.standard_release',)),
    *[('manifest-enum-' + name, '0012', line, phrase, 'MUST', ('activity.standard_release',))
      for name, line, phrase in (
          ('conformance', 188, 'conformance profiles'), ('interaction', 189, 'interaction profiles'),
          ('doc-status', 190, 'document status values'), ('gate-cadence', 191, 'gate cadences'),
          ('gate-enforcement', 192, 'gate enforcement classes'), ('doc-family-role', 193, 'doc-family roles'),
          ('module-kind', 194, 'module kinds'), ('addendum-kind', 195, 'addendum kinds'),
          ('determinism', 196, 'determinism values'), ('repo-role', 197, 'repo roles'),
          ('tool-class', 198, 'tool classes'), ('tool-placement', 199, 'tool placement targets'),
          ('verify-gate-kind', 200, 'verify gate kinds'), ('suite-module-state', 201, 'suite module states'),
          ('release-snapshot-kind', 202, 'release snapshot kinds'), ('verify-report-outcome', 203, 'verify-report outcomes'))],
    ('manifest-metadata-enum-bindings', '0012', 204, 'metadata-field -> enum bindings', 'MUST', ('activity.standard_release',)),
    ('manifest-section-enum-bindings', '0012', 205, 'section-value -> enum bindings', 'MUST', ('activity.standard_release',)),
    ('manifest-required-metadata', '0012', 206, 'required metadata fields by doc type', 'MUST', ('activity.standard_release',)),
    ('manifest-required-sections', '0012', 207, 'required sections', 'MUST', ('activity.standard_release',)),
    ('manifest-required-subsections', '0012', 207, 'required **subsections** by doc type/profile', 'MUST', ('activity.standard_release', 'standard.has_subsection_requirements')),
    ('manifest-conditional-rules', '0012', 208, 'conditional requirements', 'MUST', ('activity.standard_release', 'standard.has_conditional_requirements')),
    ('manifest-cadence-definitions', '0012', 209, 'cadence', 'MUST', ('activity.standard_release',)),
    ('manifest-enforcement-definitions', '0012', 209, 'enforcement definitions', 'MUST', ('activity.standard_release',)),
    *[('manifest-definition-' + name, '0012', 210, phrase, 'MUST', ('activity.standard_release',))
      for name, phrase in (('repo-role', 'repo roles'), ('tool-class', 'tool classes'),
                           ('tool-placement', 'tool placement targets'), ('verify-gate-kind', 'verify gate kinds'),
                           ('suite-module-state', 'suite module states'), ('release-snapshot-kind', 'release snapshot kinds'))],
    ('manifest-appendix-refs', '0012', 211, 'references to appendix files', 'MUST', ('activity.standard_release',)),
    ('manifest-normative-artifact-refs', '0012', 211, 'other normative machine-readable artifacts', 'MUST', ('activity.standard_release',)),
    ('manifest-tooling-expectations', '0012', 212, 'tooling expectations required by Appendix L', 'MUST', ('activity.standard_release',)),
    ('manifest-shipped-addenda', '0012', 213, 'normative addenda', 'MUST', ('activity.standard_release', 'standard.ships_normative_addendum')),
    ('manifest-template-catalog', '0012', 214, 'template catalog', 'MUST', ('activity.standard_release',)),
    *[('manifest-' + name + '-schema', '0012', 215, '`' + wire + '`', 'MUST', ('activity.standard_release', 'standard.uses_' + wire))
      for name, wire in (('suite-lock', 'suite_lock'), ('verify-registry', 'verify_registry'),
                         ('verify-report', 'verify_report'), ('release-snapshot', 'release_snapshot_manifest'))],
    ('status-normative-values', '0013', 221, '`draft | active | frozen | deprecated`', 'MUST', ()),
    ('status-declaration-values', '0013', 222, 'use only the normative enum values', 'MUST', ('document.declares_status',)),
    ('status-reject-unknown', '0013', 223, 'fail on unknown status values rather than silently normalizing them', 'SHOULD', ('activity.tooling',)),
    ('addendum-required-entries', '0014', 227, 'require those entries explicitly', 'MUST', ('activity.standard_release', 'standard.ships_normative_addendum')),
    ('addendum-kind-enum', '0014', 228, 'normative enum', 'MUST', ('activity.standard_release',)),
    # VERSION/self-verify/CI and actual snapshot/registry repeat earlier duties;
    # their full text is retained in the context, not duplicated as new leaves.
    ('canonical-release-presentation', '0014', 229, 'MUST NOT be presented as the canonical governed release', 'MUST', ('activity.standard_release', 'standard.repo_canonical')),
    ('tooling-metadata-bindings', '0014', 230, 'consume metadata-field enum bindings', 'SHOULD', ('activity.tooling',)),
    ('companion-doc-family', '0015', 232, 'represented as governed doc type `normative_addendum`', 'SHOULD', ('activity.standard_release', 'standard.ships_companion_doc')),
    # The permission is conditional: choosing an extension entails both
    # restrictions. Creating an extension itself remains optional.
    ('extension-machine-manifest', '0016', 236, 'local extension manifest', 'MUST', ('activity.local_extension',)),
    ('extension-masterdoc-reference', '0016', 236, 'referenced from the project Master Doc', 'MUST', ('activity.local_extension',)),
    ('extension-namespaced-id', '0016', 237, 'namespaced', 'MUST', ('activity.local_extension',)),
    *[('extension-' + name, '0016', 238, '`' + field + '`', 'MUST', ('activity.local_extension',))
      for name, field in (('name', 'name'), ('namespace', 'namespace'), ('kind', 'kind'),
                          ('extension-point', 'extensionPoint'), ('owner', 'owner'),
                          ('scope', 'scope'), ('compatibility-note', 'compatibilityNote'))],
    ('extension-review-trigger', '0016', 239, '`upstreamingTrigger` **or** `reviewDate`', 'MUST', ('activity.local_extension',)),
    ('extension-doc-type-mapping', '0016', 240, '`mapsToCoreDocType`', 'MUST', ('activity.local_extension', 'extension.satisfies_core_doc_type')),
    ('extension-schema-validation', '0016', 241, 'validate against `local_extension_manifest.schema.json`', 'SHOULD', ('activity.local_extension',)),
    ('extension-no-silent-enum-widening', '0016', 242, 'silently widen normative DAS enums', 'MUST', ()),
)


SDMM_LEAVES = (
    ('no-self-assembly', '0058', 1015, 'MUST NOT self-assemble across boundaries', 'MUST', ('activity.module_boundary',)),
    ('public-imports', '0059', 1022, 'public entrypoint', 'MUST', ('activity.module_boundary',)),
    ('no-deep-imports', '0059', 1023, 'Import from another module’s internal paths', 'MUST', ('activity.module_boundary',)),
    ('explicit-graph', '0060', 1026, 'explicit allowed dependency graph', 'MUST', ('activity.module_boundary',)),
    ('enforce-graph', '0060', 1027, 'Enforce the graph mechanically', 'MUST', ('activity.module_boundary',)),
    ('acyclic-graph', '0061', 1030, 'acyclic', 'MUST', ('activity.module_boundary',)),
    ('safe-import', '0062', 1033, 'safe', 'MUST', ('activity.module_boundary',)),
    ('fast-import', '0062', 1033, 'fast', 'MUST', ('activity.module_boundary',)),
    ('no-import-io', '0062', 1034, 'I/O', 'MUST', ('activity.module_boundary',)),
    ('no-import-network', '0062', 1034, 'network calls', 'MUST', ('activity.module_boundary',)),
    ('no-import-global-mutation', '0062', 1034, 'global mutations', 'MUST', ('activity.module_boundary',)),
    ('no-import-expensive-init', '0062', 1034, 'expensive initialization at import time', 'MUST', ('activity.module_boundary',)),
    ('explicit-initialization', '0062', 1035, 'functions, factories, or composition roots', 'SHOULD', ('activity.module_boundary',)),
    ('stable-public-api', '0063', 1039, 'public API surface', 'MUST', ('activity.module_boundary',)),
    ('consumed-contracts', '0063', 1040, 'contracts it consumes', 'MUST', ('activity.module_boundary',)),
    ('produced-contracts', '0063', 1040, 'produces', 'MUST', ('activity.module_boundary',)),
    ('contract-tests', '0063', 1041, 'tests that validate those contracts', 'MUST', ('activity.module_boundary',)),
    ('compatible-additive', '0065', 1048, 'additive changes', 'MUST', ('activity.external_or_persisted_surface',)),
    ('compatible-reader', '0065', 1048, 'tolerant readers', 'MUST', ('activity.external_or_persisted_surface',)),
    ('breaking-migration-window', '0065', 1049, 'migration windows for breaking changes (expand/contract)', 'MUST', ('activity.external_or_persisted_surface', 'change.contract_breaking')),
    ('refactor-boundaries', '0066', 1053, 'SDMM boundaries', 'MUST', ('boundary.internal_nonpersisted',)),
    ('refactor-graph', '0066', 1053, 'dependency graph rules', 'MUST', ('boundary.internal_nonpersisted',)),
    ('ci-boundary-tools', '0067', 1077, 'boundary enforcement tooling in CI', 'MUST', ('activity.module_boundary',)),
    ('canonical-verify', '0067', 1078, 'one canonical repo verify command', 'MUST', ('activity.module_boundary',)),
    ('module-map', '0067', 1079, '“module map” doc (or generated graph)', 'SHOULD', ('activity.module_boundary',)),
)


TOPOLOGY_LEAVES = (
    ('no-size-only-runtime-split', '0017', 254, 'Do not introduce a new runtime service', 'MUST', ('activity.runtime_boundary_design',)),
    ('prefer-sdmm', '0017', 254, 'Prefer SDMM-style modularization', 'SHOULD', ('activity.runtime_boundary_design',)),
    # These remain obligations to choose one lawful branch, not predicates
    # gated by an already-passing check or an approval supplied by the Worker.
    ('cross-repo-compatible-or-atomic', '0018', 303, None, 'MUST', ('activity.cross_repo_boundary',)),
    ('hub-no-business-logic', '0019', 319, 'business logic', 'MUST', ('component.contracts_hub',)),
    ('hub-no-orchestration', '0019', 319, 'runtime orchestration', 'MUST', ('component.contracts_hub',)),
    ('frontend-sdmm', '0020', 329, 'SDMM Frontend Track', 'SHOULD', ('component.frontend',)),
    ('backend-modular-monolith', '0021', 340, 'Remain a modular monolith', 'SHOULD', ('component.backend',)),
    ('algorithm-sdmm', '0022', 351, 'SDMM Algorithm Track', 'SHOULD', ('component.algorithm',)),
    ('eval-data-scrubbed-or-approved', '0023', 369, None, 'MUST', ('component.data_evals',)),
    ('ci-production-contract-pin', '0024', 383, '**pinned** contract version', 'MUST', ('activity.contract_consumer_ci_or_production',)),
    ('local-contract-override', '0024', 384, '**local override**', 'SHOULD', ('activity.local_contract_development',)),
    *[('contract-' + name, '0025', line, phrase, 'MUST', ('component.contracts_hub',))
      for name, line, phrase in (
          ('schema', 388, '**Schema**'), ('semantics', 389, '**Semantics**'),
          ('positive-fixtures', 390, 'known-good'), ('negative-fixtures', 390, 'known-bad'),
          ('ci-checks', 391, 'CI that validates schemas and fixtures'),
          ('compatibility-runners', 391, 'compatibility runners for versioned surfaces'))],
    *[('cross-language-' + name, '0026', line, phrase, 'SHOULD', ('contract.used_across_languages',))
      for name, line, phrase in (('types', 395, 'generated types/clients (or at least strongly-typed adapters)'),
                                 ('identifiers', 396, 'single canonical identifier set'))],
    *[(name, '0027', 400, phrase, 'MUST', ('contract.multiple_representations',))
      for name, phrase in (('one-authoring-ssot', 'exactly one'), ('generated-other-representations', 'generated artifacts'),
                           ('representation-drift-checks', 'drift checks'))],
    ('stable-semantics-reference', '0028', 435, 'stable Semantics reference', 'MUST', ('activity.cross_boundary_schema_or_api',)),
    ('linkable-semantics-doc', '0028', 435, 'linkable as a dedicated doc', 'SHOULD', ('activity.cross_boundary_schema_or_api',)),
    *[(name, '0029', line, phrase, 'MUST', ('activity.multi_repo_system',) + extra)
      for name, line, phrase, extra in (
          ('minimal-system-harness', 445, 'stand up the minimal system locally', ()),
          ('system-smoke-flow', 446, 'end-to-end smoke flow', ()),
          ('harness-compatibility-decode', 447, '**compatibility-mode decoding tests**', ()),
          ('harness-external-replay', 448, 'replay tests for algorithm runs when external dependencies exist', ('material.external_dependencies',)))],
    *[('harness-' + name, '0030', line, phrase, 'SHOULD', ('activity.multi_repo_system',))
      for name, line, phrase in (('release-sequencing', 452, 'cross-repo release sequencing tests'),
                                 ('bidirectional-decode', 453, '“old consumer reads new producer” and “new consumer reads old producer”'))],
)
TOPOLOGY_SCOPES = {'0025': (386, 391), '0026': (393, 396), '0029': (443, 448), '0030': (450, 453)}


# Reviewed §4 obligations. Shapes remain conceptual; OR choices describe the
# obligation, never predicates that hide it when a required field is missing.
# Closed new protected identities do not rewrite the old tolerant-reader rules.
CONTRACT_LEAVES = (
    ('serialized-camel-case', '0031', 461, 'use `camelCase`', 'MUST', ('activity.serialized_external_or_persisted_surface',)),
    ('protobuf-style', '0033', 471, 'Protobuf style (`snake_case`)', 'SHOULD', ('activity.protobuf_contract',)),
    ('protobuf-json-camel-case', '0033', 472, '`camelCase`', 'MUST', ('activity.protobuf_json_surface',)),
    *[('compat-' + name, '0034', line, phrase, 'MUST', ('activity.' + key,))
      for name, line, phrase, key in (
          ('api', 480, 'API responses and error envelopes', 'api_response_or_error'),
          ('events', 481, 'events/messages/stream frames', 'event_message_or_stream'),
          ('persisted', 482, 'persisted artifacts', 'persisted_artifact'),
          ('operational-schema', 483, 'dashboards/metrics schemas relied upon operationally', 'operational_dashboard_or_metrics_schema'),
          ('long-lived-session', 484, 'long-lived sessions (SSE/WS) spanning deploy boundaries', 'session_spanning_deploys'))],
    *[(name, '0035', 486, phrase, 'MUST', ('activity.compatibility_surface', 'change.contract_breaking'))
      for name, phrase in (('breaking-expand-contract', 'expand/dual-support/contract'), ('breaking-window', 'explicit compatibility window'))],
    ('legacy-tolerant-reader', '0036', 492, 'tolerant of unknown fields', 'MUST', ('activity.legacy_compatibility_surface',)),
    ('writer-dual-support', '0036', 493, 'remove or repurpose existing fields without a dual-support window', 'MUST', ('activity.legacy_compatibility_surface',)),
    *[(name, '0036', 494, phrase, 'MUST', ('activity.legacy_compatibility_surface',))
      for name, phrase in (('explicit-defaults', 'explicit'), ('document-defaults', 'documented'))],
    ('additive-fields', '0036', 495, 'Prefer additive fields', 'SHOULD', ('activity.legacy_compatibility_surface',)),
    *[(name, '0036', 496, phrase, 'SHOULD', ('activity.legacy_compatibility_surface', 'change.contract_deprecation'))
      for name, phrase in (('deprecation-note', '`deprecatedFields` note'), ('deprecation-date', 'removal date'))],
    ('persisted-schema-version', '0037', 500, '`schemaVersion`', 'SHOULD', ('activity.persisted_artifact',)),
    *[(name, '0037', 501, phrase, 'MUST', ('activity.compatibility_surface', 'change.contract_breaking'))
      for name, phrase in (('breaking-major-version', 'increment major version (SemVer)'), ('breaking-compatibility-runners', 'guarded by compatibility runners'))],
    ('non-atomic-window', '0037', 502, 'compatibility window', 'MUST', ('activity.compatibility_surface', 'deployment.non_atomic_producer_consumer')),
    *[('stable-' + name, '0038', line, phrase, 'MUST', (key,))
      for name, line, phrase, key in (
          ('job-type', 508, '`jobType`', 'activity.canonical_identifier_surface'), ('job-id', 508, '`jobId`', 'activity.canonical_identifier_surface'),
          ('run-id', 509, '`runId`', 'activity.canonical_identifier_surface'), ('profile-id', 510, '`profileId`', 'activity.canonical_identifier_surface'),
          ('config-identity', 511, '`configId` / `configHash`', 'activity.canonical_identifier_surface'), ('stage-id', 512, '`stageId`', 'activity.canonical_identifier_surface'),
          ('error-code', 513, 'error `code` values', 'activity.canonical_identifier_surface'), ('diagnostic-code', 514, 'diagnostic `codes[]`', 'activity.canonical_identifier_surface'),
          ('gating-dataset-id', 515, 'dataset IDs', 'activity.canonical_identifier_surface'), ('gating-metric-id', 515, 'metric IDs', 'activity.canonical_identifier_surface'),
          ('gating-score-id', 515, 'score IDs used for gating', 'activity.canonical_identifier_surface'),
          ('prompt-id', 516, 'prompt IDs', 'activity.prompt_or_tool_allowlist_identifiers'), ('tool-allowlist-id', 516, 'tool allowlist IDs', 'activity.prompt_or_tool_allowlist_identifiers'))],
    *[(name, '0039', 520, phrase, 'MUST', ('contract.equivalent_envelope',))
      for name, phrase in (('equivalent-envelope-mapping', 'documented mapping'), ('equivalent-envelope-lossless', 'keep it lossless'))],
    *[(name, '0040', line, phrase, strength, ('activity.error_envelope',))
      for name, line, phrase, strength in (
          ('error-stable-code', 537, 'stable', 'MUST'), ('error-machine-code', 537, 'machine-readable', 'MUST'),
          ('error-bounded-message', 538, 'bounded', 'MUST'), ('error-safe-message', 538, 'redaction-safe', 'MUST'),
          ('error-shallow-details', 539, 'shallow', 'SHOULD'), ('error-bounded-details', 539, 'bounded', 'SHOULD'))],
    ('diagnostic-codes-array', '0041', 554, '`codes` is an array', 'MUST', ('activity.diagnostics',)),
    ('diagnostic-scalar-kv', '0041', 555, 'scalars/short strings', 'SHOULD', ('activity.diagnostics',)),
    ('diagnostic-safe', '0041', 556, 'redaction-safe', 'MUST', ('activity.diagnostics',)),
    ('explicit-algorithm-budget', '0042', 560, 'explicit for algorithm execution', 'MUST', ('activity.algorithm_execution',)),
    ('budget-in-manifest', '0042', 560, 'recorded in both manifests and job envelopes', 'SHOULD', ('activity.run_manifest',)),
    ('budget-in-job', '0042', 560, 'recorded in both manifests and job envelopes', 'SHOULD', ('activity.job_envelope',)),
    ('stable-resource-names', '0043', 575, 'resource names are stable', 'MUST', ('activity.algorithm_execution',)),
    ('stable-exhaustion-code', '0043', 576, '`termination.code` MUST be set to a stable value', 'MUST', ('activity.algorithm_execution', 'budget.exhaustion_occurred')),
    ('hierarchical-budget', '0043', 577, 'hierarchical `children` budgets', 'SHOULD', ('activity.algorithm_execution', 'pipeline.non_trivial')),
    *[(name, '0044', line, phrase, 'MUST', ('activity.run_manifest',) + extra)
      for name, line, phrase, extra in (
          ('run-schema-version', 585, '`schemaVersion`', ()), ('run-id', 586, '`runId`', ()), ('run-created-at', 587, '`createdAt`', ()),
          ('run-correlation', 588, '`correlation.requestId` and/or `correlation.traceId`', ('material.correlations_applicable',)),
          ('run-pipeline-id', 589, '`pipeline.id`', ()), ('run-algorithm-version', 590, '`algorithm.version`', ()),
          ('run-contract-pins', 591, '`contracts`', ()), ('run-profile', 592, '`config.profileId`', ()),
          ('run-config-identity', 592, '(`config.configId` OR `config.configHash`)', ()), ('run-immutable-config', 592, 'MUST be immutable', ()),
          ('run-raw-input', 593, '`inputRef.rawInputId`', ()), ('run-input-identity', 593, 'at least one of: `inputRef.inputHash` or `inputRef.snapshotId`', ()),
          ('run-side-effects-mode', 594, '`sideEffectsMode`', ()),
          ('run-budget-allocated', 595, 'allocated', ()), ('run-budget-consumed', 595, 'consumed', ()), ('run-budget-remaining', 595, 'remaining', ()),
          ('run-determinism-tier', 596, '`determinism.tier`', ()), ('run-determinism-parameters', 596, 'any required determinism parameters', ('run.determinism_parameters_required',)))],
    ('no-embedded-manifest-hash', '0045', 653, 'embed `manifestHash` inside the RunManifest payload', 'MUST', ('activity.run_manifest',)),
    ('external-manifest-hash', '0045', 653, 'referencing objects', 'MUST', ('activity.run_manifest',)),
    ('canonical-manifest-hash', '0045', 654, 'canonical serialization', 'SHOULD', ('activity.run_manifest',)),
    ('pipeline-lossless-job', '0046', 658, 'losslessly wrappable', 'MUST', ('activity.pipeline_result',)),
    ('pipeline-run-link', '0047', 686, '`runId` links to a RunManifest', 'MUST', ('activity.pipeline_result',)),
    ('pipeline-status-error', '0047', 687, '`status` and `error` are consistent', 'MUST', ('activity.pipeline_result',)),
    ('pipeline-stage-summaries', '0047', 688, '`stageSummaries`', 'SHOULD', ('activity.pipeline_result', 'pipeline.non_trivial')),
    ('job-multiple-runs', '0048', 698, 'multiple runs', 'MUST', ('activity.job_envelope', 'job.retries_or_fallbacks')),
    *[(name, '0048', 699, phrase, 'SHOULD', ('activity.job_envelope',))
      for name, phrase in (('job-start-time', '`startedAt`'), ('job-finish-time', '`finishedAt`'))],
    ('job-side-effects-mode', '0049', 768, '`sideEffectsMode`', 'MUST', ('activity.job_envelope',)),
    ('job-profile', '0049', 769, '`profileId`', 'MUST', ('activity.job_envelope',)),
    ('job-config-identity', '0049', 769, '(`configId` OR `configHash`)', 'MUST', ('activity.job_envelope',)),
    ('job-manifest-pointer', '0049', 770, '`runs[].manifestRef`', 'MUST', ('activity.job_envelope',)),
    ('job-identical-pointers', '0049', 771, 'they MUST be identical', 'MUST', ('activity.job_envelope', 'job.both_manifest_pointers_present')),
    ('job-legacy-tolerant-reader', '0049', 772, 'ignore unknown fields', 'MUST', ('activity.legacy_job_envelope',)),
    *[('dataset-' + name, '0050', 827, '`' + field + '`', 'MUST', ('activity.dataset_manifest',))
      for name, field in (('intended-use', 'intendedUse'), ('provenance', 'provenance'), ('license', 'license'))],
    ('dataset-content-identity', '0050', 828, 'at least one of `snapshotId` or `contentHash`', 'MUST', ('activity.dataset_manifest',)),
    ('dataset-hash-method', '0050', 829, '`contentHashMethod`', 'MUST', ('activity.dataset_manifest', 'dataset.content_hash_present')),
    ('dataset-published-identity', '0050', 830, '`datasetId + datasetVersion` is immutable', 'MUST', ('activity.dataset_manifest', 'dataset.published')),
    ('dataset-artifact-pointer', '0050', 831, 'at least one entry in `artifactRefs`', 'MUST', ('activity.dataset_manifest',)),
    ('dataset-content-addressing', '0050', 832, 'prefer content-addressing', 'SHOULD', ('activity.dataset_manifest', 'dataset.content_addressing_feasible')),
    ('dataset-record-schema', '0050', 833, 'machine-checkable record schema', 'SHOULD', ('activity.dataset_manifest',)),
    ('dataset-legacy-tolerant-reader', '0050', 834, 'consumers MUST ignore unknown fields', 'MUST', ('activity.legacy_dataset_manifest',)),
    ('citation-mapping', '0051', 863, 'machine-checkable mapping', 'MUST', ('activity.citation_output',)),
    ('citation-unique-ids', '0052', 906, 'unique within the payload', 'MUST', ('activity.citation_output',)),
    ('citation-reference-exists', '0052', 907, 'exist in `references[]`', 'MUST', ('activity.citation_output',)),
    ('citation-sanitization', '0052', 908, 'sanitization layer', 'MUST', ('activity.citation_output',)),
    ('citation-safe-snippets', '0052', 911, 'include sensitive content in `snippet` by default', 'MUST', ('activity.citation_output',)),
    ('citation-offset-unit', '0052', 912, '`offsetUnit` MUST be explicitly set', 'MUST', ('activity.citation_output', 'citation.uses_offsets')),
    ('citation-offset-contract', '0052', 912, 'treated as part of the contract', 'MUST', ('activity.citation_output', 'citation.uses_offsets')),
    ('citation-web-utf16', '0052', 912, '`utf16CodeUnit` is RECOMMENDED', 'SHOULD', ('activity.citation_output', 'citation.uses_offsets', 'surface.web_ui')),
    ('citation-graceful-consumer', '0052', 913, 'degrade gracefully', 'MUST', ('activity.citation_consumption',)),
    ('citation-ui-spec', '0053', 915, 'specified in the UI Spec Appendix', 'MUST', ('activity.citation_interaction_ui',)),
    *[('stream-' + name, '0054', 919, phrase, 'MUST', ('activity.legacy_ui_stream',))
      for name, phrase in (('schema', 'schema'), ('semantics', 'semantics'), ('fixtures', 'fixtures'), ('checks', 'checks'))],
    ('stream-monotone-sequence', '0055', 958, 'monotonically increasing per (`streamId`, `laneId`)', 'MUST', ('activity.legacy_ui_stream',)),
    *[('stream-' + name, '0055', 959, phrase, 'MUST', ('activity.legacy_ui_stream',))
      for name, phrase in (('terminal', 'end in `final` or `error`'), ('timeout', 'time out'), ('recovery', 'surface recovery actions'))],
    *[('stream-' + name, '0055', 960, phrase, 'MUST', ('activity.legacy_ui_stream',))
      for name, phrase in (('kind', 'set `kind`'), ('matching-payload', 'only include the matching payload field'))],
    ('stream-append', '0055', 961, '`delta.mode = append`', 'MUST', ('activity.legacy_ui_stream', 'stream.text_surface')),
    ('stream-sparing-replace', '0055', 962, 'used sparingly', 'SHOULD', ('activity.legacy_ui_stream',)),
    ('stream-replace-no-jitter', '0055', 962, 'without jitter', 'SHOULD', ('activity.legacy_ui_stream', 'stream.uses_replace')),
    ('stream-progress', '0055', 963, 'emit `progress` frames when feasible', 'SHOULD', ('activity.legacy_ui_stream', 'pipeline.compute_bound', 'stream.progress_feasible')),
    ('stream-generic-working', '0055', 963, 'render a generic “Thinking/Working” state if progress is unavailable', 'MUST', ('activity.legacy_ui_stream', 'pipeline.compute_bound', 'stream.progress_unavailable')),
    ('tokens-canonical-versioned', '0056', 971, 'canonical, versioned contract surface', 'MUST', ('activity.shared_design_system',)),
    ('tokens-schema', '0056', 974, 'machine-readable schema', 'MUST', ('activity.shared_design_system',)),
    ('tokens-owner', '0056', 974, 'explicit owner', 'MUST', ('activity.shared_design_system',)),
    ('tokens-compatible-evolution', '0056', 975, 'Compatibility Mode semantics', 'MUST', ('activity.shared_design_system',)),
    *[('tokens-' + name, '0056', 977, phrase, 'MUST', ('activity.shared_design_system', 'change.token_behavioral'))
      for name, phrase in (('behavioral-review', 'explicit review'), ('visual-regression', 'visual regression checks'))],
    ('tokens-semantic-names', '0056', 979, 'semantic', 'MUST', ('activity.shared_design_system',)),
    ('tokens-stable-names', '0056', 979, 'stable', 'MUST', ('activity.shared_design_system',)),
    *[('tokens-' + name, '0056', 979, phrase, 'MUST', ('activity.shared_design_system', 'activity.temporary_token_experiment'))
      for name, phrase in (('incubator-namespace', 'documented **incubator namespace**'), ('incubator-owner', 'owner'), ('incubator-expiry', 'expiry date'))],
    ('tokens-frontend-ci', '0056', 980, 'forbid “magic” raw values where tokens exist', 'MUST', ('activity.frontend_using_shared_tokens',)),
    ('tokens-prototype-no-shared-leak', '0056', 981, 'leak into shared UI kit components or shared surfaces', 'MUST', ('profile.l0', 'activity.prototype_token_values')),
    *[('component-' + name, '0057', 985, phrase, 'SHOULD', ('activity.shared_ui_component',))
      for name, phrase in (('stable-id', 'stable identifiers'), ('props-events', 'documented props/events contracts'))],
    *[('component-' + name, '0057', line, phrase, 'MUST', ('activity.shared_ui_component', 'ui.kit_exists', 'ui.component_state_referenced'))
      for name, line, phrase in (('story', 987, 'Storybook story (or equivalent)'), ('visual-snapshots', 988, 'visual regression snapshots'))],
    ('component-compatible-evolution', '0057', 989, 'expand/contract, deprecations, and compatibility windows', 'SHOULD', ('activity.shared_ui_component',)),
)

# Scope includes the original heading/qualifier and list children, not an
# unrelated equal phrase. All references remain in the pinned original body.
CONTRACT_SCOPES = {
    '0031': (459, 474), '0033': (469, 474), '0034': (478, 484), '0035': (478, 486),
    '0036': (478, 502), '0037': (478, 502), '0038': (506, 516), '0039': (520, 520),
    '0040': (522, 539), '0041': (541, 556), '0042': (558, 577), '0043': (558, 577),
    '0044': (579, 596), '0045': (579, 654), '0046': (656, 658), '0047': (656, 688),
    '0048': (690, 699), '0049': (690, 772), '0050': (774, 834), '0051': (858, 915),
    '0052': (858, 915), '0053': (858, 915), '0054': (917, 963), '0055': (917, 963),
    '0056': (969, 981), '0057': (983, 989),
}


# Reviewed §7 algorithm obligations. Actual activity conditions do not encode
# permission or PASS. Whole scopes retain the tier policy, lawful adapter
# alternatives and safe migration choices; existing source remains normative.
ALGORITHM_LEAVES = (
    ('tier-master-doc', '0092', 1352, 'Master Doc', 'MUST', ('activity.algorithm_pipeline',)),
    ('tier-run-manifest', '0092', 1352, 'RunManifest', 'MUST', ('activity.algorithm_pipeline',)),
    *[(name, '0093', line, phrase, strength, ('activity.algorithm_pipeline',) + extra)
      for name, line, phrase, strength, extra in (
          ('replay-config', 1362, 'configuration', 'MUST', ('pipeline.tier_0_or_1',)),
          ('replay-dependency-pins', 1362, 'relevant dependency pins', 'MUST', ('pipeline.tier_0_or_1',)),
          ('replay-harness', 1363, 'replay harness', 'MUST', ('pipeline.tier_0_or_1',)),
          ('replay-golden-fixtures', 1363, 'golden fixtures', 'MUST', ('pipeline.tier_0_or_1',)),
          ('replay-ci', 1363, 'run in CI', 'MUST', ('pipeline.tier_0_or_1',)),
          ('invariant-assertions', 1364, 'invariant-based assertions', 'SHOULD', ()),
          ('stable-cassettes', 1365, 'tool outputs / retrieved documents / structured intermediate states', 'SHOULD', ('pipeline.uses_cassettes',)),
          ('higher-determinism', 1366, 'moving pipelines upward', 'SHOULD', ()))],
    ('accept-side-effects-mode', '0094', 1370, 'accept `sideEffectsMode`', 'MUST', ('activity.algorithm_execution',)),
    ('adapter-check-before-write', '0095', 1378, 'check `sideEffectsMode` before writing', 'MUST', ('activity.external_write_adapter',)),
    ('dry-run-read-only-or-fakes', '0095', 1379, 'read-only or use fakes/cassettes', 'MUST', ('activity.algorithm_adapter', 'side_effects.dry_run')),
    ('orchestrator-pass-mode', '0095', 1380, 'pass `sideEffectsMode` through', 'MUST', ('activity.algorithm_orchestration',)),
    ('pipeline-budget-policy', '0096', 1392, 'budget policy', 'MUST', ('activity.algorithm_pipeline',)),
    ('runtime-budget-enforcement', '0096', 1393, 'enforced at runtime', 'MUST', ('activity.algorithm_execution',)),
    ('hard-termination-code', '0096', 1394, 'stable `budget.termination.code`', 'MUST',
     ('activity.algorithm_execution', 'budget.limit_affects_execution', 'budget.hard_termination')),
    ('limit-diagnostic-code', '0096', 1394, 'diagnostics codes', 'MUST',
     ('activity.algorithm_execution', 'budget.limit_affects_execution')),
    *[(name, '0097', line, phrase, strength, ('activity.algorithm_run',) + extra)
      for name, line, phrase, strength, extra in (
          ('run-manifest', 1400, 'RunManifest', 'MUST', ()),
          ('pipeline-result', 1400, 'PipelineResult', 'MUST', ()),
          ('exact-manifest-pointer', 1401, 'exact RunManifest used', 'MUST', ()),
          ('lossless-job-wrapping', 1402, 'without lossy translation', 'MUST', ()),
          ('multi-stage-summary', 1403, 'Stage summaries', 'SHOULD', ('pipeline.multi_stage',)))],
    *[(name, '0098', line, phrase, 'MUST', ('change.algorithm_material',))
      for name, line, phrase in (
          ('material-change-evaluations', 1407, 'gated by evaluations'),
          ('evaluation-dataset-pin', 1408, 'pinned via DatasetManifest'),
          ('evaluation-report', 1409, 'summarized via EvalReport'),
          ('evaluation-artifacts', 1409, 'stored as artifacts'))],
    *[(name, '0099', line, phrase, 'MUST', ('activity.algorithm_repository',) + extra)
      for name, line, phrase, extra in (
          ('repo-boundary-checks', 1420, 'Boundary checks', ()),
          ('repo-core-unit-tests', 1421, 'Unit tests for core deterministic transforms', ()),
          ('repo-deterministic-eval', 1422, 'Deterministic CI eval suite', ()),
          ('repo-pinned-eval-split', 1422, 'pinned dataset split', ()),
          ('repo-tier-replay', 1423, 'Replay verification for Tier 0/Tier 1', ('repository.tier_0_or_1_pipelines',)))],
    ('slow-replay-full-tier', '0100', 1427, '`verify --full` tier', 'SHOULD',
     ('activity.algorithm_repository', 'pipeline.replay_slow')),
    ('critical-default-replay-smoke', '0100', 1427, 'minimal offline replay smoke', 'SHOULD',
     ('activity.algorithm_repository', 'pipeline.replay_slow', 'pipeline.critical_replay_paths')),
    ('large-refactor-safe-migration', '0101', 1431, 'safe migration patterns', 'MUST', ('change.large_algorithm_refactor',)),
)
ALGORITHM_SCOPES = {
    '0092': (1352, 1366), '0093': (1352, 1366), '0094': (1370, 1380),
    '0095': (1370, 1380), '0096': (1384, 1396), '0097': (1400, 1403),
    '0098': (1405, 1414), '0099': (1418, 1427), '0100': (1418, 1427), '0101': (1431, 1436),
}


# Original §9.7/§9.8 event-triggered duties, not a new review framework.
# Waiver metadata applies only to an actual adopted waiver; the obligation to
# resolve observed drift remains independently active. Lawful choices stay text.
DOCUMENTATION_LEAVES = (
    *[(name, '0118', line, phrase, 'MUST', ('activity.doc_drift_observed',) + extra)
      for name, line, phrase, extra in (
          ('drift-record-immediately', 1624, 'record it immediately', ()),
          ('drift-one-outcome', 1627, 'exactly one', ()),
          ('drift-decision-record', 1627, 'documenting the decision', ()),
          ('drift-external-compatibility', 1632, 'explicit compatibility plan', ('change.drift_external_or_persisted',)),
          ('drift-old-new-fixtures', 1633, 'fixtures for both old and new shapes', ('change.drift_external_or_persisted',)),
          ('drift-reproducing-gate', 1634, 'verification gates that reproduce the drift class', ('change.drift_external_or_persisted',)),
          ('drift-waiver-owner', 1635, 'owner', ('drift.not_fixed_in_current_pr', 'activity.doc_drift_waiver')),
          ('drift-waiver-scope', 1635, 'scope', ('drift.not_fixed_in_current_pr', 'activity.doc_drift_waiver')),
          ('drift-waiver-expiry', 1635, 'expiry', ('drift.not_fixed_in_current_pr', 'activity.doc_drift_waiver')))],
    ('api-inventory-automation', '0119', 1639, 'generate or validate API inventories', 'SHOULD', ('activity.api_contract_documentation',)),
    ('executable-contract-truth', '0119', 1640, 'primary executable source of truth', 'SHOULD', ('activity.cross_boundary_contract_work',)),
    ('l2-automated-drift-check', '0119', 1641, 'at least one automated drift check', 'MUST', ('profile.l2',)),
    ('l2-drift-ci', '0119', 1641, 'runs in CI', 'MUST', ('profile.l2',)),
    ('doc-owner', '0120', 1649, 'explicit **Owner**', 'MUST', ('activity.master_doc_set_doc',)),
    ('doc-approval-rule', '0120', 1649, 'review rule', 'MUST', ('activity.master_doc_set_doc',)),
    ('boundary-decision-owner', '0120', 1650, 'single **decision owner**', 'MUST', ('activity.cross_boundary_doc_section',)),
    ('doc-pr-flow', '0120', 1651, 'version control via PRs', 'MUST', ('activity.governed_doc_change',)),
    ('out-of-band-reconcile-or-noncanonical', '0120', 1651, 'reconciled back into the repo promptly or treated as non-canonical', 'MUST', ('activity.out_of_band_doc_edit',)),
    ('multi-party-rfc', '0120', 1652, 'lightweight RFC process', 'SHOULD', ('component.multi_company_program',)),
    ('dispute-decision-record', '0120', 1653, 'explicit decision record', 'MUST', ('activity.doc_dispute',)),
)
DOCUMENTATION_SCOPES = {'0118': (1618, 1635), '0119': (1637, 1641), '0120': (1643, 1655)}

# Preserve the rest of §9 as documentation duties, including lawful linked
# equivalents. An optional waiver or Context Pack is not made mandatory by a
# metadata duty, and a package does not acquire an invented UI profile.
DOCUMENTATION_LEAVES += (
    *[(name, '0103', line, phrase, 'MUST', ('activity.project_documentation',))
      for name, line, phrase in (
          ('master-doc-canonical', 1455, 'canonical Master Doc'),
          ('master-doc-versioned', 1455, 'versioned with code'),
          ('master-doc-reviewed', 1455, 'reviewed like code'),
          ('master-doc-readiness', 1457, 'Doc readiness gate'),
          ('master-doc-conformance', 1458, 'conformance profile'),
          ('master-doc-interaction', 1459, 'interaction profile'),
          ('master-doc-family-role', 1460, 'canonical_entrypoint'),
          ('master-doc-status', 1461, 'normative enum'),
          ('master-doc-standard', 1462, 'governing standard reference'),
          ('master-doc-product-scope', 1463, 'product scope and constraints'),
          ('master-doc-topology', 1464, 'system topology'),
          ('master-doc-contract-hub', 1464, 'contract hub location'),
          ('master-doc-contract-surfaces', 1465, 'contract surfaces and owners'),
          ('master-doc-contract-inventory', 1466, 'Contract Inventory Index'),
          ('master-doc-requirement-trace', 1468, 'requirements → contracts → tests/gates'),
          ('master-doc-ui-trace', 1469, 'UI workflows → routes/jobs → run/pipeline artifacts'),
          ('master-doc-verify', 1470, 'verification gates and exact `verify` commands'),
          ('master-doc-execution-plan', 1471, 'tasks with acceptance criteria and test evidence'))],
    ('master-doc-machine-section-model', '0104', 1473, 'required-section model', 'SHOULD', ('activity.master_doc_machine_checks',)),
    ('master-doc-machine-readiness-model', '0104', 1473, 'required-subsection model', 'SHOULD', ('activity.master_doc_machine_checks',)),
    ('material-change-doc-or-waiver', '0105', 1477, 'update the Master Doc (or include a documented waiver with owner + expiry)', 'MUST', ('change.doc_material',)),
    ('l0-concise-master-doc', '0105', 1479, 'remain short and focus on critical flows and risks', 'SHOULD', ('profile.l0',)),
    *[('sub-doc-' + name, '0107', line, phrase, 'MUST', ('activity.governed_subordinate_doc',))
      for name, line, phrase in (
          ('control-header', 1489, 'Document Control'), ('id', 1490, 'Doc ID'),
          ('owner', 1491, 'Owner'), ('status', 1492, 'Status'),
          ('standard', 1493, 'Governing standard'), ('updated', 1494, 'Last updated'),
          ('scope', 1495, 'Scope'), ('canonical-owner-key', 1496, 'canonical minimum metadata key'),
          ('status-enum', 1498, 'normative status enum'))],
    ('sub-doc-canonical-link', '0107', 1497, 'point back to the canonical Master Doc', 'MUST', ('activity.governed_subordinate_doc', 'document.defines_behavior')),
    ('sub-doc-na-reason', '0107', 1499, 'why', 'MUST', ('activity.governed_subordinate_doc', 'document.declared_not_applicable')),
    ('sub-doc-na-truth', '0107', 1499, 'where the governing truth lives instead', 'MUST', ('activity.governed_subordinate_doc', 'document.declared_not_applicable')),
    ('sub-doc-minimal', '0107', 1500, 'structurally minimal', 'SHOULD', ('activity.governed_subordinate_doc',)),
    ('sub-doc-templates', '0107', 1501, 'Appendix M', 'SHOULD', ('activity.governed_subordinate_doc',)),
    ('official-template-metadata', '0107', 1502, 'metadata and section rules', 'MUST', ('activity.standard_template_publication',)),
    *[('ui-spec-' + name, '0108', line, phrase, 'MUST', ('activity.user_facing_ui',) + extra)
      for name, line, phrase, extra in (
          ('appendix', 1521, 'UI Spec Appendix', ()),
          ('screen-route-ids', 1523, 'stable Screen IDs and Route IDs', ()),
          ('standard-states', 1524, 'Loading/Empty/Ready/Error/Permission', ()),
          ('ai-states', 1524, 'Thinking/Streaming/Repair', ('ui.ai_states_applicable',)),
          ('traceability', 1525, 'workflow-to-screen-to-contract traceability', ()),
          ('selectors', 1526, 'stable test selectors', ()),
          ('interaction-mode', 1527, 'AI interaction mode per screen', ()),
          ('ai-contract-references', 1527, 'referenced contracts when applicable', ('ui.ai_contracts_consumed',)),
          ('shared-design-references', 1528, 'design system contract references', ('ui.shared_surface',)))],
    ('headless-note-or-mapped-equivalent', '0109', 1532, 'Headless Surface Note', 'MUST', ('profile.headless',)),
    ('headless-pointer-governing-link', '0109', 1533, 'point to the governing Headless Surface Note', 'MUST', ('profile.headless', 'activity.headless_pointer_doc')),
    ('headless-pointer-not-substantive', '0109', 1533, 'MUST NOT be treated as the substantive headless interaction spec', 'MUST', ('profile.headless', 'activity.headless_pointer_doc')),
    ('headless-no-silent-skip', '0109', 1534, 'silently skip UI-spec governance', 'MUST', ('profile.headless',)),
    ('automatable-design-review-gate', '0110', 1539, 'enforced in the frontend `verify` gate', 'SHOULD', ('activity.user_facing_ui', 'review.automatable_items')),
    ('module-master-doc', '0112', 1547, 'own module-level MASTER_DOC (or an equivalent doc-family member)', 'MUST', ('activity.module_work',)),
    ('module-kind', '0112', 1552, 'Module kind', 'MUST', ('activity.module_doc',)),
    ('module-doc-role', '0112', 1553, 'module_doc', 'MUST', ('activity.module_doc',)),
    ('worker-service-interaction', '0112', 1554, 'explicit `Interaction profile`', 'MUST', ('activity.worker_or_service_doc',)),
    ('worker-service-headless', '0112', 1555, 'MUST be `headless`', 'MUST', ('activity.worker_or_service_doc', 'module.no_primary_end_user_ui')),
    ('worker-service-surfaces', '0112', 1555, 'operator/API/job/runtime surfaces', 'MUST', ('activity.worker_or_service_doc', 'module.no_primary_end_user_ui')),
    ('package-no-fake-profile', '0112', 1557, 'MUST NOT be forced to invent a fake interaction profile', 'MUST', ('activity.pure_package_library_tooling_doc',)),
    ('package-na-profile-explicit', '0112', 1557, 'say so explicitly outside the project-level interaction-profile enum', 'MUST', ('activity.pure_package_library_tooling_doc', 'module.interaction_not_applicable')),
    ('module-determinism-applicability', '0112', 1558, 'whether determinism is applicable', 'MUST', ('activity.module_doc',)),
    ('module-determinism-section', '0112', 1559, 'Determinism', 'MUST', ('activity.module_doc', 'module.evidence_or_deterministic_logic')),
    ('module-na-determinism-reason', '0112', 1566, 'one-line reason', 'MUST', ('activity.static_style_or_type_only_package', 'module.determinism_declared_not_applicable')),
    ('module-no-half-governance', '0112', 1567, 'structurally exempt', 'MUST', ('activity.module_work',)),
    ('module-doc-template', '0112', 1568, 'Appendix M', 'SHOULD', ('activity.module_doc',)),
    ('traceability-automation', '0113', 1572, 'automate where feasible', 'SHOULD', ('activity.project_documentation',)),
    ('manual-traceability-focus', '0114', 1579, 'minimal and focused on critical workflows and externally observed/persisted surfaces', 'MUST', ('activity.project_documentation', 'traceability.not_automated')),
    ('manual-traceability-owner', '0114', 1580, 'Assign an owner', 'MUST', ('activity.project_documentation', 'traceability.not_automated')),
    ('manual-traceability-review', '0114', 1580, 'at least once per release milestone', 'MUST', ('activity.project_documentation', 'traceability.not_automated')),
    ('one-master-doc-entrypoint', '0115', 1588, 'exactly **one canonical Master Doc entrypoint**', 'MUST', ('activity.project_documentation',)),
    *[('delegated-index-' + name, '0115', line, phrase, 'MUST', ('activity.master_doc_delegation',))
      for name, line, phrase in (
          ('no-link-farm', 1590, 'MUST NOT create a “link farm'),
          ('profiles', 1591, 'conformance profile + interaction profile declarations'),
          ('topology-hub', 1592, 'topology summary and contract hub location'),
          ('contract-inventory', 1593, 'Contract Inventory Index (or a single authoritative link to it)'),
          ('traceability', 1594, 'Traceability Index (or a single authoritative link to it)'),
          ('verify', 1595, 'canonical `verify` commands'),
          ('execution-plan', 1596, 'task list + acceptance criteria'))],
    ('sub-doc-mini-header', '0115', 1597, 'mini **Document Control** header', 'SHOULD', ('activity.governed_subordinate_doc',)),
    ('doc-context-budget', '0115', 1598, 'practical model context budget', 'SHOULD', ('activity.project_documentation',)),
    ('context-pack-small', '0116', 1602, 'kept intentionally small', 'SHOULD', ('activity.project_documentation',)),
    ('context-pack-l2-current', '0116', 1609, 'updated in the same PR when changing workflows/contracts/gates', 'MUST', ('profile.l2', 'change.context_pack_material')),
    *[('doc-verify-' + name, '0117', line, phrase, 'SHOULD', ('activity.repository_verification',))
      for name, line, phrase in (('links', 1614, 'broken relative links'),
                                ('metadata', 1615, 'missing required Document Control fields'),
                                ('unique-ids', 1616, 'duplicate IDs'))],
)
DOCUMENTATION_SCOPES.update({
    '0103': (1455, 1471), '0104': (1473, 1473), '0105': (1475, 1479),
    '0107': (1489, 1517), '0108': (1521, 1528), '0109': (1530, 1534),
    '0110': (1536, 1539), '0112': (1547, 1568), '0113': (1572, 1575),
    '0114': (1577, 1580), '0115': (1588, 1598), '0116': (1600, 1609),
    '0117': (1613, 1616),
})

# §6 is an interaction track, not proof that a UI was exercised. Preserve the
# actual screen/repository/activity predicates and original cost-control modes.
UI_LEAVES = (
    ('feature-no-deep-imports', '0068', 1118, 'deep-import from other', 'MUST', ('activity.frontend_feature_module',)),
    ('kit-no-feature-imports', '0068', 1119, 'import from `features/*`', 'MUST', ('activity.ui_kit',)),
    ('feature-public-exports', '0068', 1120, 'feature API', 'SHOULD', ('activity.frontend_feature_module',)),
    *[(name, '0069', line, phrase, 'MUST', ('activity.frontend_module',))
      for name, line, phrase in (('no-import-environment', 1133, 'read environment/config at import time'),
                                ('no-implicit-routes', 1134, 'register routes implicitly'),
                                ('no-global-singletons', 1135, 'instantiate global singletons outside the app shell'))],
    *[('feature-' + name, '0070', line, phrase, 'MUST', ('activity.frontend_feature_module',))
      for name, line, phrase in (('public-api', 1141, 'stable feature-level public API'),
                                ('states', 1142, 'explicit states'),
                                ('happy-test', 1143, 'one critical happy path'),
                                ('failure-test', 1143, 'one failure path'))],
    ('feature-contract-map', '0071', 1147, 'contract map', 'SHOULD', ('activity.frontend_feature_module',)),
    ('feature-test-selectors', '0071', 1148, 'stable test selectors', 'SHOULD', ('activity.frontend_feature_module',)),
    *[('kit-' + name, '0072', line, phrase, strength, ('activity.ui_kit',))
      for name, line, phrase, strength in (
          ('generic', 1154, 'generic and do not encode product workflows', 'MUST'),
          ('no-network', 1155, 'MUST NOT call backend APIs directly', 'MUST'),
          ('canonical-tokens', 1156, 'canonical token contract', 'MUST'),
          ('storybook', 1157, 'publish Storybook (or equivalent)', 'MUST'),
          ('stories-canonical', 1157, 'canonical visual contract', 'MUST'),
          ('stable-identifiers', 1158, 'stable identifiers', 'SHOULD'),
          ('props-events', 1158, 'documented props/events', 'SHOULD'),
          ('compatible-evolution', 1158, 'expand/contract + deprecation windows', 'SHOULD'))],
    ('repo-canonical-verify', '0073', 1162, 'single `verify` entrypoint', 'MUST', ('activity.frontend_repository',)),
    ('repo-local-ci-verify', '0073', 1162, 'runs locally and in CI', 'MUST', ('activity.frontend_repository',)),
    ('verify-review-loop-fast', '0074', 1166, 'review-loop fast', 'MUST', ('activity.frontend_repository',)),
    ('verify-deterministic', '0074', 1166, 'deterministic', 'MUST', ('activity.frontend_repository',)),
    ('slow-full-mode', '0074', 1167, 'full mode', 'SHOULD', ('activity.frontend_repository', 'ui.slow_e2e_or_visual')),
    *[('default-gate-' + name, '0075', line, phrase, 'MUST', ('activity.frontend_repository',))
      for name, line, phrase in (
          ('boundary', 1171, 'Boundary lint'), ('unit', 1172, 'Unit tests'),
          ('types-lint', 1173, 'Type/lint'), ('smoke', 1174, 'E2E smoke tests'),
          ('smoke-selectors', 1174, 'stable selectors'))],
    ('smoke-deterministic-dependencies', '0075', 1174, 'deterministic/stubbed dependencies whenever feasible', 'SHOULD', ('activity.frontend_repository',)),
    ('token-enforcement', '0076', 1178, 'Token enforcement', 'MUST', ('activity.frontend_repository',)),
    ('kit-state-snapshots', '0076', 1179, 'states referenced by the UI Spec Appendix MUST be snapshotted', 'MUST', ('activity.ui_kit', 'ui.component_state_referenced')),
    ('kit-snapshot-pr', '0076', 1179, 'Running these snapshots in PR gates is RECOMMENDED when UI kit code changes', 'SHOULD', ('activity.ui_kit', 'change.ui_kit_code')),
    ('accessibility-gate', '0076', 1180, 'Accessibility gate', 'SHOULD', ('activity.frontend_repository',)),
    ('ai-contract-rendering-tests', '0076', 1181, 'AI-specific contracts consumed by the UI', 'SHOULD', ('activity.frontend_repository', 'ui.ai_contracts_consumed')),
    ('trust-screen-visual-tests', '0076', 1182, 'critical “trust” surfaces', 'SHOULD', ('activity.frontend_repository', 'ui.trust_surface')),
    ('design-code-traceability', '0077', 1186, 'Design-to-code traceability check', 'SHOULD', ('activity.frontend_repository',)),
    ('ai-distinct-thinking', '0078', 1199, 'distinct “Thinking/Working” state', 'MUST', ('activity.ai_ui_flow', 'pipeline.compute_bound')),
    ('ai-progress-frames', '0078', 1200, 'structured progress frames', 'SHOULD', ('activity.ai_ui_flow', 'pipeline.compute_exceeds_two_seconds')),
    ('ai-generic-thinking', '0078', 1200, 'generic Thinking state after an appropriate threshold', 'MUST', ('activity.ai_ui_flow', 'pipeline.compute_bound', 'stream.progress_unavailable')),
    *[('stream-' + name, '0079', line, phrase, strength, ('activity.ui_stream_screen',))
      for name, line, phrase, strength in (
          ('contract', 1206, 'StreamFrame', 'MUST'), ('fixtures', 1206, 'fixture-backed', 'MUST'),
          ('scroll', 1207, 'scroll anchoring', 'MUST'), ('selection', 1207, 'selection stability', 'MUST'),
          ('cancel', 1207, 'ability to cancel/stop generation', 'MUST'),
          ('partial-final', 1208, 'partial vs final states explicitly', 'MUST'),
          ('prefer-append', 1209, 'Prefer `delta.mode = append`', 'SHOULD'),
          ('replace-documented', 1209, 'only when the UI Spec explicitly calls it out', 'SHOULD'))],
    ('recovery-actions', '0080', 1215, 'user-facing recovery actions', 'MUST', ('activity.ai_ui_flow', 'ui.meaningful_failure_recovery')),
    ('recovery-stable-errors', '0080', 1215, 'stable error identifiers', 'MUST', ('activity.ai_ui_flow', 'ui.meaningful_failure_recovery')),
    ('repair-ux', '0080', 1216, 'repair', 'SHOULD', ('activity.ai_ui_flow', 'ui.minimal_fix_available')),
    ('optimistic-reversible-action', '0081', 1222, 'apply the change optimistically and roll back on error', 'SHOULD', ('activity.low_risk_reversible_ui_action',)),
    ('optimistic-rollback', '0081', 1223, 'implement rollback correctly', 'MUST', ('activity.low_risk_reversible_ui_action', 'ui.optimistic_update_used')),
    ('optimistic-safe-error', '0081', 1223, 'user-safe error messaging', 'MUST', ('activity.low_risk_reversible_ui_action', 'ui.optimistic_update_used')),
    ('reversible-backend-idempotency', '0081', 1224, 'idempotency', 'MUST', ('activity.low_risk_reversible_ui_action',)),
    ('reversible-backend-stable-errors', '0081', 1224, 'stable error codes', 'MUST', ('activity.low_risk_reversible_ui_action',)),
    *[('citation-' + name, '0082', line, phrase, strength, ('activity.ui_citation_rendering',))
      for name, line, phrase, strength in (
          ('structured-contract', 1230, 'AnnotatedContent/CitationSet', 'MUST'),
          ('integrity', 1230, 'integrity.status', 'MUST'),
          ('specified-interactions', 1231, 'UI interactions for citations MUST be specified', 'MUST'),
          ('accessible', 1231, 'keyboard + screen readers', 'MUST'),
          ('graceful-missing-invalid', 1232, 'degrade gracefully when citations are missing/invalid', 'SHOULD'))],
)
UI_SCOPES = {
    '0068': (1116, 1120), '0069': (1122, 1135), '0070': (1139, 1143),
    '0071': (1145, 1148), '0072': (1152, 1158), '0073': (1162, 1186),
    '0074': (1164, 1186), '0075': (1169, 1186), '0076': (1176, 1182),
    '0077': (1184, 1186), '0078': (1192, 1200), '0079': (1202, 1209),
    '0080': (1211, 1216), '0081': (1218, 1224), '0082': (1226, 1232),
}

HFVI_LEAVES = (
    ('maintain-ui-appendix', '0083', 1240, 'continue to maintain Appendix D', 'MUST', ('profile.hfvi',)),
    ('declare-profile', '0084', 1244, 'hfvi_canvas_webgl_game', 'MUST', ('activity.hfvi_product_surface',)),
    ('identify-rendering-engines', '0084', 1245, 'concrete rendering engine(s) and libraries', 'SHOULD', ('profile.hfvi',)),
    ('surface-vis', '0085', 1249, 'Appendix K', 'MUST', ('profile.hfvi',)),
    ('ui-vis-scene-links', '0085', 1250, 'VIS Scene IDs', 'MUST', ('profile.hfvi', 'activity.hfvi_screen')),
    *[('vis-' + name, '0085', line, phrase, 'MUST', ('profile.hfvi',))
      for name, line, phrase in (
          ('coordinates', 1254, 'coordinate system and transforms'), ('layers', 1255, 'layer/z-order rules'),
          ('input', 1256, 'input model'), ('invariants', 1257, 'visual aggregates and invariants'),
          ('technical-component-table', 1258, 'visual component spec table'),
          ('motion-tokens', 1259, 'motion tokens referenced'), ('debug-overlay', 1260, 'debug overlay contract'),
          ('verification', 1261, 'verification mapping to replay cassettes and visual baselines'))],
    ('technical-anchors', '0086', 1265, 'library-level technical anchors', 'MUST', ('profile.hfvi',)),
    ('glossary', '0086', 1266, 'project glossary', 'SHOULD', ('profile.hfvi',)),
    ('no-hardcoded-motion', '0087', 1270, 'MUST NOT hardcode motion parameters', 'MUST', ('profile.hfvi',)),
    ('motion-token-expression', '0087', 1271, 'expressed via motion tokens', 'MUST', ('profile.hfvi',)),
    ('motion-stable-ids', '0087', 1271, 'referenced by stable IDs', 'MUST', ('profile.hfvi',)),
    ('prototype-motion-bounds', '0087', 1272, 'explicitly bounded prototype namespace', 'MUST', ('profile.hfvi', 'profile.l0', 'activity.prototype_motion_values')),
    ('prototype-motion-owner', '0087', 1272, 'owner', 'MUST', ('profile.hfvi', 'profile.l0', 'activity.prototype_motion_values')),
    ('prototype-motion-expiry', '0087', 1272, 'expiry', 'MUST', ('profile.hfvi', 'profile.l0', 'activity.prototype_motion_values')),
    *[('debug-' + name, '0088', 1276, phrase, 'MUST', ('profile.hfvi', 'activity.hfvi_component'))
      for name, phrase in (('mode', 'debug overlay mode'), ('hit-areas', 'hit areas'),
                           ('boxes', 'bounding boxes'), ('anchors', 'anchor points'), ('vectors', 'key vectors'))],
    ('debug-explicit-invariants', '0088', 1277, 'explicit invariants', 'SHOULD', ('profile.hfvi', 'activity.hfvi_visual_aggregate')),
    ('debug-validate-invariants', '0088', 1277, 'validate them in debug mode', 'SHOULD', ('profile.hfvi', 'activity.hfvi_visual_aggregate')),
    *[(name, '0089', line, phrase, strength, ('profile.hfvi', 'activity.frontend_repository'))
      for name, line, phrase, strength in (
          ('visual-gate', 1283, 'visual verification gate', 'MUST'),
          ('deterministic-input-replay', 1284, 'deterministic input replay', 'MUST'),
          ('key-frame-screenshots', 1284, 'screenshot baselines for key frames', 'MUST'),
          ('invariants-plus-diffs', 1285, 'invariant assertions', 'SHOULD'),
          ('minimal-fast-replay', 1286, 'minimal cassette set', 'SHOULD'),
          ('broader-full-visual', 1286, 'broader visual suites', 'SHOULD'))],
    *[('task-' + name, '0090', line, phrase, 'MUST', ('profile.hfvi', 'activity.hfvi_task'))
      for name, line, phrase in (('scene-component-refs', 1292, 'Scene/VC IDs'),
                                ('technical-anchors', 1293, 'technical anchors'),
                                ('replay-cassettes', 1294, 'replay cassette(s)'),
                                ('baseline-policy', 1295, 'visual baseline update policy'))],
    ('schema-before-code', '0091', 1299, 'before generating implementation code', 'MUST', ('profile.hfvi', 'activity.hfvi_task')),
    ('constructor-event-replay-sequence', '0091', 1300, 'pure constructors first', 'SHOULD', ('profile.hfvi', 'activity.hfvi_task')),
)
# Keep §6.8's declared-profile qualifier and the complete bounded L0 alternative
# in every HFVI leaf. Shared reading views deduplicate the exact source scope.
HFVI_SCOPES = {str(number).zfill(4): (1236, 1300) for number in range(83, 92)}

# Inherited force for list children, and the few mixed-force lines. Keeping the
# complete prohibition token matters when a line also includes positive duties.
INTERACTION_FORCE = {
    **{name: (1131, 'MUST NOT') for name in ('no-import-environment', 'no-implicit-routes', 'no-global-singletons')},
    **{'feature-' + name: (1139, 'MUST') for name in ('public-api', 'states', 'happy-test', 'failure-test')},
    'feature-contract-map': (1145, 'SHOULD'), 'feature-test-selectors': (1145, 'SHOULD'),
    **{'default-gate-' + name: (1169, 'Minimum required gates') for name in ('boundary', 'unit', 'types-lint', 'smoke')},
    'kit-snapshot-pr': (1179, 'RECOMMENDED'),
    **{'vis-' + name: (1252, 'Minimum VIS coverage') for name in ('coordinates', 'layers', 'input', 'invariants', 'technical-component-table', 'motion-tokens', 'debug-overlay', 'verification')},
    **{'prototype-motion-' + name: (1272, 'only inside') for name in ('bounds', 'owner', 'expiry')},
    **{'task-' + name: (1290, 'MUST') for name in ('scene-component-refs', 'technical-anchors', 'replay-cassettes', 'baseline-policy')},
}
DOCUMENTATION_FORCE = {
    **{name: (1455, 'MUST') for name, suffix, *_ in DOCUMENTATION_LEAVES if suffix == '0103'},
    **{name: (1489, 'MUST') for name, suffix, line, *_ in DOCUMENTATION_LEAVES if suffix == '0107' and 1490 <= line <= 1495},
    **{name: (1521, 'MUST') for name, suffix, *_ in DOCUMENTATION_LEAVES if suffix == '0108'},
    'headless-pointer-governing-link': (1533, 'MUST point'),
    'package-na-profile-explicit': (1557, 'MUST say'),
    **{'delegated-index-' + name: (1590, 'MUST still contain') for name in ('profiles', 'topology-hub', 'contract-inventory', 'traceability', 'verify', 'execution-plan')},
    **{'doc-verify-' + name: (1613, 'SHOULD') for name in ('links', 'metadata', 'unique-ids')},
}

# §10 defines evidence/report semantics independently of any current test PASS.
# Optional full/report/lock representations keep SHOULD; adopting them activates
# their mandatory minima. Reporting a state does not establish qualification.
VERIFICATION_LEAVES = (
    ('one-canonical-entrypoint', '0121', 1661, 'single canonical entrypoint', 'MUST', ('activity.repository_verification',)),
    ('canonical-local-ci-gate', '0122', 1663, 'canonical local and CI gate', 'MUST', ('activity.repository_verification',)),
    ('deterministic-verify', '0122', 1664, 'deterministic', 'MUST', ('activity.repository_verification',)),
    ('fail-fast-boundary-contract', '0122', 1664, 'fail fast on boundary / contract violations', 'MUST', ('activity.repository_verification',)),
    ('two-standard-modes', '0123', 1666, 'two standard modes', 'MUST', ('activity.repository_verification',)),
    ('default-fast-mode', '0124', 1669, 'correspond to “fast mode”', 'MUST', ('activity.repository_verification',)),
    ('fast-five-minute-target', '0124', 1670, '< 5 minutes', 'SHOULD', ('activity.repository_verification',)),
    *[('fast-' + name, '0124', 1671, phrase, 'MUST', ('activity.repository_verification',))
      for name, phrase in (('format-lint-type', 'formatting/lint/type checks'), ('boundary', 'boundary checks'),
                           ('contracts', 'contract validation (changed surfaces)'), ('doc-metadata', 'document metadata gates'),
                           ('smoke', 'minimal smoke test set'))],
    ('fast-hermetic-or-documented-stubs', '0124', 1672, 'MUST NOT require external, non-hermetic dependencies unless explicitly documented and stubbed', 'MUST', ('activity.repository_verification',)),
    ('provide-full-gate', '0125', 1675, 'full gate', 'SHOULD', ('activity.repository_verification',)),
    ('default-documentation', '0126', 1681, 'well-defined and documented in the Master Doc', 'MUST', ('activity.repository_verification',)),
    ('convenience-wrappers', '0126', 1682, 'convenience wrappers', 'SHOULD', ('activity.repository_verification',)),
    *[('output-' + name, '0126', 1683, phrase, 'MUST', ('activity.repository_verification',))
      for name, phrase in (('mode', 'mode'), ('build', 'git SHA/build ID'),
                           ('tool-pins', 'pinned tool versions'), ('standard-manifest', 'standardManifestVersion'))],
    ('declare-one-cadence', '0127', 1696, 'exactly one **gate cadence**', 'SHOULD', ('activity.governed_gate_or_report',)),
    ('pr-correctness', '0128', 1707, 'Catch explicit correctness failures', 'MUST', ('activity.pr_blocking_gate',)),
    ('post-merge-aggregate-audits', '0129', 1711, 'aggregate audits', 'SHOULD', ('activity.post_merge_gate',)),
    ('nightly-deep-checks', '0130', 1715, 'slow, deep, or trend-oriented checks', 'SHOULD', ('activity.nightly_gate',)),
    ('pre-release-parity', '0131', 1719, 'release-surface parity', 'MUST', ('activity.pre_release_gate',)),
    ('pre-release-closure', '0131', 1719, 'closure before promotion', 'MUST', ('activity.pre_release_gate',)),
    ('document-implemented-cadences', '0132', 1728, 'Master Doc, a repo-local verify registry, or an equivalent governed artifact', 'MUST', ('activity.repository_verification',)),
    ('no-report-as-blocking-gate', '0132', 1729, 'MUST NOT be presented as equivalent to PR-blocking conformance gates', 'MUST', ('activity.report_or_migration_tool',)),
    ('aggregate-cadence-metadata', '0132', 1730, 'aggregate cadence metadata', 'SHOULD', ('activity.suite_verification',)),
    ('publish-cadence-enforcement-definitions', '0132', 1731, 'cadence and enforcement definitions', 'SHOULD', ('activity.governed_verification_manifest',)),
    ('registry-publication', '0133', 1735, 'publish a machine-readable **verify registry**', 'MUST', ('activity.repository_verification', 'repository.multiple_or_distinct_governed_gates')),
    ('registry-schema-validation', '0133', 1735, 'validated against `verify_registry.schema.json`', 'MUST', ('activity.repository_verification', 'repository.multiple_or_distinct_governed_gates')),
    *[('registry-' + name, '0134', line, phrase, 'MUST', ('activity.governed_gate_entry',))
      for name, line, phrase in (
          ('gate-id', 1739, 'gateId'), ('kind', 1740, 'kind'), ('cadence', 1741, 'cadence'),
          ('enforcement', 1742, 'enforcementClass'), ('command', 1743, 'command'),
          ('owner', 1744, 'owner/maintainer information'), ('scope', 1745, 'scope / touched-surface expectations'),
          ('no-result-policy', 1746, 'failureOnNoResults'))],
    ('registry-expected-artifacts', '0134', 1747, 'expected artifact classes or refs', 'MUST', ('activity.governed_gate_entry', 'gate.governed_output_expected')),
    ('read-registry-metadata', '0135', 1751, 'read verify-registry metadata', 'SHOULD', ('activity.suite_or_dashboard_verification',)),
    ('no-unregistered-governed-claim', '0135', 1752, 'MUST NOT claim that a gate is governed if it is omitted', 'MUST', ('activity.repository_verification', 'repository.registry_backed_governed_gates')),
    ('commit-registry', '0135', 1753, 'committed `verify_registry.json` (or schema-equivalent serialization)', 'SHOULD', ('activity.repository_verification',)),
    ('emit-machine-report', '0136', 1757, 'machine-readable **verify report** validated against `verify_report.schema.json`', 'SHOULD', ('activity.governed_verify_run',)),
    *[('report-' + name, '0137', 1761, phrase, 'MUST', ('activity.governed_verify_report',))
      for name, phrase in (('mode', 'mode'), ('build', 'build ref / repo SHA'),
                           ('standard-manifest', 'standardManifestVersion'), ('tool-pins', 'toolchain pins'),
                           ('start-end', 'start/end time'), ('gate-outcomes', 'per-gate outcomes'))],
    ('report-explicit-not-run', '0137', 1762, 'represented explicitly as `not_run` or `error`', 'MUST', ('activity.governed_verify_report',)),
    ('report-no-disappearing-gates', '0137', 1762, 'MUST NOT disappear from the report', 'MUST', ('activity.governed_verify_report',)),
    ('report-no-results-fails', '0137', 1763, 'explicit failing outcome rather than a synthetic PASS summary', 'MUST', ('activity.governed_verify_report', 'gate.failure_on_no_results', 'gate.blocking_or_source_of_truth')),
    ('report-no-empty-pass', '0137', 1764, 'MUST NOT summarize overall PASS when every expected gate is skipped / not-run', 'MUST', ('activity.governed_verify_report',)),
    ('report-linked-artifacts', '0137', 1765, 'link to artifact refs', 'SHOULD', ('activity.governed_verify_report',)),
    ('merge-test-stability', '0138', 1769, 'Tests that gate merges MUST be stable', 'MUST', ('activity.merge_gating_test',)),
    ('flaky-quarantine', '0138', 1769, 'quarantined with an owner and a plan', 'MUST', ('activity.merge_gating_test', 'test.flaky')),
    ('deterministic-substitutes', '0138', 1770, 'deterministic substitutes', 'SHOULD', ('activity.ci_verification',)),
    ('expected-output-not-run-fails', '0138', 1771, 'explicit failure for gates that are expected to produce governed output', 'MUST', ('activity.governed_output_gate',)),
    ('hermetic-pinned-environment', '0139', 1779, 'hermetic environment (container or equivalent) that pins tool versions', 'MUST', ('activity.repository_verification',)),
    ('reproducible-tooling-lock', '0139', 1780, 'reproduce the exact toolchain used by CI', 'MUST', ('activity.repository_verification',)),
    ('standalone-tooling-lock-schema', '0139', 1781, 'validate against `tooling_lock.schema.json`', 'SHOULD', ('activity.standalone_tooling_lock',)),
    ('no-floating-ci-tools', '0139', 1782, 'MUST NOT depend on floating tool tags', 'MUST', ('activity.ci_verification',)),
    ('gate-enforcement-class', '0139', 1783, 'enforcement class', 'MUST', ('activity.governed_gate_or_check',)),
    ('distinguish-collection-enforcement', '0139', 1787, 'distinguish “metadata collection” from “enforcement”', 'MUST', ('activity.repository_or_suite_verification',)),
    ('no-collection-as-enforcement', '0139', 1787, 'MUST NOT be counted as a passing enforcement gate unless', 'MUST', ('activity.metadata_collection_check',)),
    *[('mirror-' + name, '0139', 1788, phrase, 'MUST', ('activity.governed_artifact_mirror',))
      for name, phrase in (('declared', 'declared as a **mirror**'), ('ssot', 'source-of-truth ref'),
                           ('purpose', 'mirror purpose'), ('no-local-edits-or-extension', 'localModificationsAllowed=false` unless the divergence is governed as an explicit extension'))],
    ('verify-machine-summary', '0139', 1789, 'machine-readable summary', 'SHOULD', ('activity.repository_verification',)),
    ('high-stakes-verifier-self-tests', '0139', 1790, 'self-tests (pass-case + fail-case)', 'SHOULD', ('activity.regulated_or_high_stakes_verification',)),
    ('suite-lock', '0140', 1798, 'machine-readable **suite lock**', 'MUST', ('activity.multi_versioned_module_suite',)),
    ('suite-lock-schema', '0140', 1798, 'validated against `suite_lock.schema.json`', 'MUST', ('activity.multi_versioned_module_suite',)),
    *[('suite-lock-' + name, '0140', line, phrase, 'MUST', ('activity.multi_versioned_module_suite',))
      for name, line, phrase in (('modules', 1800, 'governed modules'), ('repo-role', 1801, 'primary repo role'),
                                ('refs', 1802, 'locked refs'), ('override-policy', 1803, 'override policy'),
                                ('state-model', 1804, 'allowed local state model'))],
    ('critical-locked-sync-default', '0140', 1805, 'Locked sync MUST be the default', 'MUST', ('activity.release_or_adoption_critical_sync',)),
    ('critical-no-clone-tip', '0140', 1805, 'MUST NOT use clone-tip / floating HEAD', 'MUST', ('activity.release_or_adoption_critical_sync',)),
    ('suite-module-state-report', '0140', 1806, 'module-state report derived from the suite lock', 'SHOULD', ('activity.multi_versioned_module_suite',)),
    ('version-closure-manifest', '0141', 1820, 'machine-readable **version closure manifest**', 'MUST', ('activity.separately_versioned_component_workflow',)),
    ('version-closure-schema', '0141', 1820, 'validated against `suite_version_closure.schema.json`', 'MUST', ('activity.separately_versioned_component_workflow',)),
    *[('closure-' + name, '0141', line, phrase, 'MUST', ('activity.separately_versioned_component_workflow',) + extra)
      for name, line, phrase, extra in (
          ('standard-version', 1822, 'standardVersion', ()), ('manifest-version', 1823, 'standardManifestVersion', ()),
          ('suite-version', 1824, 'suiteVersion', ()), ('factory-version', 1825, 'factoryVersion', ()),
          ('verify-runtime-version', 1826, 'verifyRuntimeVersion', ()),
          ('policy-pack-version', 1827, 'policyPackVersion', ('suite.policy_pack_applicable',)),
          ('template-version', 1828, 'generatorTemplateVersion', ('suite.generator_template_applicable',)),
          ('suite-lock-ref', 1829, 'suiteLockRef', ()), ('ci-release-pins', 1830, 'exact refs/digests', ()))],
    ('release-tool-no-floating-source', '0141', 1831, 'MUST NOT clone “latest tip” / unpinned HEAD', 'MUST', ('activity.release_critical_tooling',)),
    ('closure-structured-pins', '0141', 1832, 'structured pinned refs', 'MUST', ('activity.release_or_adoption_closure',)),
    ('closure-no-bare-string-pins', '0141', 1832, 'MUST NOT accept legacy bare string refs', 'MUST', ('activity.governed_closure_schema',)),
    ('closure-valid-kind-pin-pairs', '0141', 1833, 'reject nonsensical `kind × pinType` pairs', 'MUST', ('activity.governed_closure_or_lock_schema',)),
    ('pre-release-lock-closure-check', '0141', 1834, 'validate suite lock + suite version closure before promotion', 'SHOULD', ('activity.pre_release_gate',)),
    ('adoption-same-change-closure', '0141', 1835, 'update the closure manifest as part of the same change', 'SHOULD', ('activity.adoption_or_migration_tool',)),
    ('standard-immutable-snapshot', '0142', 1839, 'consumable as immutable snapshots', 'MUST', ('activity.canonical_standard_release',)),
    ('release-snapshot-manifest', '0143', 1843, 'ship a machine-readable `release_snapshot_manifest.json`', 'MUST', ('activity.governed_standard_release',)),
    ('release-snapshot-schema', '0143', 1843, 'validated against `release_snapshot_manifest.schema.json`', 'MUST', ('activity.governed_standard_release',)),
    *[('snapshot-' + name, '0143', 1844, phrase, 'MUST', ('activity.governed_standard_release',))
      for name, phrase in (('standard-version', 'standardVersion'), ('manifest-version', 'standardManifestVersion'),
                           ('kind', 'snapshot kind'), ('build', 'build ref'), ('source-repo', 'source repo ref'),
                           ('bundle-digest', 'bundle digest'), ('artifact-inventory', 'per-artifact digests (or an equivalent immutable artifact inventory)'))],
    ('mirror-originating-snapshot', '0143', 1845, 'reference the originating release snapshot', 'MUST', ('activity.governed_artifact_mirror',)),
    ('no-seeded-copy-canonical-claim', '0143', 1846, 'MUST NOT treat mutable, template-seeded local copies of the standard as canonical unless', 'MUST', ('activity.factory_or_product_standard_copy',)),
    ('pre-upgrade-mirror-comparison', '0143', 1847, 'compare repo-local mirrors against the release snapshot manifest before mutation or upgrade', 'SHOULD', ('activity.adoption_or_standard_diff',)),
    ('placement-lock-playbooks', '0143', 1848, 'Appendix N and Appendix L', 'SHOULD', ('activity.governed_standard_release',)),
)
VERIFICATION_SCOPES = {
    '0121': (1661, 1683), '0122': (1661, 1683), '0123': (1666, 1683),
    '0124': (1666, 1677), '0125': (1666, 1677), '0126': (1681, 1683),
    '0127': (1696, 1702), '0128': (1706, 1708), '0129': (1710, 1712),
    '0130': (1714, 1716), '0131': (1718, 1720), '0132': (1726, 1731),
    '0133': (1735, 1753), '0134': (1735, 1753), '0135': (1749, 1753),
    '0136': (1757, 1765), '0137': (1759, 1765), '0138': (1767, 1771),
    '0139': (1773, 1790), '0140': (1792, 1806), '0141': (1808, 1835),
    '0142': (1837, 1848), '0143': (1837, 1848),
}
VERIFICATION_FORCE = {
    'canonical-local-ci-gate': (1661, 'MUST'),
    'report-explicit-not-run': (1762, 'MUST be represented'),
    **{'registry-' + name: (1737, 'MUST') for name in ('gate-id', 'kind', 'cadence', 'enforcement', 'command', 'owner', 'scope', 'no-result-policy', 'expected-artifacts')},
    **{'suite-lock-' + name: (1799, 'MUST') for name in ('modules', 'repo-role', 'refs', 'override-policy', 'state-model')},
    **{'closure-' + name: (1821, 'MUST') for name in ('standard-version', 'manifest-version', 'suite-version', 'factory-version', 'verify-runtime-version', 'policy-pack-version', 'template-version', 'suite-lock-ref', 'ci-release-pins')},
    'critical-locked-sync-default': (1805, 'MUST be'),
    'closure-structured-pins': (1832, 'MUST use'),
    'distinguish-collection-enforcement': (1787, 'MUST distinguish'),
}

# §12's practical bar has explicit domain/activity conditions. The original
# owner review, offline scenario and data ownership duties are not optional
# merely because AI wrote the draft or an external service is nondeterministic.
DOMAIN_LEAVES = (
    ('boundary-context-owner-record-contract', '0146', 1890, 'bounded context', 'SHOULD', ('activity.repo_or_sdmm_boundary',)),
    ('unjustified-boundary-merge-or-formalize', '0146', 1891, 'treated as suspect and either', 'SHOULD', ('activity.repo_or_sdmm_boundary', 'boundary.no_context_rationale')),
    ('no-silent-contract-rename', '0147', 1898, 'MUST NOT “silently rename”', 'MUST', ('activity.released_contract_terminology',)),
    ('critical-executable-scenarios', '0148', 1903, 'executable scenarios', 'SHOULD', ('activity.critical_workflow',)),
    ('proportional-ddd', '0149', 1907, 'DDD is not an excuse for ceremony', 'SHOULD', ('activity.domain_modelling',)),
    ('domain-glossary', '0150', 1910, 'glossary (or link to one)', 'SHOULD', ('domain.non_trivial',)),
    ('meaning-terms-contracts', '0150', 1915, 'MUST be treated as **contracts**', 'MUST', ('domain.non_trivial', 'activity.product_meaning_terms')),
    ('context-owner', '0151', 1918, 'explicit owner', 'MUST', ('domain.non_trivial', 'activity.bounded_context')),
    ('context-system-of-record', '0151', 1918, 'system of record', 'MUST', ('domain.non_trivial', 'activity.bounded_context')),
    ('enforce-data-ownership', '0151', 1919, 'Data ownership MUST be enforced', 'MUST', ('domain.non_trivial', 'activity.bounded_context')),
    ('no-backdoor-context-writes', '0151', 1920, 'No “backdoor” writes', 'MUST', ('domain.non_trivial', 'activity.bounded_context')),
    ('cross-context-public-contracts', '0151', 1921, 'owning context’s public API/event contracts', 'MUST', ('domain.non_trivial', 'activity.cross_context_data_access')),
    ('core-entity-invariants-stated', '0152', 1924, 'invariants MUST be stated', 'MUST', ('domain.non_trivial', 'activity.core_domain_entity')),
    ('core-entity-invariants-tested', '0152', 1924, '(and tested)', 'MUST', ('domain.non_trivial', 'activity.core_domain_entity')),
    ('aggregate-enforceable-boundaries', '0152', 1925, 'without cross-context transactions', 'SHOULD', ('domain.non_trivial', 'activity.domain_aggregate')),
    ('external-legacy-acl', '0153', 1928, 'anti-corruption layer', 'SHOULD', ('domain.non_trivial', 'activity.external_or_legacy_integration')),
    ('acl-deterministic', '0153', 1929, 'deterministic', 'MUST', ('domain.non_trivial', 'activity.acl_translation')),
    ('acl-fixtures', '0153', 1929, 'covered by fixtures', 'MUST', ('domain.non_trivial', 'activity.acl_translation')),
    *[('boundary-event-' + name, '0154', line, phrase, 'MUST', ('activity.boundary_command_or_domain_event',))
      for name, line, phrase in (('first-class-contract', 1935, 'first-class contract surface'),
                                ('schema', 1936, 'schema'), ('semantics', 1937, 'semantics/invariants'),
                                ('fixtures', 1938, 'fixtures'), ('executable-checks', 1939, 'executable checks'))],
    ('event-domain-naming', '0154', 1940, 'ubiquitous language', 'SHOULD', ('activity.domain_event',)),
    ('event-no-internal-details', '0154', 1940, 'MUST avoid leaking internal implementation details', 'MUST', ('activity.domain_event',)),
    ('state-machine-contract-alignment', '0154', 1941, 'State machines defined in the Master Doc', 'SHOULD', ('activity.documented_job_or_workflow_state_machine',)),
    ('critical-given-when-then', '0155', 1951, 'Given/When/Then', 'SHOULD', ('activity.critical_behavior',)),
    *[('scenario-trace-' + name, '0155', line, phrase, 'MUST', ('activity.bdd_scenario',))
      for name, line, phrase in (('workflow-requirement', 1953, 'workflows (`W#`) and functional requirements'),
                                ('contracts', 1954, 'contract surfaces they exercise'),
                                ('gate', 1955, 'verification gate that runs them'))],
    ('scenario-near-boundary', '0156', 1958, 'near the boundary they test', 'SHOULD', ('activity.repo_local_scenario',)),
    ('cross-repo-integration-harness', '0156', 1962, 'MUST live in the **integration harness**', 'MUST', ('activity.cross_repo_e2e_scenario',)),
    ('tier-deterministic-verification', '0157', 1965, 'deterministic verification paths', 'MUST', ('activity.algorithm_pipeline', 'pipeline.tier_0_or_1')),
    ('tier-bdd-offline-default', '0157', 1965, 'offline-by-default', 'MUST', ('activity.tier_0_or_1_bdd_scenario',)),
    *[('nondeterministic-scenario-' + name, '0157', 1966, phrase, 'MUST', ('activity.bdd_scenario', 'scenario.nondeterministic_external_dependencies'))
      for name, phrase in (('tagged', 'tagged'), ('isolated', 'isolated from the default `verify` path'),
                           ('explicit-runner', 'explicit, documented runner'))],
    *[('owner-accept-' + name, '0158', line, phrase, 'MUST', ('activity.ai_assisted_domain_draft',) + extra)
      for name, line, phrase, extra in (('semantic-definitions', 1978, 'semantic definitions', ()),
                                      ('invariants', 1979, 'invariants', ()),
                                      ('release-scenario', 1980, 'scenario that becomes a release gate', ('scenario.release_gate',)))],
    ('inheritance-stable-is-a', '0159', 1987, 'stable “is-a” relationship', 'MUST', ('activity.domain_inheritance',)),
    *[('domain-class-' + name, '0159', line, phrase, 'SHOULD', ('activity.domain_class',))
      for name, line, phrase in (('explicit', 1990, 'small and explicit'),
                                ('invariants', 1991, 'invariant-bearing'),
                                ('infrastructure-independent', 1992, 'testable without infrastructure'))],
)
DOMAIN_SCOPES = {
    '0146': (1890, 1893), '0147': (1897, 1898), '0148': (1902, 1903),
    '0149': (1907, 1907), '0150': (1907, 1915), '0151': (1907, 1921),
    '0152': (1907, 1925), '0153': (1907, 1929), '0154': (1933, 1944),
    '0155': (1950, 1955), '0156': (1957, 1962), '0157': (1964, 1966),
    '0158': (1968, 1980), '0159': (1984, 1993),
}
DOMAIN_FORCE = {
    'no-backdoor-context-writes': (1919, 'MUST'),
    **{'boundary-event-' + name: (1935, 'MUST') for name in ('schema', 'semantics', 'fixtures', 'executable-checks')},
    **{'scenario-trace-' + name: (1952, 'MUST') for name in ('workflow-requirement', 'contracts', 'gate')},
    **{'owner-accept-' + name: (1977, 'MUST') for name in ('semantic-definitions', 'invariants', 'release-scenario')},
    **{'domain-class-' + name: (1989, 'SHOULD') for name in ('explicit', 'invariants', 'infrastructure-independent')},
}

# Independently reviewed Appendix E duties absent from the main-body mapping.
# Duplicate topology summaries are not counted again. Original authority, strict
# decoding negotiation and pure generated-helper constraints remain distinct.
MULTIREPO_LEAVES = (
    ('scoring-locally-runnable', '0016', 316, 'runnable by the `algo` repo locally', 'MUST', ('activity.cross_repo_scoring_contract',)),
    ('scoring-version-pinned', '0016', 316, 'version‑pinned scoring artifact', 'MUST', ('activity.cross_repo_scoring_contract',)),
    ('no-hidden-success-definition', '0017', 323, 'Hide the definition of “success” exclusively inside', 'MUST', ('activity.cross_repo_scoring_contract',)),
    ('contract-one-decision-owner', '0018', 331, 'exactly one **decision owner**', 'MUST', ('activity.contract_surface',)),
    ('contract-owner-review-rule', '0019', 341, 'CODEOWNERS` (or equivalent review rules)', 'MUST', ('activity.contract_surface',)),
    *[('contract-pr-' + name, '0020', line, phrase, 'MUST', ('activity.contract_change_pr',) + extra)
      for name, line, phrase, extra in (
          ('owner-approval', 350, 'decision owner approval', ()),
          ('fixtures', 351, 'updated fixtures', ('change.contract_fixtures_applicable',)),
          ('codegen', 352, 'updated codegen artifacts', ('change.contract_codegen_applicable',)),
          ('classification-evolution', 353, 'explicit change classification and evolution plan', ()))],
    *[('producer-' + name, '0021', 357, phrase, 'MUST', ('activity.contract_producer',))
      for name, phrase in (('implementation', 'implement the contract'), ('compliance-tests', 'provide compliance tests'),
                           ('non-schema-semantics', 'document non‑schema semantics'))],
    ('consumer-compatible-changes', '0021', 358, 'tolerate backward‑compatible changes', 'MUST', ('activity.contract_consumer',)),
    ('consumer-no-undocumented-interpretation', '0021', 358, 'MUST NOT invent undocumented interpretations', 'MUST', ('activity.contract_consumer',)),
    ('consumer-ignore-unknown-default', '0022', 362, 'ignore unknown fields by default', 'SHOULD', ('activity.contract_consumer',)),
    ('producer-no-tightening-without-window', '0022', 363, 'tightening validation without a migration window', 'SHOULD', ('activity.contract_producer',)),
    ('strict-internet-version-negotiation', '0023', 365, 'explicit versioning/negotiation', 'MUST', ('activity.internet_facing_contract', 'contract.strict_decoding_selected')),
    ('boundary-one-drift-check', '0024', 369, 'At least one of the following MUST exist', 'MUST', ('activity.contract_boundary',)),
    ('critical-two-check-layers', '0025', 375, 'at least two layers', 'SHOULD', ('activity.critical_contract_boundary',)),
    ('shared-error-definitions-portable', '0028', 408, 'error **definitions**', 'SHOULD', ('activity.cross_cutting_error_contract',)),
    ('hub-portable-representations-fixtures', '0029', 410, 'portable representations and fixtures', 'MUST', ('activity.contract_hub',)),
    ('repo-local-runtime-error-classes', '0029', 411, 'own exception/error classes and mapping locally', 'MUST', ('activity.repository_error_mapping',)),
    *[('helper-' + name, '0030', line, phrase, 'MUST', ('activity.generated_contract_helper',))
      for name, line, phrase in (
          ('generated', 422, 'generated from contract artifacts'),
          ('no-network-persistence', 423, 'without network/persistence I/O'),
          ('no-duplicate-cyclic-dependencies', 424, 'dependencies that risk duplication or dependency cycles'),
          ('no-runtime-exceptions', 425, 'Export runtime exception/error classes'))],
    ('helper-data-constructors', '0030', 426, 'construct **data representations**', 'MUST', ('activity.generated_contract_helper', 'helper.constructors_provided')),
    *[('contract-metadata-' + name, '0031', line, phrase, 'SHOULD', ('activity.contract_artifact',))
      for name, line, phrase in (('decision-owner', 432, 'decision owner'), ('stability-tier', 433, 'stability tier'),
                                ('evolution-mode', 434, 'evolution mode'), ('version-changelog', 435, 'version + changelog pointer'),
                                ('required-checks', 436, 'required checks'))],
    ('codegen-frontend-types', '0032', 446, 'TypeScript clients/types for frontend', 'SHOULD', ('activity.frontend_contract_types',)),
    ('codegen-backend-models', '0032', 447, 'server‑side DTOs/validators/models for backend', 'SHOULD', ('activity.backend_contract_models',)),
    ('codegen-algorithm-models', '0032', 448, 'Pydantic models (or equivalent) for algo', 'SHOULD', ('activity.algorithm_contract_models',)),
    *[('codegen-' + name, '0033', line, phrase, 'MUST', ('activity.contract_codegen',))
      for name, line, phrase in (('tool-pins', 452, 'pinned tool versions'), ('deterministic-output', 453, 'deterministic output'),
                                ('ci-reproducibility', 454, 'CI verifies reproducibility'))],
    ('codegen-no-manual-edits', '0034', 456, 'not manually edited', 'MUST', ('activity.generated_contract_code',)),
    ('codegen-separated-path-markers', '0035', 458, 'path + header markers', 'MUST', ('activity.generated_contract_code',)),
    *[('high-impact-fixture-' + name, '0036', line, phrase, 'MUST', ('activity.high_impact_contract_fixtures',))
      for name, line, phrase in (('scrubbed', 472, 'scrubbed of secrets and PII'), ('stable', 473, 'stable'),
                                ('automated', 474, 'executed by automated tests'))],
    ('contract-semver', '0037', 484, 'Semantic Versioning', 'SHOULD', ('activity.contract_versioning',)),
    ('consumer-baseline-pin', '0038', 507, 'Pin to a version/tag/commit', 'MUST', ('activity.contract_consumer',)),
    ('consumer-upgrade-compatibility', '0040', 513, 'fixtures decoding and/or integration harness', 'MUST', ('activity.consumer_contract_upgrade',)),
    ('contract-change-classification', '0043', 529, 'Every contract change MUST be labeled', 'MUST', ('activity.contract_change',)),
    ('behavior-change-documentation', '0044', 535, 'explicit documentation', 'MUST', ('change.contract_behavioral',)),
    ('behavior-change-fixtures-tests', '0044', 535, 'fixtures/tests that demonstrate the new behavior', 'MUST', ('change.contract_behavioral',)),
    *[('breaking-strategy-' + name, '0046', line, phrase, 'MUST', ('change.contract_breaking', 'boundary.compatibility_mode') + extra)
      for name, line, phrase, extra in (('cutoff', 580, 'cutoff (date/release)', ()),
                                      ('old-new-fixtures', 581, 'fixtures/tests for both old and new', ()),
                                      ('stored-data-migration', 582, 'migration plan for stored data', ('change.persisted_data_migration_applicable',)))],
)
MULTIREPO_SCOPES = {
    '0016': (303, 325), '0017': (303, 325), '0018': (329, 341), '0019': (329, 341),
    '0020': (343, 353), '0021': (355, 365), '0022': (355, 365), '0023': (355, 365),
    '0024': (367, 375), '0025': (367, 375), '0028': (406, 426), '0029': (406, 426),
    '0030': (406, 426), '0031': (428, 438), '0032': (440, 458), '0033': (440, 458),
    '0034': (440, 458), '0035': (440, 458), '0036': (460, 474), '0037': (480, 491),
    '0038': (493, 507), '0040': (509, 513), '0043': (527, 535), '0044': (527, 535),
    '0046': (570, 582),
}
MULTIREPO_FORCE = {
    **{'contract-pr-' + name: (348, 'MUST') for name in ('owner-approval', 'fixtures', 'codegen', 'classification-evolution')},
    'consumer-compatible-changes': (358, 'Consumer MUST'),
    **{'contract-metadata-' + name: (430, 'SHOULD') for name in ('decision-owner', 'stability-tier', 'evolution-mode', 'version-changelog', 'required-checks')},
    **{'codegen-' + name: (444, 'SHOULD') for name in ('frontend-types', 'backend-models', 'algorithm-models')},
    **{'codegen-' + name: (450, 'MUST') for name in ('tool-pins', 'deterministic-output', 'ci-reproducibility')},
    **{'high-impact-fixture-' + name: (470, 'MUST') for name in ('scrubbed', 'stable', 'automated')},
    **{'breaking-strategy-' + name: (578, 'MUST') for name in ('cutoff', 'old-new-fixtures', 'stored-data-migration')},
}


def legacy_navigation_parent(unit, registry):
    """Use an existing stable parent; never invent a clause in the old body."""
    if unit['parentClause']:
        return unit['parentClause']
    match = re.fullmatch(r'appendices/appendix-([a-z]+)-[^/]+\.md', unit['source'])
    if match:
        parent = 'A-' + match.group(1).upper()
        if parent not in registry['appendixIds']:
            raise ValueError('legacy appendix navigation parent is not registered')
        return parent
    if unit['source'] == 'SPECIFICATION.md' and 'C-001' in registry['clauseIds']:
        return 'C-001'  # Preserved document-purpose/root ID for unnumbered text.
    if unit['source'] in ('DAS_DEPLOYMENT_ADDENDUM.md', 'DAS_GOVERNANCE_COLLABORATION.md') and 'C-001' in registry['clauseIds']:
        # A separately named addendum has no numbered clause in the old body.
        # Navigate from the registered Standard root, without inventing §14.
        return 'C-001'
    raise ValueError('unreviewed legacy source has no registered navigation parent')


IMPLICIT_MINIMUM_UNITS = (
    ('contracts', 1687, '- `contracts`: schema validation + fixture validation + compatibility checks for changed contracts.'),
    ('algo', 1688, '- `algo`: boundary checks + unit tests + deterministic CI eval suite + replay (offline) where applicable.'),
    ('backend', 1689, '- `backend`: unit + integration + contract tests + idempotency/retry tests for job flows.'),
    ('frontend', 1690, '- `frontend`: boundary checks + unit + minimal E2E smoke for critical flows.'),
    ('integration', 1691, '- `integration`: end-to-end smoke + compatibility runner (old/new fixtures) + system verify.'),
    ('docs', 1692, '- `docs/meta` (whenever a repo carries a governed doc set): status enum validation, governing-standard presence/correctness, required-section checks for canonical docs, and placeholder-residue checks.'),
)

# Exact, independently byte-pinned carriers omitted by keyword sampling.
# Headings make F.1/F.9 required/minimum; H.2 inherits H.1's severity policy.
IMPLICIT_PLAYBOOK_UNITS = (
    ('legacy-guide-e80f2d11-required', 'appendices/appendix-f-sdmm-refactoring-migration-playbook.md', 'A-F', 5, 12, '73094e6e0037ce9b4519e2b685bb2996e32bc3071a5d625527d3e2961b032a6d'),
    ('legacy-guide-e80f2d11-cutover', 'appendices/appendix-f-sdmm-refactoring-migration-playbook.md', 'A-F', 84, 93, '3b0db605145d6706281bdbd1d2fe249e3ef839ddffae891397e91af7688542a3'),
    ('legacy-guide-4d6c4f21-checklist', 'appendices/appendix-h-ui-design-review-checklist.md', 'A-H', 17, 38, '02a7a7e6c8ea33619deb749f928c8735ecb9fcfd58e69c1b4f8ed6e2589a5022'),
)

# Required template minima, separately pinned to the unchanged original body.
IMPLICIT_PLAYBOOK_UNITS += (
    ('legacy-guide-c-traceability', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 242, 251, '703834931518da5e604d486208d824dbed3eacb491ec0ed672d984567335ad85'),
    ('legacy-guide-c-domain-glossary', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 439, 440, 'b53e27dcff67e2a86f6418d463412e7e5c9f28b257f6dabb8e166e4cfaee3341'),
    ('legacy-guide-c-environment-matrix', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 552, 569, '3e44a89bda93d6c101f3ba9a94dfdd41fa4035c726bb231180fe1d2a571246ab'),
    ('legacy-guide-c-deployment-record', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 571, 578, '7de61f5d2ef162eade9d46dfb84c06198d4bbf12b0ce3adcd1232a1263772b00'),
    ('legacy-guide-c-vendor-record', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 580, 594, '16ce7ec38f348fa920a3b52c117c54e0a258b423644e644f6540732a931c0982'),
    ('legacy-guide-c-security-declarations', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 733, 738, '3fce17a7140e133257998fc3560c8909484a9b8cc0d1a082ad36b476cb145cd6'),
    ('legacy-guide-c-production-replay-record', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 773, 777, 'ae199d0497691c9c79fab8a908caf49e9fcd9e79cb2041e4ae44de29d498b7fc'),
    ('legacy-guide-c-breaking-migration-record', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 858, 862, '093580820bcd53536a5daaf07fb2c206e3eb7edea10ba5a16ea80497475469f6'),
    ('legacy-guide-d-primary-states', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 128, 136, '23db36a55f88749fbeb20e1e84a501a81cd0163c751fe3609352a317ced75a1f'),
    ('legacy-guide-d-ai-states', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 139, 149, '3ea2bf1c7d9a71d4fa268cabe8b9691c830ed48f8e303c357f2db4368d43a274'),
    ('legacy-guide-d-controls-record', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 151, 155, 'd751cd610dbadf4d594930a724438db8e0b3a1d6d2ffa8e51faa2faefc266523'),
    ('legacy-guide-d-citation-record', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 172, 180, '97fd550f0622d1b97ade6061b8317d06b646370dd25504c887289d422765105b'),
    ('legacy-guide-d-accessibility-record', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 186, 190, 'f6d552cc2a79ff03a3970546bf1a38977acdba1d0f5e5be38d8a690290ed9b83'),
    ('legacy-guide-d-multidevice-record', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 192, 194, 'c3555e683c2e79d6baccb15c94c608597506df58422d4055f3119e60174ed7e4'),
    ('legacy-guide-k-conventions-inventory', 'appendices/appendix-k-hfvi-vis-template.md', 'A-K', 34, 48, 'f2264fe203fc2d89f6784c7a196c5610bb3d29e459781d77b99083822baf88d5'),
    ('legacy-guide-k-critical-verification', 'appendices/appendix-k-hfvi-vis-template.md', 'A-K', 107, 114, 'abca9ef6eb3356d786ea9d8fd1b9a20d4093b06d1ce12da9d2d3c15d0e1396e1'),
)

IMPLICIT_PLAYBOOK_UNITS += (
    ('legacy-guide-c-contract-index', 'appendices/appendix-c-project-master-doc-template.md', 'A-C', 621, 625, '6711bf25136671225e17408bc1583651ec8aebd6eb53d267968c1e58d527163f'),
    ('legacy-guide-d-workflow-map', 'appendices/appendix-d-ui-spec-appendix-template.md', 'A-D', 90, 98, 'bbd89c283069a648dacd0f7f680caef313098c7dc76e3ea2be9a8f7b7924ce47'),
    ('legacy-guide-g-ui-content', 'appendices/appendix-g-ai-product-engineering-principles-addendum.md', 'A-G', 923, 935, '71697e714451e5ad65765999aef7a758f5413a2638a271322252593d23b09a7b'),
)


# E1's optional illustrative layout retains explicit conditional BCP14 pointer duties.
IMPLICIT_PLAYBOOK_UNITS += (
    ('legacy-guide-g-dataset-pointer', 'appendices/appendix-g-ai-product-engineering-principles-addendum.md', 'A-G', 780, 840, '1c31ac11ec085563fbacb8b7ee95d4f752bd42ba76d0e671ef8779843806018c'),
)

MANIFEST_DOCUMENT_FACTS = {
    'master_doc': 'document.kind_master_doc',
    'module_doc': 'document.kind_module_doc',
    'ui_spec': 'document.kind_ui_spec',
    'headless_surface_note': 'document.kind_headless_surface_note',
    'normative_addendum': 'document.kind_normative_addendum',
}
MANIFEST_PROFILE_FACTS = {
    'L0': 'document.conformance_l0', 'L1': 'document.conformance_l1', 'L2': 'document.conformance_l2',
    'headless': 'document.interaction_headless', 'standard_ui': 'document.interaction_standard_ui',
    'hfvi_canvas_webgl_game': 'document.interaction_hfvi',
}
MANIFEST_RULE_OWNERS = {
    'l2_master_doc_requires_context_pack': 'das.governance.documentation',
    'headless_master_doc_requires_headless_surface_note': 'das.interaction.headless',
    'ui_projects_require_ui_spec': 'das.interaction.standard-ui',
    'hfvi_projects_require_vis_appendix': 'das.interaction.hfvi',
    'worker_service_module_docs_require_interaction_profile': 'das.governance.documentation',
    'master_doc_requires_canonical_entrypoint_role': 'das.governance.documentation',
    'module_doc_requires_module_doc_role': 'das.governance.documentation',
    'ui_spec_requires_non_headless_interaction_profile': 'das.interaction.headless',
    'headless_surface_note_requires_headless_interaction_profile': 'das.interaction.headless',
    'normative_addendum_requires_subordinate_role': 'das.governance.documentation',
}


def manifest_rule_sources(root, baseline):
    """Read the ten original machine rules, pinned independently of the leaves.

    Document facts identify the governed document, not a project's primary UI
    or whether its metadata already passes. Each rule retains its original
    required values and permitted mapped equivalents in its source fragments.
    """
    raw = local_file(root, 'standard_manifest.json').read_text()
    manifest = standard_io.loads(raw)
    rules = baseline['conditionalRequirements']
    if (manifest['conditionalRequirements'] != rules
            or {rule['ruleId'] for rule in rules} != set(MANIFEST_RULE_OWNERS)):
        raise ValueError('original manifest conditions changed during leaf extraction')
    decoder = json.JSONDecoder()
    result = []
    for rule in rules:
        marker = '"ruleId": ' + json.dumps(rule['ruleId'])
        if raw.count(marker) != 1:
            raise ValueError('manifest rule missing or ambiguous original source')
        start = raw.rfind('{', 0, raw.index(marker))
        value, length = decoder.raw_decode(raw[start:])
        if value != rule:
            raise ValueError('manifest rule fragment differs from independent original')
        first = raw.count('\n', 0, start) + 1
        last = raw.count('\n', 0, start + length) + 1
        text = '\n'.join(raw.splitlines()[first - 1:last])
        result.append((rule, first, last, text))
    return result


def manifest_rule_requirements(root, baseline):
    """Map original rules to the existing bounded three-valued leaf language."""
    mappings = {item['ruleId']: item for item in load(root / 'standard_modules.json')['conditionalMappings']}
    if {key: value['ownerModule'] for key, value in mappings.items()} != MANIFEST_RULE_OWNERS:
        raise ValueError('original manifest rule owner or identity changed')
    result = []
    for rule, first, last, text in manifest_rule_sources(root, baseline):
        def ref(start, end):
            return dict(path='standard_manifest.json', startLine=first, endLine=last,
                        startColumn=start, endColumn=end,
                        textSha256=hashlib.sha256(text[start:end].encode()).hexdigest())
        def field(name):
            start = text.index('"' + name + '"')
            colon = text.index(':', start) + 1
            value_start = colon + len(text[colon:]) - len(text[colon:].lstrip())
            _, length = json.JSONDecoder().raw_decode(text[value_start:])
            return ref(value_start, value_start + length)
        scope = rule['appliesTo']
        terms = [dict(op='fact', key=MANIFEST_DOCUMENT_FACTS[scope['docType']])]
        for key in ('conformanceProfiles', 'interactionProfiles', 'moduleKinds'):
            if key not in scope:
                continue
            facts = [('document.module_' + name) if key == 'moduleKinds' else MANIFEST_PROFILE_FACTS[name]
                     for name in scope[key]]
            alternatives = [dict(op='fact', key=name) for name in facts]
            terms.append(alternatives[0] if len(alternatives) == 1 else dict(op='any', args=alternatives))
        criterion = rule['ruleId'].replace('_', '-')
        force = text.index('"requires"')
        result.append(dict(id=mappings[rule['ruleId']]['ownerModule'] + '.manifest-rule.' + criterion,
            ownerModule=mappings[rule['ruleId']]['ownerModule'], parentClause='cl-2.5',
            legacyUnitId='legacy-manifest-' + criterion, strength='MUST',
            applicability='original-manifest-document-kind-and-declared-profile', criterion=criterion,
            conditionRefs=[field('appliesTo')], contextRefs=[ref(text.index('{'), text.rfind('}') + 1)],
            strengthRef=ref(force, force + len('"requires"')), bodyRefs=[field('requires')],
            activation=terms[0] if len(terms) == 1 else dict(op='all', args=terms)))
    return result


def legacy_units(root, baseline):
    """Extend the reviewed inventory without resampling its 479 keyword blocks.

    Explicit original minimum/checklist rows were absent from keyword sampling. Their
    exact literals/ranges are reviewed here against the independently pinned
    whole 1.4 source, not derived from the modified catalog or new edition.
    """
    units = {unit['id']: unit for unit in baseline['units']}
    if len(units) != len(baseline['units']):
        raise ValueError('duplicate independent baseline unit')
    source = next(item for item in baseline['sources'] if item['path'] == 'SPECIFICATION.md')
    original = legacy_source(root, source).splitlines()
    for name, line, expected in IMPLICIT_MINIMUM_UNITS:
        if original[line - 1] != expected:
            raise ValueError('reviewed implicit minimum differs from the pinned original source')
        identity = 'legacy-minimum-de7276bb-10-2-' + name
        if identity in units:
            raise ValueError('implicit minimum cannot replace an independent keyword unit')
        units[identity] = dict(id=identity, source='SPECIFICATION.md', parentClause='cl-10.2',
                              startLine=line, endLine=line, text=expected,
                              textSha256=hashlib.sha256(expected.encode()).hexdigest())
    for identity, path, parent, first, last, expected in IMPLICIT_PLAYBOOK_UNITS:
        source = next(item for item in baseline['sources'] if item['path'] == path)
        text = '\n'.join(legacy_source(root, source).splitlines()[first - 1:last])
        if identity in units or hashlib.sha256(text.encode()).hexdigest() != expected:
            raise ValueError('reviewed implicit playbook carrier differs from pinned source')
        units[identity] = dict(id=identity, source=path, parentClause=parent,
                              startLine=first, endLine=last, text=text, textSha256=expected)
    for rule, first, last, text in manifest_rule_sources(root, baseline):
        identity = 'legacy-manifest-' + rule['ruleId'].replace('_', '-')
        if identity in units:
            raise ValueError('manifest rule cannot replace an existing original carrier')
        units[identity] = dict(id=identity, source='standard_manifest.json', parentClause='cl-2.5',
            startLine=first, endLine=last, text=text, textSha256=hashlib.sha256(text.encode()).hexdigest())
    return units


MINIMUM_LEAVES = (
    *[('contracts-' + name, 'contracts', 1687, phrase, 'MUST', ('activity.contract_repository',) + extra)
      for name, phrase, extra in (('schema', 'schema validation', ()), ('fixtures', 'fixture validation', ()),
                                 ('changed-compatibility', 'compatibility checks for changed contracts', ('activity.contract_change',)))],
    *[('backend-' + name, 'backend', 1689, phrase, 'MUST', ('activity.backend_repository',) + extra)
      for name, phrase, extra in (('unit', 'unit', ()), ('integration', 'integration', ()),
                                 ('contract', 'contract tests', ()),
                                 ('job-idempotency', 'idempotency', ('activity.backend_job_flows',)),
                                 ('job-retry', 'retry tests for job flows', ('activity.backend_job_flows',)))],
    *[('integration-' + name, 'integration', 1691, phrase, 'MUST', ('activity.integration_harness',))
      for name, phrase in (('smoke', 'end-to-end smoke'), ('compatibility', 'compatibility runner (old/new fixtures)'),
                           ('system-verify', 'system verify'))],
    *[('docs-' + name, 'docs', 1692, phrase, 'MUST', ('activity.governed_doc_set',))
      for name, phrase in (('status', 'status enum validation'), ('governing-standard', 'governing-standard presence/correctness'),
                           ('required-sections', 'required-section checks for canonical docs'),
                           ('placeholders', 'placeholder-residue checks'))],
)
MINIMUM_ALIASES = {
    'algo': tuple('das.ai-runtime-evaluation.algorithm.' + name for name in
                  ('repo-boundary-checks', 'repo-core-unit-tests', 'repo-deterministic-eval', 'repo-tier-replay')),
    'frontend': tuple('das.interaction.standard-ui.ui.default-gate-' + name for name in ('boundary', 'unit', 'smoke')),
}


# Reviewed Appendix G backend obligations. Existing graph/public-import and
# job-configuration duties are linked below rather than duplicated. G's scoped
# MUST for external stored schemas remains distinct from the wider old SHOULD.
BACKEND_LEAVES = (
    ("single-artifact-or-operational-justification", "0006", 134, "single deployable artifact unless a runtime split is operationally justified", "SHOULD", ("activity.backend_repository",)),
    ("no-ai-sized-runtime-split", "0006", 136, "purely to make code “AI-sized”", "MUST", ("activity.backend_runtime_design",)),
    ("no-runtime-split-to-avoid-boundaries", "0006", 136, "or to avoid enforcing internal boundaries", "MUST", ("activity.backend_runtime_design",)),
    ("side-effect-adapters", "0007", 142, "isolated behind adapters", "MUST", ("activity.backend_side_effect_code",)),
    ("deterministic-domain", "0007", 143, "deterministic and testable without infrastructure", "SHOULD", ("activity.backend_domain_logic",)),
    ("no-ownerless-cross-module-helper", "0007", 144, "without ownership", "MUST", ("activity.backend_cross_module_helper",)),
    ("cross-cutting-owner", "0007", 144, "a single owner module", "MUST", ("activity.backend_cross_cutting_code",)),
    ("sor-state-validation", "0008", 147, "validated and applied in the backend", "MUST", ("activity.backend_state_change",)),
    ("no-consumer-state-authority", "0008", 148, "MUST NOT be the authority for canonical state", "MUST", ("activity.backend_state_change",)),
    ("transaction-before-external-effects", "0008", 149, "committed transactionally with invariant checks before any external side effects", "MUST", ("activity.backend_state_change",)),
    ("one-invariant-owner", "0008", 151, "enforced in one place", "SHOULD", ("activity.backend_cross_entity_invariant",)),
    ("boundary-validation", "0009", 156, "Validate and normalize all untrusted inputs", "MUST", ("activity.backend_untrusted_input",)),
    ("contract-publication", "0009", 157, "Publish contract artifacts", "MUST", ("activity.backend_external_contract",)),
    ("contract-schema", "0009", 157, "schema", "MUST", ("activity.backend_external_contract",)),
    ("contract-semantics", "0009", 157, "semantics", "MUST", ("activity.backend_external_contract",)),
    ("contract-fixtures", "0009", 157, "fixtures", "MUST", ("activity.backend_external_contract",)),
    ("contract-checks", "0009", 157, "executable checks", "MUST", ("activity.backend_external_contract",)),
    ("contract-metadata", "0009", 158, "machine-readable metadata", "SHOULD", ("activity.backend_external_contract",)),
    ("canonical-error-mapping", "0009", 160, "stable error envelope + stable error codes", "MUST", ("activity.backend_external_contract",)),
    ("no-raw-error-contract", "0009", 160, "raw infrastructure/library errors", "MUST", ("activity.backend_external_contract",)),
    ("error-id-governance", "0009", 161, "centrally governed as stable identifier contracts", "MUST", ("activity.backend_error_code",)),
    ("error-id-version", "0009", 161, "versioned in the contract hub", "MUST", ("activity.backend_error_code",)),
    ("error-correlation", "0009", 162, "a correlation identifier", "SHOULD", ("activity.backend_error_envelope",)),
    ("safe-retryability-class", "0009", 162, "a retryability classification where safe", "SHOULD", ("activity.backend_error_envelope",)),
    ("safe-validation-diagnostics", "0009", 163, "diagnosable (field paths, codes) without exposing sensitive internals", "SHOULD", ("activity.backend_untrusted_input",)),
    ("non-schema-semantics", "0010", 167, "idempotency, pagination, timeouts, retryability, ordering guarantees, partial-success behavior, and rate-limit semantics", "MUST", ("activity.backend_external_endpoint_or_event",)),
    ("timeout-cancellation-contract", "0010", 168, "Declare timeout and cancellation behavior", "MUST", ("activity.backend_interactive_or_job_creation_endpoint",)),
    ("automated-success-failure-fixtures", "0010", 169, "fixtures for success and representative failure paths", "SHOULD", ("activity.backend_external_endpoint_or_event",)),
    ("retryable-write-idempotency", "0011", 172, "idempotent within a documented deduplication window", "MUST", ("activity.retryable_backend_write",)),
    ("dedup-window-or-prevent-late-retries", "0011", 173, "The deduplication window MUST cover the maximum end-to-end retry/redelivery window for that operation (client retries, gateway retries, and queue redelivery), or the system MUST ensure that retries cannot occur beyond the deduplication window.", "MUST", ("activity.retryable_backend_write",)),
    ("key-source-lifetime", "0011", 175, "key source and lifetime", "MUST", ("activity.retryable_backend_write",)),
    ("dedup-scope", "0011", 176, "deduplication scope", "MUST", ("activity.retryable_backend_write",)),
    ("canonical-request-comparison", "0011", 177, "canonical request normalization", "MUST", ("activity.retryable_backend_write",)),
    ("key-conflict-policy", "0011", 178, "conflict policy", "MUST", ("activity.retryable_backend_write",)),
    ("response-replay-semantics", "0011", 179, "response replay semantics", "MUST", ("activity.retryable_backend_write",)),
    ("replay-storage-policy", "0011", 180, "storage policy", "MUST", ("activity.retryable_backend_write",)),
    ("explicit-key-when-no-safe-implicit-idempotency", "0011", 181, "require an explicit idempotency key", "MUST", ("activity.retryable_backend_write", "operation.no_safe_implicit_idempotency")),
    ("reject-invalid-key", "0011", 181, "reject missing/invalid keys with a stable, documented error code", "MUST", ("activity.retryable_backend_write", "operation.no_safe_implicit_idempotency")),
    ("external-side-effect-dedup", "0011", 182, "include an external deduplication mechanism", "MUST", ("activity.retryable_backend_write", "operation.nonduplicable_external_effect")),
    ("nonretryable-when-no-safe-dedup", "0011", 183, "classified as **non-retryable**", "MUST", ("activity.backend_state_change", "operation.no_safe_external_dedup")),
    ("prevent-unsafe-retries-every-layer", "0011", 183, "prevented at every layer", "MUST", ("activity.backend_state_change", "operation.no_safe_external_dedup")),
    ("deterministic-documented-conflict", "0011", 184, "deterministic and documented", "MUST", ("activity.retryable_backend_write",)),
    ("minimal-request-hash", "0011", 185, "hash of the normalized request", "SHOULD", ("activity.retryable_backend_write",)),
    ("sensitive-replay-body-controls", "0011", 185, "treat them as sensitive artifacts", "SHOULD", ("activity.retryable_backend_write", "operation.raw_replay_body_stored")),
    ("standard-key-transport", "0011", 186, "Standardize idempotency key transport", "SHOULD", ("activity.retryable_backend_write",)),
    ("opaque-key", "0011", 187, "opaque identifiers", "MUST", ("activity.backend_idempotency_key",)),
    ("no-key-secrets-pii", "0011", 187, "encode secrets or PII", "MUST", ("activity.backend_idempotency_key",)),
    ("no-full-key-log", "0011", 187, "logged in full", "MUST", ("activity.backend_idempotency_key",)),
    ("no-key-metric-analytics", "0011", 188, "metric label dimensions or analytics identifiers", "MUST", ("activity.backend_idempotency_key",)),
    ("operator-replay-new-key-or-retain-dedup", "0011", 189, "If operator tooling can replay/requeue work beyond the deduplication window, it MUST either (a) require a new idempotency key/job ID and treat the replay as a new operation, or (b) retain deduplication records for the full replay window.", "MUST", ("activity.backend_operator_replay_beyond_dedup_window",)),
    ("key-operation-scope", "0011", 190, "Scope idempotency keys by operation", "SHOULD", ("activity.backend_idempotency_key",)),
    ("model-output-before-state-effects", "0012", 193, "validated against a schema and normalized before persistence or side effects", "MUST", ("activity.backend_model_output_state_change",)),
    ("bounded-observable-repair", "0012", 194, "budgeted, observable, and safely bounded", "MUST", ("activity.backend_model_repair",)),
    ("stable-model-prompt-config-id", "0012", 195, "stable and treated as identifier contracts", "MUST", ("activity.backend_model_debug_or_rollout",)),
    ("privacy-safe-repro-diagnostics", "0012", 196, "without storing raw sensitive content by default", "SHOULD", ("activity.backend_model_output",)),
    ("job-id", "0013", 203, "`jobId`", "MUST", ("activity.backend_long_running_job",)),
    ("job-type", "0013", 204, "`jobType`", "MUST", ("activity.backend_long_running_job",)),
    ("job-schema-version", "0013", 205, "`schemaVersion`", "MUST", ("activity.backend_long_running_job",)),
    ("job-status", "0013", 206, "`status`", "MUST", ("activity.backend_long_running_job",)),
    ("job-timestamps", "0013", 207, "`createdAt` / `updatedAt`", "MUST", ("activity.backend_long_running_job",)),
    ("job-attempt-retry-metadata", "0013", 208, "attempt counters and retry/backoff metadata", "MUST", ("activity.backend_long_running_job",)),
    ("job-budget-summary", "0013", 210, "declared budgets and a budget consumption summary", "MUST", ("activity.backend_long_running_job",)),
    ("job-artifact-references", "0013", 211, "references to primary input/output artifacts", "MUST", ("activity.backend_long_running_job",)),
    ("job-typed-error", "0013", 212, "typed error/diagnostics representation", "MUST", ("activity.backend_long_running_job",)),
    ("job-correlation", "0013", 213, "correlation IDs", "MUST", ("activity.backend_long_running_job",)),
    ("safe-inspectable-job", "0013", 214, "safe to store and inspect broadly", "SHOULD", ("activity.backend_long_running_job",)),
    ("idempotent-job-transitions", "0013", 215, "idempotent", "MUST", ("activity.backend_job_transition",)),
    ("defined-job-machine", "0013", 215, "defined state machine", "MUST", ("activity.backend_job_transition",)),
    ("no-job-time-travel", "0013", 216, "Terminal states MUST NOT transition back", "MUST", ("activity.backend_job_transition",)),
    ("small-job-status-enum", "0013", 217, "small and explicit", "SHOULD", ("activity.backend_long_running_job",)),
    ("versioned-job-hub-artifacts", "0013", 218, "stored and versioned in the contract hub", "SHOULD", ("activity.backend_long_running_job",)),
    ("full-pipeline-result-every-attempt", "0014", 224, "full algorithm **PipelineResult** for **each attempt**", "MUST", ("activity.backend_algorithm_job",)),
    ("no-last-run-only-terminality", "0015", 235, "MUST NOT infer terminality from `runs[-1]` alone", "MUST", ("activity.backend_algorithm_job",)),
    ("retry-cancel-terminal-state", "0015", 235, "consider retry policy", "MUST", ("activity.backend_algorithm_job",)),
    ("retry-state-when-attempts-remain", "0016", 242, "remain `queued`", "SHOULD", ("activity.backend_algorithm_job", "job.last_run_failed_retries_remain")),
    ("normalized-run-error", "0017", 246, "shared `NormalizedError` shape", "MUST", ("activity.backend_algorithm_job_failure",)),
    ("structured-nonfatal-diagnostics", "0017", 247, "shared `Diagnostics` shape", "SHOULD", ("activity.backend_algorithm_job_diagnostics",)),
    ("identical-derived-job-result", "0018", 253, "identical to `runs[-1].result`", "MUST", ("activity.backend_algorithm_job", "job.derived_result_field_present")),
    ("derived-result-not-canonical", "0018", 253, "MUST NOT be treated as the canonical source", "MUST", ("activity.backend_algorithm_job", "job.derived_result_field_present")),
    ("stage-retry-class", "0019", 258, "retry classification", "MUST", ("activity.backend_job_retry",)),
    ("bounded-jitter-backoff", "0019", 259, "bounded (attempts, elapsed time) and use backoff with jitter", "MUST", ("activity.backend_job_retry",)),
    ("poison-message-handling", "0019", 260, "poison-message handling", "MUST", ("activity.backend_queue_redelivery",)),
    ("at-least-once-dedup", "0019", 261, "at-least-once delivery + idempotency", "SHOULD", ("activity.backend_job_retry",)),
    ("transactional-state-driven-events", "0019", 262, "transactional pattern", "SHOULD", ("activity.backend_state_driven_effect",)),
    ("best-effort-cancellation", "0020", 265, "propagate cancellation downstream when safe", "SHOULD", ("activity.backend_long_running_job",)),
    ("job-type-budgets", "0020", 266, "explicit budgets (time, steps/iterations, external calls, and cost where applicable)", "MUST", ("activity.backend_long_running_job",)),
    ("budget-classified", "0020", 267, "classified as **hard** or **soft**", "MUST", ("activity.backend_long_running_job",)),
    ("hard-budget-stop", "0020", 268, "stop further work", "MUST", ("activity.backend_long_running_job", "job.hard_budget_exhausted")),
    ("hard-budget-no-effects", "0020", 268, "prevent additional side effects", "MUST", ("activity.backend_long_running_job", "job.hard_budget_exhausted")),
    ("hard-budget-terminal", "0020", 268, "transition to a terminal outcome", "MUST", ("activity.backend_long_running_job", "job.hard_budget_exhausted")),
    ("hard-budget-diagnostic", "0020", 268, "emit a stable diagnostic code", "MUST", ("activity.backend_long_running_job", "job.hard_budget_exhausted")),
    ("hard-budget-safe-outcome", "0020", 268, "If a partial/best-effort result is safe to return, the outcome MUST be `degraded`; otherwise it MUST be `failed`.", "MUST", ("activity.backend_long_running_job", "job.hard_budget_exhausted")),
    ("soft-budget-diagnostic", "0020", 269, "emit a stable diagnostic code or metric", "MUST", ("activity.backend_long_running_job", "job.soft_budget_exceeded")),
    ("soft-budget-documented-lifecycle", "0020", 269, "explicitly documented per job type/stage/profile", "MUST", ("activity.backend_long_running_job", "job.soft_budget_used")),
    ("soft-budget-justification", "0020", 269, "SHOULD be used only when a hard cutoff would cause worse outcomes or when spend can only be estimated until completion.", "SHOULD", ("activity.backend_long_running_job", "job.soft_budget_used")),
    ("budget-envelope-metrics", "0020", 270, "recorded in the job envelope and emitted in metrics", "MUST", ("activity.backend_long_running_job",)),
    ("in-loop-stage-budget-check", "0020", 271, "in-loop and at stage boundaries", "SHOULD", ("activity.backend_long_running_job",)),
    ("concurrency-backpressure-limits", "0020", 272, "concurrency and queue backpressure limits", "MUST", ("activity.backend_job_queue",)),
    ("explicit-backpressure-behavior", "0020", 273, "explicit (reject, shed load, queue, or degrade)", "SHOULD", ("activity.backend_job_queue",)),
    ("observable-backpressure", "0020", 274, "observable", "MUST", ("activity.backend_job_queue",)),
    ("rolling-schema-compatibility", "0021", 279, "backward compatible across rolling deploys", "MUST", ("activity.backend_schema_change",)),
    ("repeatable-automated-migration", "0021", 280, "automated, repeatable, and safe to re-run", "MUST", ("activity.backend_schema_change",)),
    ("avoid-or-review-production-locks", "0021", 281, "Avoid production-impacting locks; when unavoidable, require explicit review and a rollout plan.", "SHOULD", ("activity.backend_schema_change",)),
    ("plan-index-migration-impact", "0021", 282, "Treat index changes as migrations", "SHOULD", ("activity.backend_index_change",)),
    ("persisted-external-schema-version", "0022", 285, "version the stored schema", "MUST", ("activity.backend_external_persisted_artifact",)),
    ("artifact-retention-deletion", "0022", 286, "retention and deletion rules", "MUST", ("activity.backend_persisted_artifact",)),
    ("sensitive-encryption-or-approved-exception", "0022", 287, "For artifacts classified as sensitive, encryption-at-rest MUST be enabled (or an explicit documented exception approved by the appropriate owner).", "MUST", ("activity.backend_sensitive_artifact",)),
    ("artifact-key-ownership-rotation", "0022", 288, "key ownership and rotation", "SHOULD", ("activity.backend_encrypted_artifact",)),
    ("sor-authorization", "0023", 293, "system-of-record boundary", "MUST", ("activity.backend_system_of_record_operation",)),
    ("stable-governed-permission-ids", "0023", 294, "stable, centrally governed", "MUST", ("activity.backend_permission_identifier",)),
    ("auditable-auth-decisions", "0023", 295, "auditable", "SHOULD", ("activity.backend_system_of_record_operation",)),
    ("high-risk-audit-event", "0024", 298, "actor, resource, action, outcome, and correlation IDs", "SHOULD", ("activity.backend_high_risk_action",)),
    ("safe-audit-payload", "0024", 299, "avoid raw sensitive payloads unless explicitly required and protected", "MUST", ("activity.backend_audit_emission",)),
    ("end-to-end-correlation", "0025", 304, "Propagate correlation IDs", "MUST", ("activity.backend_boundary_or_async_callback",)),
    ("structured-state-error-events", "0025", 305, "structured events for job state changes and error outcomes", "MUST", ("activity.backend_job_event",)),
    ("standard-log-fields", "0025", 306, "Standardize structured log fields", "SHOULD", ("activity.backend_log_emission",)),
    ("verify-unit", "0026", 309, "unit tests", "MUST", ("activity.backend_repository",)),
    ("verify-contract", "0026", 309, "contract enforcement tests", "MUST", ("activity.backend_repository",)),
    ("verify-build", "0026", 309, "build/package checks", "MUST", ("activity.backend_repository",)),
    ("verify-static", "0026", 309, "static analysis", "MUST", ("activity.backend_repository",)),
    ("hermetic-verify", "0026", 310, "no calls to external SaaS APIs", "SHOULD", ("activity.backend_repository",)),
    ("versioned-operational-conventions", "0027", 313, "version them in the contract hub", "SHOULD", ("activity.backend_cross_service_convention",)),
)
BACKEND_FORCE = {
    "single-artifact-or-operational-justification": (134, "SHOULD"),
    "no-ai-sized-runtime-split": (136, "MUST NOT"),
    "no-runtime-split-to-avoid-boundaries": (136, "MUST NOT"),
    "side-effect-adapters": (142, "MUST"),
    "deterministic-domain": (143, "SHOULD"),
    "no-ownerless-cross-module-helper": (144, "MUST NOT"),
    "cross-cutting-owner": (144, "cross-cutting concerns MUST"),
    "sor-state-validation": (147, "MUST"),
    "no-consumer-state-authority": (148, "MUST NOT"),
    "transaction-before-external-effects": (149, "MUST"),
    "one-invariant-owner": (151, "SHOULD"),
    "boundary-validation": (156, "MUST"),
    "contract-publication": (157, "MUST"),
    "contract-schema": (157, "MUST"),
    "contract-semantics": (157, "MUST"),
    "contract-fixtures": (157, "MUST"),
    "contract-checks": (157, "MUST"),
    "contract-metadata": (158, "SHOULD"),
    "canonical-error-mapping": (160, "MUST"),
    "no-raw-error-contract": (160, "MUST NOT"),
    "error-id-governance": (161, "MUST"),
    "error-id-version": (161, "MUST"),
    "error-correlation": (162, "SHOULD"),
    "safe-retryability-class": (162, "SHOULD"),
    "safe-validation-diagnostics": (163, "SHOULD"),
    "non-schema-semantics": (167, "MUST"),
    "timeout-cancellation-contract": (168, "MUST"),
    "automated-success-failure-fixtures": (169, "SHOULD"),
    "retryable-write-idempotency": (172, "MUST"),
    "dedup-window-or-prevent-late-retries": (173, "MUST"),
    "key-source-lifetime": (174, "MUST"),
    "dedup-scope": (174, "MUST"),
    "canonical-request-comparison": (174, "MUST"),
    "key-conflict-policy": (174, "MUST"),
    "response-replay-semantics": (174, "MUST"),
    "replay-storage-policy": (174, "MUST"),
    "explicit-key-when-no-safe-implicit-idempotency": (181, "MUST"),
    "reject-invalid-key": (181, "MUST"),
    "external-side-effect-dedup": (182, "MUST"),
    "nonretryable-when-no-safe-dedup": (183, "MUST"),
    "prevent-unsafe-retries-every-layer": (183, "MUST"),
    "deterministic-documented-conflict": (184, "MUST"),
    "minimal-request-hash": (185, "SHOULD"),
    "sensitive-replay-body-controls": (185, "SHOULD"),
    "standard-key-transport": (186, "SHOULD"),
    "opaque-key": (187, "MUST"),
    "no-key-secrets-pii": (187, "MUST NOT"),
    "no-full-key-log": (187, "MUST NOT"),
    "no-key-metric-analytics": (188, "MUST NOT"),
    "operator-replay-new-key-or-retain-dedup": (189, "MUST"),
    "key-operation-scope": (190, "SHOULD"),
    "model-output-before-state-effects": (193, "MUST"),
    "bounded-observable-repair": (194, "MUST"),
    "stable-model-prompt-config-id": (195, "MUST"),
    "privacy-safe-repro-diagnostics": (196, "SHOULD"),
    "job-id": (202, "MUST"),
    "job-type": (202, "MUST"),
    "job-schema-version": (202, "MUST"),
    "job-status": (202, "MUST"),
    "job-timestamps": (202, "MUST"),
    "job-attempt-retry-metadata": (202, "MUST"),
    "job-budget-summary": (202, "MUST"),
    "job-artifact-references": (202, "MUST"),
    "job-typed-error": (202, "MUST"),
    "job-correlation": (202, "MUST"),
    "safe-inspectable-job": (214, "SHOULD"),
    "idempotent-job-transitions": (215, "MUST"),
    "defined-job-machine": (215, "MUST"),
    "no-job-time-travel": (216, "MUST NOT"),
    "small-job-status-enum": (217, "SHOULD"),
    "versioned-job-hub-artifacts": (218, "SHOULD"),
    "full-pipeline-result-every-attempt": (224, "MUST"),
    "no-last-run-only-terminality": (235, "MUST NOT"),
    "retry-cancel-terminal-state": (235, "MUST consider"),
    "retry-state-when-attempts-remain": (242, "SHOULD"),
    "normalized-run-error": (246, "MUST"),
    "structured-nonfatal-diagnostics": (247, "SHOULD"),
    "identical-derived-job-result": (253, "MUST"),
    "derived-result-not-canonical": (253, "MUST NOT"),
    "stage-retry-class": (258, "MUST"),
    "bounded-jitter-backoff": (259, "MUST"),
    "poison-message-handling": (260, "MUST"),
    "at-least-once-dedup": (261, "SHOULD"),
    "transactional-state-driven-events": (262, "SHOULD"),
    "best-effort-cancellation": (265, "SHOULD"),
    "job-type-budgets": (266, "MUST"),
    "budget-classified": (267, "MUST"),
    "hard-budget-stop": (268, "MUST"),
    "hard-budget-no-effects": (268, "MUST"),
    "hard-budget-terminal": (268, "MUST"),
    "hard-budget-diagnostic": (268, "MUST"),
    "hard-budget-safe-outcome": (268, "MUST"),
    "soft-budget-diagnostic": (269, "MUST"),
    "soft-budget-documented-lifecycle": (269, "MUST"),
    "soft-budget-justification": (269, "SHOULD"),
    "budget-envelope-metrics": (270, "MUST"),
    "in-loop-stage-budget-check": (271, "SHOULD"),
    "concurrency-backpressure-limits": (272, "MUST"),
    "explicit-backpressure-behavior": (273, "SHOULD"),
    "observable-backpressure": (274, "MUST"),
    "rolling-schema-compatibility": (279, "MUST"),
    "repeatable-automated-migration": (280, "MUST"),
    "avoid-or-review-production-locks": (281, "SHOULD"),
    "plan-index-migration-impact": (282, "SHOULD"),
    "persisted-external-schema-version": (285, "MUST"),
    "artifact-retention-deletion": (286, "MUST"),
    "sensitive-encryption-or-approved-exception": (287, "MUST"),
    "artifact-key-ownership-rotation": (288, "SHOULD"),
    "sor-authorization": (293, "MUST"),
    "stable-governed-permission-ids": (294, "MUST"),
    "auditable-auth-decisions": (295, "SHOULD"),
    "high-risk-audit-event": (298, "SHOULD"),
    "safe-audit-payload": (299, "MUST"),
    "end-to-end-correlation": (304, "MUST"),
    "structured-state-error-events": (305, "MUST"),
    "standard-log-fields": (306, "SHOULD"),
    "verify-unit": (309, "MUST"),
    "verify-contract": (309, "MUST"),
    "verify-build": (309, "MUST"),
    "verify-static": (309, "MUST"),
    "hermetic-verify": (310, "SHOULD"),
    "versioned-operational-conventions": (313, "SHOULD"),
}
BACKEND_ALIASES = (
    ("0006", ("das.architecture-modularity.sdmm.enforce-graph",)),
    ("0006", ("das.architecture-modularity.sdmm.public-imports", "das.architecture-modularity.sdmm.no-deep-imports")),
    ("0006", ("das.architecture-modularity.sdmm.ci-boundary-tools",)),
    ("0013", ("das.contracts-compatibility.contract.job-profile", "das.contracts-compatibility.contract.job-config-identity")),
)

DATA_LEAVES = (
    ("manifest-metadata-only", "0040", 435, "metadata only", "MUST", ("activity.dataset_manifest",)),
    ("no-raw-content-in-manifest", "0040", 435, "MUST NOT embed raw dataset contents", "MUST", ("activity.dataset_manifest",)),
    ("manifest-schema-version", "0040", 436, "format/schema MUST be versioned", "MUST", ("activity.dataset_manifest",)),
    ("manifest-ci-validation", "0040", 436, "validated (schema check) in CI", "MUST", ("activity.dataset_manifest",)),
    ("dataset-manifest-required", "0040", 437, "Every dataset used in development, evaluation, or gating MUST include a machine-readable manifest", "MUST", ("activity.dataset_in_use",)),
    ("manifest-schema-field", "0040", 438, "manifest schema version", "MUST", ("activity.dataset_manifest",)),
    ("manifest-dataset-identity", "0040", 439, "`datasetId` and `datasetVersion`", "MUST", ("activity.dataset_manifest",)),
    ("manifest-owner-contact", "0040", 440, "owner and point-of-contact", "MUST", ("activity.dataset_manifest",)),
    ("manifest-record-schema", "0040", 444, "schema/field definitions (or pointer to schema)", "MUST", ("activity.dataset_manifest",)),
    ("manifest-split-policy", "0040", 445, "split policy (train/val/test) where applicable", "MUST", ("activity.dataset_manifest", "dataset.split_policy_applicable")),
    ("manifest-sensitivity-access", "0040", 446, "PII/sensitivity classification and access level", "MUST", ("activity.dataset_manifest",)),
    ("gating-hash-preferred", "0040", 449, "`contentHash` SHOULD be used for CI/release gating when feasible", "SHOULD", ("activity.gating_dataset", "dataset.content_hash_feasible")),
    ("gating-snapshot-when-hash-infeasible", "0040", 450, "`snapshotId` MUST be used for CI/release gating if `contentHash` is not feasible", "MUST", ("activity.gating_dataset", "dataset.content_hash_infeasible")),
    ("governed-immutable-snapshot", "0040", 450, "immutable snapshot identifier from a governed system", "MUST", ("activity.dataset_manifest", "dataset.snapshot_id_used")),
    ("optional-uri-immutable-same-bytes", "0040", 451, "immutable/versioned and MUST correspond to the same bytes", "MUST", ("activity.dataset_manifest", "dataset.storage_uri_present")),
    ("snapshot-system-guarantees", "0040", 452, "snapshot system and immutability guarantees", "MUST", ("activity.dataset_manifest", "dataset.snapshot_id_used")),
    ("manifest-retention-deletion-owner", "0040", 453, "retention window and deletion contact/owner", "MUST", ("activity.dataset_manifest",)),
    ("manifest-known-limitations", "0040", 454, "known limitations", "SHOULD", ("activity.dataset_manifest",)),
    ("all-dataset-provenance-license", "0041", 457, "Every dataset MUST document source/provenance and license/terms", "MUST", ("activity.dataset_in_use",)),
    ("no-unclear-license-production-distribution", "0041", 458, "MUST NOT be used for production decision-making or distributed outside approved scopes", "MUST", ("activity.dataset_production_decision_or_external_distribution", "dataset.licensing_unclear")),
    ("no-production-pii-in-repo", "0042", 461, "Raw production PII MUST NOT be committed to repos", "MUST", ("activity.dataset_repository_content",)),
    ("scrubbed-eval-datasets-fixtures", "0042", 462, "scrubbed/minimized", "MUST", ("activity.eval_dataset_or_fixture",)),
    ("least-privilege-eval-data", "0042", 462, "access-controlled by least privilege", "MUST", ("activity.eval_dataset_or_fixture",)),
    ("broad-access-synthetic-or-deidentified", "0042", 463, "synthetic or de-identified datasets", "SHOULD", ("activity.dataset_broad_developer_access",)),
    ("sensitive-debug-access-approval", "0042", 465, "explicit access approvals", "MUST", ("activity.sensitive_debug_capture",)),
    ("sensitive-debug-retention", "0042", 466, "tight retention windows", "MUST", ("activity.sensitive_debug_capture",)),
    ("sensitive-debug-redaction-or-encryption", "0042", 467, "redaction or encryption controls", "MUST", ("activity.sensitive_debug_capture",)),
    ("sensitive-debug-deletion-path", "0042", 468, "documented deletion path", "MUST", ("activity.sensitive_debug_capture",)),
    ("gating-dataset-versioned-immutable", "0043", 471, "versioned and immutable", "MUST", ("activity.gating_dataset",)),
    ("dataset-update-version-change", "0043", 472, "version MUST change", "MUST", ("activity.dataset_update",)),
    ("no-gating-in-place-edit", "0043", 472, "in-place edits are prohibited for gating sets", "MUST", ("activity.gating_dataset_update",)),
    ("stable-gating-splits", "0043", 473, "stable splits for gating sets", "SHOULD", ("activity.gating_dataset",)),
    ("dataset-and-derived-retention-deletion", "0044", 476, "including derived artifacts (indexes, embeddings, cached generations)", "MUST", ("activity.dataset_in_use",)),
    ("required-deletion-audit", "0044", 477, "lightweight audit trail when compliance requires it", "SHOULD", ("activity.dataset_deletion", "compliance.deletion_audit_required")),
    ("eval-determinism-tier", "0045", 482, "determinism tier for every eval suite", "MUST", ("activity.eval_suite",)),
    ("stable-decision-report-tier", "0045", 483, "stable tiers", "SHOULD", ("activity.gating_or_shared_reporting_eval_suite",)),
    ("metric-rubric-definition", "0046", 492, "clear definitions (what is measured and how)", "MUST", ("activity.eval_suite",)),
    ("metric-rubric-threshold", "0046", 493, "thresholds (pass/fail or tiers)", "MUST", ("activity.eval_suite",)),
    ("metric-rubric-sampling", "0046", 494, "sampling policy", "MUST", ("activity.eval_suite",)),
    ("metric-rubric-report-schema", "0046", 495, "reporting schema", "MUST", ("activity.eval_suite",)),
    ("gating-eval-local-pinned", "0046", 496, "runnable locally with pinned versions", "MUST", ("activity.gating_eval",)),
    ("shared-scoring-artifact", "0047", 499, "version-pinned scoring artifact", "SHOULD", ("activity.shared_scoring_logic",)),
    ("lightweight-hub-scoring", "0047", 500, "small and dependency-light (package or equivalent) and referenced from the contract hub", "SHOULD", ("activity.shared_scoring_artifact",)),
    ("gating-scoring-version-pin", "0047", 501, "version-pinned (no implicit `latest`)", "MUST", ("activity.gating_scoring_artifact",)),
    ("gating-scoring-run-version", "0047", 501, "version used MUST be recorded in eval run manifests", "MUST", ("activity.gating_scoring_artifact",)),
    ("no-private-only-success", "0047", 502, "MUST NOT exist only as private scripts", "MUST", ("activity.eval_success_criteria",)),
    ("small-deterministic-ci-eval", "0048", 506, "small deterministic CI eval set", "SHOULD", ("activity.eval_program",)),
    ("larger-offline-benchmark", "0048", 507, "larger offline benchmark", "SHOULD", ("activity.eval_program",)),
    ("no-unstable-gating-network", "0048", 508, "avoid reliance on unstable third-party network calls; use stubs/snapshots", "MUST", ("activity.gating_eval",)),
    ("stochastic-trial-count", "0049", 513, "number of trials", "SHOULD", ("activity.stochastic_eval",)),
    ("stochastic-aggregation", "0049", 514, "aggregation method", "SHOULD", ("activity.stochastic_eval",)),
    ("stochastic-variance-tolerance", "0049", 515, "acceptable variance/tolerance bands", "SHOULD", ("activity.stochastic_eval",)),
    ("stochastic-regression-detection", "0049", 516, "regression detection method", "SHOULD", ("activity.stochastic_eval",)),
    ("explicit-regression-budgets", "0050", 519, "explicit regression budgets", "MUST", ("activity.eval_suite",)),
    ("promote-stable-owned-evals", "0050", 522, "once stable, trusted, and owned", "SHOULD", ("activity.eval_gate_promotion",)),
    ("label-guidelines-examples-edge-cases", "0051", 527, "labeling guidelines, examples, and edge-case handling", "MUST", ("activity.dataset_labeling",)),
    ("subjective-label-agreement", "0051", 528, "inter-annotator agreement checks for subjective labels", "SHOULD", ("activity.subjective_labeling",)),
    ("label-process-dataset-version", "0051", 529, "labeling process changes as part of dataset versioning", "MUST", ("activity.labeling_process_change",)),
    ("eval-run-dataset-immutable-identity", "0052", 535, "`datasetId`, `datasetVersion`, and an immutable dataset pointer", "MUST", ("activity.eval_run",)),
    ("eval-run-scoring-version", "0052", 536, "scoring artifact version (if applicable)", "MUST", ("activity.eval_run", "eval.scoring_artifact_used")),
    ("eval-run-code-version", "0052", 537, "code version (git SHA/build version)", "MUST", ("activity.eval_run",)),
    ("eval-run-model-prompt-config-sampling", "0052", 538, "model/prompt/config identifiers (including sampling parameters", "MUST", ("activity.eval_run",)),
    ("eval-run-retrieval-snapshot", "0052", 538, "retrieval snapshot/version where applicable", "MUST", ("activity.eval_run", "eval.retrieval_snapshot_applicable")),
    ("eval-run-seeds-when-used", "0052", 539, "random seeds (if any)", "MUST", ("activity.eval_run", "eval.random_seeds_used")),
    ("eval-run-tier", "0052", 539, "determinism tier", "MUST", ("activity.eval_run",)),
    ("eval-run-environment-fingerprint", "0052", 540, "environment fingerprint (optional but recommended)", "SHOULD", ("activity.eval_run",)),
    ("eval-run-replay", "0052", 541, "reproduces a run within the declared determinism tier", "SHOULD", ("activity.eval_run",)),
    ("no-raw-sensitive-report-default", "0053", 544, "avoid exposing raw sensitive examples by default", "MUST", ("activity.eval_report",)),
    ("aggregate-redacted-report", "0053", 545, "aggregate metrics and redacted snippets under access control", "SHOULD", ("activity.eval_qualitative_debug_report",)),
)
DATA_FORCE = {
    "manifest-metadata-only": (435, "MUST"),
    "no-raw-content-in-manifest": (435, "MUST NOT"),
    "manifest-schema-field": (437, "MUST"),
    "manifest-dataset-identity": (437, "MUST"),
    "manifest-owner-contact": (437, "MUST"),
    "manifest-record-schema": (437, "MUST"),
    "manifest-split-policy": (437, "MUST"),
    "manifest-sensitivity-access": (437, "MUST"),
    "snapshot-system-guarantees": (437, "MUST"),
    "manifest-retention-deletion-owner": (437, "MUST"),
    "no-unclear-license-production-distribution": (458, "MUST NOT"),
    "no-production-pii-in-repo": (461, "MUST NOT"),
    "sensitive-debug-access-approval": (464, "MUST"),
    "sensitive-debug-retention": (464, "MUST"),
    "sensitive-debug-redaction-or-encryption": (464, "MUST"),
    "sensitive-debug-deletion-path": (464, "MUST"),
    "metric-rubric-definition": (491, "MUST"),
    "metric-rubric-threshold": (491, "MUST"),
    "metric-rubric-sampling": (491, "MUST"),
    "metric-rubric-report-schema": (491, "MUST"),
    "no-private-only-success": (502, "MUST NOT"),
    "small-deterministic-ci-eval": (505, "SHOULD"),
    "larger-offline-benchmark": (505, "SHOULD"),
    "stochastic-trial-count": (512, "SHOULD"),
    "stochastic-aggregation": (512, "SHOULD"),
    "stochastic-variance-tolerance": (512, "SHOULD"),
    "stochastic-regression-detection": (512, "SHOULD"),
    "eval-run-dataset-immutable-identity": (534, "MUST"),
    "eval-run-scoring-version": (534, "MUST"),
    "eval-run-code-version": (534, "MUST"),
    "eval-run-model-prompt-config-sampling": (534, "MUST"),
    "eval-run-retrieval-snapshot": (534, "MUST"),
    "eval-run-seeds-when-used": (534, "MUST"),
    "eval-run-tier": (534, "MUST"),
    "eval-run-environment-fingerprint": (540, "recommended"),
}
DATA_ALIASES = (
    ("0040", ("das.contracts-compatibility.contract.dataset-intended-use", "das.contracts-compatibility.contract.dataset-provenance", "das.contracts-compatibility.contract.dataset-license", "das.contracts-compatibility.contract.dataset-content-identity", "das.contracts-compatibility.contract.dataset-hash-method")),
    ("0049", ("das.ai-runtime-evaluation.data.eval-determinism-tier",)),
)

INTEGRATION_LEAVES = (
    ("one-command-startup", "0028", 330, "one-command startup for local development", "MUST", ("activity.integration_harness",)),
    ("minimal-smoke-services", "0028", 331, "minimal set of services required for smoke tests", "MUST", ("activity.integration_harness",)),
    ("local-first-dependencies", "0028", 332, "minimal, local-first dependency set", "SHOULD", ("activity.integration_harness",)),
    ("local-ci-same-commands", "0029", 337, "same smoke/compat checks as local using the same commands", "SHOULD", ("activity.integration_harness",)),
    ("parity-divergence-documented", "0029", 338, "divergence MUST be documented", "MUST", ("activity.integration_harness", "harness.local_ci_divergence")),
    ("parity-divergence-tested", "0029", 338, "and tested", "MUST", ("activity.integration_harness", "harness.local_ci_divergence")),
    ("component-contract-image-pins", "0030", 341, "versions/tags/commits for each component it wires together", "MUST", ("activity.integration_harness",)),
    ("shared-ci-image-digests", "0030", 342, "container images MUST be pinned by immutable digest", "MUST", ("activity.harness_ci_or_shared_environment",)),
    ("pins-manifest-emitted-retained", "0030", 343, "single machine-readable “pins manifest”", "SHOULD", ("activity.integration_harness",)),
    ("no-implicit-ci-latest", "0030", 344, "deterministic pins (no implicit “latest” tags)", "MUST", ("activity.harness_ci",)),
    ("local-pin-override", "0030", 345, "support “pin to local” for active development while keeping CI pins deterministic", "SHOULD", ("activity.harness_local_development",)),
    ("minimal-critical-smoke-suite", "0031", 350, "most important end-to-end flows", "MUST", ("activity.integration_harness",)),
    ("deterministic-smoke", "0031", 351, "deterministic and non-flaky", "SHOULD", ("activity.integration_harness",)),
    ("smoke-runnable-in-ci", "0031", 352, "Smoke tests MUST be runnable in CI", "MUST", ("activity.integration_harness",)),
    ("smoke-default-branch-pr", "0031", 353, "pull requests (PRs) targeting the default branch", "SHOULD", ("activity.integration_harness",)),
    ("merge-smoke-if-not-every-pr", "0031", 354, "run on merges to the default branch", "MUST", ("activity.integration_harness", "harness.smoke_not_every_pr")),
    ("daily-smoke-if-not-every-pr", "0031", 355, "at least daily on the default branch", "SHOULD", ("activity.integration_harness", "harness.smoke_not_every_pr")),
    # I4a's MUST label governs coverage with the documented API alternative;
    # its body keeps the SHOULD recommendation for the browser mechanism.
    ("browser-smoke-or-api-rationale", "0032", 360, "SHOULD include at least one **browser-level** smoke scenario (`smoke-ui`) for each canonical workflow (or document why API-level smoke is sufficient).", "MUST", ("activity.integration_harness", "surface.ui")),
    ("stable-ui-selectors", "0032", 361, "use stable selectors", "MUST", ("activity.harness_ui_smoke",)),
    ("ui-screen-id-alignment", "0032", 361, "SHOULD align with the UI Spec Appendix’s Screen IDs", "SHOULD", ("activity.harness_ui_smoke",)),
    ("ui-failure-artifacts", "0032", 362, "diagnosable artifacts (screenshot + trace/DOM snapshot where supported)", "MUST", ("activity.harness_ui_smoke_failure",)),
    ("ui-failure-correlation", "0032", 362, "surface correlation/request IDs", "MUST", ("activity.harness_ui_smoke_failure",)),
    ("deterministic-ui-smoke", "0032", 363, "seeded/scrubbed data, pinned versions, and stubs/snapshots", "SHOULD", ("activity.harness_ui_smoke",)),
    ("ui-workflow-screen-mapping", "0032", 364, "explicitly mapped to workflows/screens", "SHOULD", ("activity.harness_ui_smoke",)),
    ("failure-scenario-correlation", "0032", 366, "scenario name and correlation IDs", "MUST", ("activity.harness_test_failure",)),
    ("ci-failure-artifacts", "0032", 367, "Persist failure artifacts in CI", "SHOULD", ("activity.harness_ci_test_failure",)),
    ("critical-consumer-golden-decode", "0033", 378, "consumer decoding tests against golden fixtures", "MUST", ("activity.harness_critical_boundary",)),
    ("happy-and-representative-failure", "0033", 379, "both happy-path and representative failures", "SHOULD", ("activity.harness_critical_boundary",)),
    ("contract-change-fixtures", "0033", 380, "update fixtures", "MUST", ("activity.harness_contract_change",)),
    ("contract-change-checks", "0033", 380, "required checks", "MUST", ("activity.harness_contract_change",)),
    ("stable-contract-n-with-n-minus-one", "0034", 383, "“N with N-1” (or equivalent) for stable contracts", "SHOULD", ("activity.harness_stable_contract",)),
    ("supported-window-documented-tested", "0034", 385, "document it and test within it", "SHOULD", ("activity.integration_harness", "contract.supported_window_exists")),
    ("deterministic-scrubbed-seeds", "0035", 390, "deterministic and scrubbed of PII", "MUST", ("activity.integration_harness",)),
    ("quick-seed-reset", "0035", 391, "reset to a known state quickly", "SHOULD", ("activity.integration_harness",)),
    ("no-manual-local-state", "0035", 392, "MUST NOT depend on manual local state or operator steps", "MUST", ("activity.integration_harness",)),
    ("ephemeral-ci-environment", "0036", 395, "ephemeral CI environments", "SHOULD", ("activity.harness_ci",)),
    ("shared-data-namespace-cleanup", "0036", 396, "namespace their data and clean up reliably", "MUST", ("activity.harness_shared_environment",)),
    ("critical-flow-performance-guard", "0037", 401, "at least one guard for a critical flow", "SHOULD", ("activity.integration_harness",)),
    ("canonical-harness-commands", "0038", 407, "canonical commands (or equivalents)", "SHOULD", ("activity.integration_harness",)),
    ("ci-system-authority", "0039", 415, "authoritative for system integration", "MUST", ("activity.integration_harness", "activity.harness_ci")),
    ("slow-check-small-pr-larger-merge", "0039", 416, "When a harness check is too slow for every PR", "SHOULD", ("activity.integration_harness", "harness.slow_check_exists")),
)
INTEGRATION_FORCE = {
    "browser-smoke-or-api-rationale": (360, "MUST"),
    "no-manual-local-state": (392, "MUST NOT"),
}
PLATFORM_LEAVES = (
    ("verify-pr-default-merge-release", "0054", 564, "every pull request targeting the default branch and on every merge to the default branch (e.g., `main`) and any release branch", "MUST", ("activity.repository_verification",)),
    ("hermetic-verify", "0054", 565, "no calls to external SaaS APIs", "SHOULD", ("activity.repository_verification",)),
    ("layered-verification", "0055", 568, "layered verification", "SHOULD", ("activity.repository_verification",)),
    ("dependency-and-tool-locks", "0056", 575, "Pin dependencies and tool versions (lockfiles)", "MUST", ("activity.repository_build",)),
    ("reproducible-generated-code", "0056", 576, "Generated code MUST be reproducible", "MUST", ("activity.repository_codegen",)),
    ("ci-codegen-reproducibility", "0056", 577, "CI MUST verify deterministic codegen outputs", "MUST", ("activity.repository_codegen",)),
    ("no-hand-edited-generated-artifact", "0056", 578, "MUST NOT be manually edited", "MUST", ("activity.repository_codegen",)),
    ("generated-handwritten-separated", "0056", 578, "clearly separated from hand-written code", "MUST", ("activity.repository_codegen",)),
    ("local-ci-reproducible-build", "0056", 579, "reproducible across local and CI", "SHOULD", ("activity.repository_build",)),
    ("build-runtime-metadata", "0056", 580, "build ID, git SHA, contract versions, and the `profileId`/`configId`", "SHOULD", ("activity.repository_build",)),
    ("production-sbom-when-feasible", "0056", 581, "SBOM for production artifacts where feasible", "SHOULD", ("activity.production_artifact", "build.sbom_feasible")),
    ("production-signed-provenance-when-feasible", "0056", 582, "signed build provenance/attestations", "SHOULD", ("activity.production_artifact", "build.signed_provenance_feasible")),
    ("rolling-unless-enforced-atomic", "0057", 585, "rolling deploys and partial upgrades unless you can enforce atomic cutover", "MUST", ("activity.release_rollout",)),
    ("rollout-public-contract-compatibility", "0057", 586, "backward compatible across the rollout window", "MUST", ("activity.public_contract_rollout",)),
    ("safe-rollout-strategy", "0057", 587, "Prefer one of", "SHOULD", ("activity.release_rollout",)),
    ("release-code-config-flag-rollback", "0057", 590, "rollback plan covering code, config, and flags", "MUST", ("activity.release_rollout",)),
    ("breaking-migration-cutoff-adoption-telemetry", "0057", 591, "explicit cutoffs and telemetry proving adoption", "SHOULD", ("activity.contract_breaking_release",)),
    ("flag-owner-default-rollout-sunset", "0058", 594, "owner, default value, rollout plan, and sunset plan", "MUST", ("activity.feature_flag",)),
    ("high-risk-flag-audit", "0058", 595, "auditable (who changed what, when)", "MUST", ("activity.high_risk_feature_flag",)),
    ("flag-deploy-release-separation", "0058", 596, "using flags for risky behavior changes", "SHOULD", ("activity.risky_behavior_release",)),
    ("owned-flag-removal", "0058", 597, "first-class maintenance work; unowned flags are defects", "SHOULD", ("activity.feature_flag",)),
    ("startup-runtime-config-validation", "0059", 600, "schema-validated at startup (fail fast for invalid config)", "MUST", ("activity.runtime_configuration",)),
    ("runtime-config-version", "0059", 601, "explicit config ID/version", "MUST", ("activity.runtime_configuration",)),
    ("typed-config-migrations", "0059", 602, "typed config + migrations", "SHOULD", ("activity.runtime_configuration",)),
    ("security-privacy-spend-config-audit", "0059", 603, "security, privacy, or spend MUST be auditable", "MUST", ("activity.security_privacy_or_spend_config_change",)),
    ("migration-deploy-order", "0060", 606, "controlled step with clear ordering relative to app deploy", "MUST", ("activity.database_migration",)),
    ("expand-contract-schema-evolution", "0060", 607, "Expand/contract rules MUST be followed", "MUST", ("activity.database_schema_evolution",)),
    ("destructive-migration-extra-review", "0060", 608, "explicit annotation and extra review gates", "SHOULD", ("activity.destructive_database_migration",)),
    ("automated-contract-publish-upgrade", "0061", 611, "automation to publish contract artifacts and open consumer upgrade PRs", "SHOULD", ("activity.contract_release",)),
    ("stable-contract-actual-producer", "0061", 612, "at least one producer deployment supports it in shared environments", "MUST", ("activity.stable_contract_publish_or_advertise",)),
    ("small-upgrade-compatibility-check", "0061", 614, "compatibility checks on every contract bump", "SHOULD", ("activity.contract_upgrade",)),
    ("critical-operation-slos", "0062", 619, "critical user-facing operations", "SHOULD", ("activity.critical_user_facing_operation",)),
    ("slo-alert-error-budget", "0062", 620, "alert policies and error budgets", "SHOULD", ("activity.service_level_objective",)),
    ("owned-actionable-alert", "0062", 621, "actionable and owned", "MUST", ("activity.alerting",)),
    ("service-four-golden-signals", "0063", 624, "latency, error rate, throughput, saturation", "MUST", ("activity.service_operation",)),
    ("relevant-ai-signals", "0063", 625, "AI-specific signals where relevant", "SHOULD", ("activity.ai_service_observability",)),
    ("sync-async-correlation", "0064", 633, "across sync and async boundaries (jobs, callbacks, queues)", "MUST", ("activity.service_sync_or_async_boundary",)),
    ("safe-user-error-trace-id", "0064", 634, "user-visible error reports where safe", "SHOULD", ("activity.safe_user_visible_error_report",)),
    ("no-observability-secrets", "0064", 635, "MUST NOT contain secrets", "MUST", ("activity.observability_emission",)),
    ("no-unprotected-sensitive-observability", "0064", 636, "MUST NOT contain raw sensitive user content unless explicitly required and protected", "MUST", ("activity.observability_emission",)),
    ("internet-size-timeout-rate-limits", "0065", 639, "request size limits, timeouts, and rate limits at internet-facing boundaries", "MUST", ("activity.internet_facing_boundary",)),
    ("multi-tenant-budgets", "0065", 640, "per-tenant budgets in multi-tenant systems", "SHOULD", ("activity.multi_tenant_service",)),
    ("explicit-typed-limit-budget-enforcement", "0065", 641, "explicit and typed", "MUST", ("activity.limit_or_budget_enforcement",)),
    ("hard-exhaustion-fast-terminal-diagnostic", "0065", 642, "fail fast (or terminate a job) with a stable, diagnosable outcome and stable diagnostic codes", "MUST", ("activity.hard_limit_or_budget_exhaustion",)),
    ("soft-budget-explicit-lifecycle", "0065", 643, "MUST be explicitly documented", "MUST", ("activity.soft_budget",)),
    ("soft-exceeded-diagnostic-metric", "0065", 643, "emit stable diagnostics/metrics", "MUST", ("activity.soft_budget_exceeded",)),
    ("exhaustion-no-crash-typed-outcome", "0065", 644, "MUST NOT crash the process", "MUST", ("activity.limit_or_budget_exhaustion",)),
    ("exhaustion-sync-contract-outcome", "0065", 645, "stable error envelope/code (and an HTTP status consistent with your contract", "MUST", ("activity.synchronous_limit_or_budget_exhaustion",)),
    ("exhaustion-async-terminal-outcome", "0065", 646, "terminal `failed` or `degraded` outcome", "MUST", ("activity.asynchronous_limit_or_budget_exhaustion",)),
    ("safe-degradation-over-retry", "0065", 647, "safe degradation modes", "SHOULD", ("activity.limit_or_budget_enforcement",)),
    ("common-failure-runbooks", "0077", 723, "runbooks for common failure modes", "SHOULD", ("activity.service_operation",)),
    ("production-oncall-escalation", "0077", 728, "on-call and escalation responsibilities for production systems", "MUST", ("activity.production_system",)),
    ("incident-review-owned-corrective-actions", "0078", 731, "contributing factors, and corrective actions with owners/due dates", "SHOULD", ("activity.incident_followup",)),
    ("corrective-contract-evolution", "0078", 732, "change contracts MUST follow contract evolution rules", "MUST", ("activity.incident_contract_change",)),
)
PLATFORM_FORCE = {
    "generated-handwritten-separated": (578, "MUST"),
    "no-hand-edited-generated-artifact": (578, "MUST NOT"),
    "no-observability-secrets": (635, "MUST NOT"),
    "no-unprotected-sensitive-observability": (636, "MUST NOT"),
    "exhaustion-no-crash-typed-outcome": (644, "MUST NOT"),
    "exhaustion-sync-contract-outcome": (644, "MUST"),
    "exhaustion-async-terminal-outcome": (644, "MUST"),
}
OPERATIONAL_LEAVES = (
    ("internet-threat-model-owned-mitigations", "0066", 652, "trust boundaries, attacker goals, critical assets, and mitigations with owners", "MUST", ("activity.internet_facing_system",)),
    ("new-capability-data-flow-threat-update", "0066", 653, "new tool capabilities, data flows, or external integrations", "SHOULD", ("activity.new_tool_data_flow_or_integration",)),
    ("least-privilege-service-job-credentials", "0067", 656, "least-privilege credentials", "MUST", ("activity.service_or_job_execution",)),
    ("runtime-secret-manager-injection", "0067", 657, "secret manager (or equivalent) and injected at runtime", "MUST", ("activity.secret_use",)),
    ("no-secrets-in-source", "0067", 658, "Commit secrets to source control", "MUST", ("activity.repository_content",)),
    ("restricted-audited-ci-credentials", "0067", 659, "Restrict and audit CI credentials", "SHOULD", ("activity.ci_credential_use",)),
    ("protect-used-signing-keys", "0067", 659, "protect signing keys if used", "SHOULD", ("activity.signing_key_use",)),
    ("untrusted-network-tls", "0068", 662, "TLS for in-transit data on untrusted networks", "MUST", ("activity.untrusted_network_transport",)),
    ("network-segmentation-egress", "0068", 663, "network segmentation and egress controls", "SHOULD", ("activity.networked_service",)),
    ("owned-third-party-egress-allowlist", "0068", 664, "explicit allowlist with owners", "SHOULD", ("activity.third_party_egress",)),
    ("untrusted-input-validation-sanitization", "0069", 667, "Validate and sanitize untrusted inputs", "MUST", ("activity.untrusted_input",)),
    ("no-unsafe-deserialization-evaluation", "0069", 668, "unsafe deserialization and unsafe dynamic evaluation", "MUST", ("activity.untrusted_input",)),
    ("untrusted-input-size-limits", "0069", 669, "size limits to prevent resource-exhaustion attacks", "MUST", ("activity.untrusted_input",)),
    ("fail-closed-safe-degradation-no-partial-state", "0069", 670, "while avoiding partial writes or inconsistent state", "SHOULD", ("activity.authorization_or_availability_failure",)),
    ("dependency-container-vulnerability-scans", "0070", 673, "dependency vulnerability scanning and container scanning", "SHOULD", ("activity.software_supply_chain",)),
    ("follow-critical-high-vulnerability-slas", "0070", 674, "vulnerability remediation SLAs (at least for critical/high findings) and follow them", "MUST", ("activity.software_supply_chain",)),
    ("pinned-verified-minimal-base", "0070", 675, "pinned, verified base images and minimal runtimes", "SHOULD", ("activity.container_build",)),
    ("ci-secret-sast-scanning", "0070", 676, "secret scanning and basic SAST checks in CI", "SHOULD", ("activity.ci_verification",)),
    ("untrusted-model-schema", "0071", 680, "model outputs as untrusted and validate against schemas", "MUST", ("activity.llm_tool_retrieval_or_agent", "activity.ai_model_output")),
    ("tool-allowlists-io-schemas", "0071", 681, "tool allowlists and explicit tool input/output schemas", "MUST", ("activity.llm_tool_retrieval_or_agent", "activity.ai_tool_use")),
    ("tool-quotas-timeout-call-bound", "0071", 682, "tool quotas/timeouts and bound the number of tool calls per request/job", "MUST", ("activity.llm_tool_retrieval_or_agent", "activity.ai_tool_use")),
    ("prevent-ai-data-exfiltration", "0071", 683, "Prevent data exfiltration", "MUST", ("activity.llm_tool_retrieval_or_agent",)),
    ("no-tool-secrets-unless-necessary", "0071", 684, "MUST NOT access secrets unless strictly necessary", "MUST", ("activity.llm_tool_retrieval_or_agent", "activity.ai_tool_use")),
    ("retrieval-tenant-user-access", "0071", 685, "access-controlled per tenant/user", "MUST", ("activity.llm_tool_retrieval_or_agent", "activity.ai_retrieval_use")),
    ("prompt-injection-defense", "0071", 686, "Defend against prompt injection", "SHOULD", ("activity.llm_tool_retrieval_or_agent",)),
    ("log-secret-sensitive-redaction", "0072", 693, "redacted for secrets and sensitive data", "MUST", ("activity.log_emission",)),
    ("security-change-audit", "0072", 694, "security-sensitive changes (permissions, keys, flags, high-risk config)", "MUST", ("activity.security_sensitive_change",)),
    ("controlled-audited-log-access", "0072", 695, "controlled and audited", "MUST", ("activity.log_access",)),
    ("sensitive-store-default-encryption", "0073", 698, "encryption at rest by default", "MUST", ("activity.sensitive_data_store",)),
    ("encryption-exception-approval-record-expiry-controls", "0073", 699, "explicitly approved, documented, and time-bounded with compensating controls", "MUST", ("activity.encryption_exception",)),
    ("central-kms-access-rotation-audit", "0073", 700, "centralized KMS", "SHOULD", ("activity.encryption_key_management",)),
    ("no-app-db-secrets-without-protected-purpose", "0073", 704, "MUST NOT be stored in application databases unless explicitly designed for that purpose and protected", "MUST", ("activity.secret_storage",)),
    ("data-minimization-purpose", "0074", 709, "only what is necessary for product function", "MUST", ("activity.user_data_collection_or_storage",)),
    ("separate-telemetry-user-content", "0074", 710, "Separate operational telemetry from user content; avoid logging raw user content by default", "SHOULD", ("activity.operational_telemetry",)),
    ("user-derived-retention", "0075", 713, "retention windows for user data and derived artifacts", "MUST", ("activity.user_or_derived_data_storage",)),
    ("primary-derived-deletion", "0075", 714, "primary and derived data (indexes, embeddings, caches) where applicable", "MUST", ("activity.deletable_user_or_derived_data",)),
    ("no-sensitive-analytics-payload", "0076", 717, "Analytics events MUST avoid sensitive payloads", "MUST", ("activity.analytics_emission",)),
    ("decision-analytics-stable-versioned-schema", "0076", 718, "stable event schemas and versioning", "SHOULD", ("activity.analytics_used_for_decisions",)),
)
OPERATIONAL_FORCE = {
    "no-secrets-in-source": (658, "MUST NOT"),
    "no-tool-secrets-unless-necessary": (684, "MUST NOT"),
    "no-app-db-secrets-without-protected-purpose": (704, "MUST NOT"),
}
PRINCIPLES_LEAVES = (
    ("keyword-synonym-interpretation", "0001", 18, "interpreted as the corresponding BCP 14 keyword", "MUST", ("activity.normative_interpretation",)),
    ("prefer-primary-keywords", "0001", 18, "authors SHOULD prefer the primary keywords", "SHOULD", ("activity.normative_authoring",)),
    ("no-repo-rule-weakening", "0004", 48, "MUST NOT weaken higher-priority requirements", "MUST", ("activity.repo_specific_principle",)),
    ("should-deviation-justification-controls", "0005", 58, "documented with justification and compensating controls", "MUST", ("activity.principles_should_deviation",)),
    ("must-exception-owner-approval", "0005", 60, "approved by the appropriate owner (security/compliance where applicable)", "MUST", ("activity.principles_must_exception",)),
    ("must-exception-scope-duration-rationale-controls", "0005", 61, "scope, duration, rationale, compensating controls", "MUST", ("activity.principles_must_exception",)),
    ("must-exception-sunset", "0005", 62, "sunset plan", "MUST", ("activity.principles_must_exception",)),
    ("no-policy-law-violating-exception", "0005", 63, "MUST NOT violate applicable law/regulation or organizational security/compliance policy", "MUST", ("activity.principles_exception",)),
)
PRINCIPLES_FORCE = {
    "no-repo-rule-weakening": (48, "MUST NOT"),
    "no-policy-law-violating-exception": (63, "MUST NOT"),
}
OPERATIONAL_ALIASES = (
    ("0054", ("das.governance.verification-release.verify.one-canonical-entrypoint",)),
    ("0061", ("das.contracts-compatibility.multirepo.consumer-baseline-pin",)),
)


# Full reviewed source ranges retain method choices, severity and examples.
# These are existing F/H/I/J duties, not new frameworks or mandatory layouts.
# Rows: criterion, carrier, body line/phrase, strength, actual facts, full scope,
# force line/phrase. Repeated main-spec obligations reuse IDs below.
PLAYBOOKS = (
    ('das.governance.verification-release', 'tooling', 'legacy-text-33cd7d6c-', (
        *[('lock-' + name, '0001', line, phrase, 'SHOULD', ('activity.repository_verification',) + extra, (12, 19), (12, 'SHOULD'))
          for name, line, phrase, extra in (
            ('standard-version', 14, 'standard manifest version', ()),
            ('verify-runtime', 15, 'verify runtime ref', ()),
            ('environment-source', 16, 'source-of-truth ref for the repo-local verify environment', ()),
            ('core-versions', 17, 'core tool versions', ()),
            ('generator-policy-versions', 18, 'when they materially affect outputs', ('tooling.generator_or_policy_affects_outputs',)),
            ('mirror-snapshot-purpose', 19, 'originating snapshot ref and mirror purpose', ('activity.governed_artifact_mirror',)),
        )],
        *[('report-' + name, '0012', line, phrase, 'SHOULD', ('activity.governed_verify_report',) + extra, (99, 107), (99, 'SHOULD'))
          for name, line, phrase, extra in (
            ('expected', 101, 'whether the gate was expected', ()),
            ('executed', 102, 'whether it executed', ()),
            ('artifact-count-refs', 104, 'artifact count / refs', ()),
            ('fail-open-notes', 105, 'any fail-open prevention notes', ('gate.fail_open_notes_applicable',)),
        )],
        *[('ship-' + name, '0014', line, phrase, 'SHOULD', ('activity.governed_release',), (111, 115), (111, 'SHOULD'))
          for name, line, phrase in (
            ('registry', 113, 'actual `verify_registry.json`'),
            ('snapshot', 114, 'actual `release_snapshot_manifest.json`'),
            ('schema-examples', 115, 'examples for the shipped schemas'),
        )],
        *[('self-check-' + name, '0015', line, phrase, 'SHOULD', ('activity.governed_release_self_check',), (117, 124), (117, 'SHOULD'))
          for name, line, phrase in (
            ('examples', 122, 'every shipped example validates'),
            ('version', 123, '`VERSION` matches `standard_manifest.json`'),
            ('snapshot-inventory', 124, 'inventories the shipped bundle consistently'),
        )],
        *[('check-' + name, '0017', line, phrase, 'SHOULD', ('activity.tooling_pre_release_or_adoption', key), (137, 148), (137, 'SHOULD'))
          for name, line, phrase, key in (
            ('tooling-lock', 139, 'tooling-lock schema validation', 'tooling.standalone_lock_present'),
            ('suite-lock', 140, 'suite-lock schema validation', 'tooling.suite_lock_present'),
            ('version-closure', 141, 'suite version closure schema validation', 'tooling.version_closure_present'),
            ('verify-registry', 142, 'verify-registry schema validation', 'tooling.verify_registry_present'),
            ('verify-report', 143, 'verify-report schema validation (for emitted reports)', 'tooling.verify_report_emitted'),
            ('pinned-refs', 144, 'pinned-ref semantic checks', 'tooling.structured_refs_present'),
            ('manifest', 145, 'machine-readable manifest validation', 'tooling.standard_manifest_present'),
            ('release-completeness', 146, 'release-package completeness audit', 'tooling.release_bundle_present'),
            ('snapshot', 147, 'release snapshot verification', 'tooling.release_snapshot_present'),
            ('mirror', 148, 'mirror provenance checks', 'activity.governed_artifact_mirror'),
        )],
    )),
    ('das.architecture-modularity', 'migration', 'legacy-text-e80f2d11-', (
        ('required-playbook', 'legacy-guide-e80f2d11-required', 7, 'Use this playbook', 'MUST', ('change.breaking_persisted_or_cross_repo_contract', 'change.coupled_multi_module_refactor', 'change.major_algorithm_quality_or_cost', 'change.production_adapter_or_prompt_migration'), (5, 12), (5, 'required')),
        ('stable-seam', '0001', 18, 'Keep at least one stable seam', 'MUST', ('activity.sdmm_migration',), (5, 19), (18, 'MUST')),
        ('expand-contract', '0001', 19, 'Prefer “expand/contract”', 'SHOULD', ('activity.sdmm_migration', 'migration.externally_observed'), (5, 19), (19, 'SHOULD')),
        ('golden-expectations', '0002', 60, 'expected outputs (or expected invariants / tolerances)', 'MUST', ('activity.algorithm_pipeline', 'pipeline.tier_0_or_1'), (56, 65), (56, 'mandatory')),
        ('replay-ci-stability', '0002', 61, 'in CI with stable results', 'MUST', ('activity.algorithm_pipeline', 'pipeline.tier_0_or_1'), (56, 65), (56, 'mandatory')),
        ('tier0-offline', '0002', 62, 'fully offline/deterministic (no live network)', 'MUST', ('activity.algorithm_pipeline', 'pipeline.tier_0'), (56, 65), (62, 'MUST')),
        ('tier1-pinned-replay', '0002', 63, 'replayable given **pinned dependencies**', 'MUST', ('activity.algorithm_pipeline', 'pipeline.tier_1'), (56, 65), (63, 'MUST')),
        ('configured-merge-block', '0002', 65, 'failures MUST block merges', 'MUST', ('activity.replay_suite', 'replay.configured_merge_gate'), (56, 65), (65, 'MUST')),
        *[(name, 'legacy-guide-e80f2d11-cutover', line, phrase, 'MUST', ('activity.migration_production_cutover',) + extra, (84, 93), (84, 'minimum')) for name, line, phrase, extra in (
            ('cutover-boundary', 88, 'Boundary lints pass', ()), ('cutover-no-deep-imports', 88, 'no deep imports', ()),
            ('cutover-graph', 88, 'graph enforced', ()), ('cutover-pinned-eval', 89, 'CI eval gates pass on pinned datasets', ()),
            ('cutover-replay', 90, 'Replay harness passes', ('pipeline.tier_0_or_1',)),
            ('cutover-job-observability', 91, 'jobId', ()), ('cutover-run-observability', 91, 'runId', ()),
            ('cutover-manifest-observability', 91, 'manifestHash', ()),
            ('cutover-rollback-documented', 92, 'Rollback path is documented', ()), ('cutover-rollback-tested', 92, 'tested', ()),
            ('cutover-traceability', 93, 'Master Doc traceability index is updated', ()),
        )],
    )),
    ('das.interaction.standard-ui', 'review', 'legacy-text-4d6c4f21-', (
        ('automatable-ci', '0001', 6, 'enforced in CI', 'SHOULD', ('activity.ui_automatable_review',), (5, 7), (6, 'SHOULD')),
        ('judgement-human', '0001', 7, 'reviewed by a human', 'MUST', ('activity.ui_judgement_review',), (5, 7), (7, 'MUST')),
        ('p0-fix', '0002', 11, 'fix before merge/release', 'MUST', ('activity.ui_merge_or_release', 'ui.p0_finding'), (11, 13), (11, 'MUST')),
        ('p1-fix', '0002', 12, 'fix before release', 'SHOULD', ('activity.ui_release', 'ui.p1_finding'), (11, 13), (12, 'SHOULD')),
        *[(name, '0002', 12, phrase, 'MUST', ('ui.p1_finding', 'ui.p1_deferred'), (11, 13), (12, 'may defer only with')) for name, phrase in (
            ('p1-deferred-owner', 'explicit owner'), ('p1-deferred-date', 'due date'), ('p1-deferred-rationale', 'rationale'))],
        *[(name, 'legacy-guide-4d6c4f21-checklist', line, phrase, strength, ('activity.ui_design_review',) + extra, (11, 38), (11 if strength == 'MUST' else 12, strength)) for name, line, phrase, strength, extra in (
            ('shared-tokens-or-prototype-exception', 19, 'approved design tokens', 'MUST', ('activity.shared_ui_surface',)),
            ('token-contract-version', 20, 'Token contract is versioned', 'MUST', ('activity.ui_token_contract',)),
            ('token-canonical-no-drift', 20, 'consumed from the canonical source (no drift between design and code)', 'MUST', ('activity.ui_token_contract',)),
            ('semantic-cta-colors', 21, 'Primary/Secondary/Tertiary/Danger semantics are consistent', 'MUST', ()),
            ('text-contrast', 22, 'Text, icons, borders meet contrast baseline', 'MUST', ()),
            ('visible-placeholders', 22, 'placeholders are visible', 'MUST', ()),
            ('keyboard-navigation', 23, 'Keyboard navigation works', 'MUST', ()),
            ('visible-focus', 23, 'focus states visible', 'MUST', ()),
            ('modal-focus-trap', 23, 'modals trap focus', 'MUST', ('activity.ui_modal',)),
            ('modal-close', 23, 'Esc/close behavior', 'MUST', ('activity.ui_modal',)),
            ('screen-reader-labels', 23, 'screen reader labels', 'MUST', ()),
            ('critical-loading', 24, 'Loading', 'MUST', ('activity.critical_ui_screen',)),
            ('critical-empty', 24, 'Empty', 'MUST', ('activity.critical_ui_screen',)),
            ('critical-error', 24, 'Error', 'MUST', ('activity.critical_ui_screen',)),
            ('critical-permission', 24, 'Permission', 'MUST', ('activity.critical_ui_screen',)),
            ('critical-state-components', 24, 'consistent components', 'MUST', ('activity.critical_ui_screen',)),
            ('ai-loading-thinking', 25, 'distinguish Loading vs Thinking', 'MUST', ('activity.ai_ui_flow',)),
            ('ai-streaming-state', 25, 'Streaming', 'MUST', ('activity.ai_ui_flow',)),
            ('ai-repairing-state', 25, 'Repairing', 'MUST', ('activity.ai_ui_flow',)),
            ('ai-confirmation-state', 25, 'Needs-confirmation', 'MUST', ('activity.ai_ui_flow',)),
            ('ai-cancel-retry', 25, 'provide cancel/retry', 'MUST', ('activity.ai_ui_flow',)),
            ('form-required-markers', 27, 'Required fields are marked', 'SHOULD', ('activity.ui_form',)),
            ('form-inline-errors', 27, 'inline errors near fields', 'SHOULD', ('activity.ui_form',)),
            ('form-clear-copy', 27, 'clear validation copy', 'SHOULD', ('activity.ui_form',)),
            ('destructive-danger-style', 28, 'Danger styling', 'MUST', ('activity.destructive_ui_action',)),
            ('destructive-object-identity', 28, 'confirmation includes object identity', 'MUST', ('activity.destructive_ui_action',)),
            ('destructive-irreversibility', 28, 'irreversibility explained', 'MUST', ('activity.destructive_ui_action',)),
            ('screen-name-content', 29, 'Screen/module naming matches content', 'MUST', ()),
            ('permission-navigation', 29, 'navigation matches user permissions', 'MUST', ()),
            ('list-toolbar', 30, 'Standard list toolbar layout', 'SHOULD', ('activity.ui_list_page',)),
            ('list-pagination', 30, 'pagination consistency', 'SHOULD', ('activity.ui_list_page',)),
            ('icon-discoverability', 32, 'Icon-only controls have tooltips/labels', 'SHOULD', ('activity.ui_icon_control',)),
            ('minimum-click-target', 32, 'click targets meet minimum size', 'SHOULD', ()),
            ('dashboard-units', 33, 'Units', 'MUST', ('activity.ui_dashboard',)),
            ('dashboard-definitions', 33, 'definitions', 'MUST', ('activity.ui_dashboard',)),
            ('dashboard-time-window', 33, 'time window', 'MUST', ('activity.ui_dashboard',)),
            ('dashboard-totals', 33, 'totals are correct and non-misleading', 'MUST', ('activity.ui_dashboard',)),
            ('synthetic-review-data', 34, 'synthetic data', 'SHOULD', ('activity.ui_review_artifacts',)),
            ('review-edge-cases', 34, 'cover edge cases', 'SHOULD', ('activity.ui_review_artifacts',)),
            ('critical-stable-selectors', 35, 'stable `data-testid` selectors', 'MUST', ('activity.critical_ui_interaction',)),
            ('screen-design-frames', 36, 'map to named frames in the design source of truth', 'SHOULD', ()),
            ('critical-visual-baselines', 38, 'Critical screens have baseline screenshots', 'SHOULD', ('activity.critical_ui_screen',)),
            ('critical-visual-drift', 38, 'protected from accidental drift', 'SHOULD', ('activity.critical_ui_screen',)),
            ('citation-linkable-preview', 26, 'linkable/previewable', 'MUST', ('activity.ui_citation_rendering',)),
        )],
        *[(name, '0003', line, phrase, 'SHOULD', ('activity.frontend_repository',) + extra, (42, 53), (42, 'SHOULD')) for name, line, phrase, extra in (
            ('bundle-accessibility', 47, 'Accessibility checks (axe) on critical flows', ()),
            ('bundle-ui-smoke-trace', 48, 'traceable to the UI Spec Appendix', ()),
            ('bundle-critical-visual', 52, 'critical screens or high-trust surfaces', ('ui.critical_or_trust_surface',)),
        )],
    )),
    ('das.architecture-modularity', 'ddd', 'legacy-text-329162a7-', (
        ('playbook-suitability', '0001', 7, 'apply this playbook', 'SHOULD', ('domain.multi_team_surface', 'domain.complex_long_lived_concepts', 'domain.sync_async_mix', 'domain.semantic_drift'), (5, 12), (7, 'SHOULD')),
        ('monolith-context-module', '0002', 29, 'each bounded context', 'SHOULD', ('activity.bounded_context', 'topology.modular_monolith'), (28, 30), (29, 'SHOULD')),
        ('multi-repo-primary-context', '0002', 30, 'one primary bounded context', 'SHOULD', ('topology.multi_repo',), (28, 30), (30, 'SHOULD')),
        ('multiple-context-sdmm', '0002', 30, 'multiple contexts in one repo MUST still be separated by SDMM boundaries', 'MUST', ('activity.multiple_context_repository',), (28, 30), (30, 'MUST')),
        *[(name, '0003', 33, phrase, 'MUST', ('activity.domain_contract',), (32, 34), (33, 'MUST')) for name, phrase in (
            ('language-fields', 'field names'), ('language-enums', 'enums'), ('language-diagnostics', 'diagnostic codes'))],
        ('rename-contract-change', '0003', 34, 'treated as a contract change', 'MUST', ('activity.contract_rename_only',), (32, 34), (34, 'MUST')),
        ('boundary-command-event-hub', '0004', 37, 'live in the contract hub', 'MUST', ('activity.boundary_command_or_domain_event',), (36, 37), (37, 'MUST')),
        ('domain-no-infrastructure', '0005', 66, 'depend on infrastructure (DB/network)', 'MUST', ('activity.domain_layer',), (45, 68), (66, 'MUST NOT')),
        ('cross-context-api-or-contract', '0005', 67, 'through `adapters/` (API) or explicit event/command contracts', 'MUST', ('activity.cross_context_call',), (65, 68), (67, 'MUST')),
        ('shared-code-scoped', '0005', 68, 'carefully scoped', 'MUST', ('activity.shared_context_code',), (65, 68), (68, 'MUST')),
        ('no-shared-domain-logic', '0005', 68, 'Sharing domain logic across contexts', 'SHOULD', ('activity.cross_context_domain_sharing',), (65, 68), (68, 'SHOULD')),
        ('shallow-inheritance', '0006', 74, 'shallow (0–1 levels)', 'SHOULD', ('activity.domain_inheritance',), (70, 87), (74, 'SHOULD')),
        ('no-inheritance-reuse-hack', '0006', 74, 'used as a code reuse hack', 'SHOULD', ('activity.domain_inheritance',), (70, 87), (74, 'SHOULD NOT')),
        ('class-construction-or-transition-validation', '0006', 80, 'validate on construction or on state transitions', 'SHOULD', ('activity.domain_class',), (70, 87), (78, 'SHOULD')),
        ('class-intention-methods', '0006', 81, 'intention-revealing methods', 'SHOULD', ('activity.domain_class',), (70, 87), (78, 'SHOULD')),
        ('aggregate-invariant-tests', '0007', 91, 'invariants', 'MUST', ('activity.domain_aggregate',), (89, 93), (91, 'MUST')),
        ('aggregate-transition-tests', '0007', 91, 'state transitions', 'MUST', ('activity.domain_aggregate',), (89, 93), (91, 'MUST')),
        *[(name, '0007', 92, phrase, 'SHOULD', ('activity.domain_event_emission',), (89, 93), (92, 'SHOULD')) for name, phrase in (
            ('event-fixture-identity', 'what event'), ('event-fixture-time', 'when'), ('event-fixture-payload', 'with which payload'))],
    )),
    ('das.architecture-modularity', 'bdd', 'legacy-text-d2a39e69-', (
        *[(name, '0002', line, phrase, strength, (key,), (44, 53), (46 if strength == 'SHOULD' else 50, strength)) for name, line, phrase, strength, key in (
            ('local-domain-rules', 47, 'domain rules', 'SHOULD', 'activity.repo_local_scenario'),
            ('local-adapter-behavior', 48, 'adapter behavior', 'SHOULD', 'activity.repo_local_scenario'),
            ('local-boundary-validation', 49, 'boundary validations', 'SHOULD', 'activity.repo_local_scenario'),
            ('harness-compatibility', 52, 'compatibility windows', 'MUST', 'activity.integration_harness'),
            ('harness-critical-smoke', 53, 'critical production smoke flows', 'MUST', 'activity.integration_harness'))],
        ('ai-determinism-declaration', '0003', 57, 'declare their determinism expectations', 'MUST', ('activity.bdd_scenario', 'scenario.ai_pipeline'), (55, 63), (57, 'MUST')),
        *[(name, '0004', line, phrase, 'MUST', ('activity.tier_0_or_1_bdd_scenario',), (55, 63), (59, 'MUST')) for name, line, phrase in (
            ('offline-replay-fixtures', 60, 'cassettes, snapshots, or pinned fixtures'),
            ('untrusted-model-input', 61, 'model outputs as untrusted input'),
            ('model-schema-validation', 61, 'validate against schemas'),
            ('scenario-budget-enforcement', 62, 'enforce budgets'),
            ('scenario-budget-termination', 62, 'explicit termination codes'))],
        ('tier2-isolated', '0004', 63, 'isolated from the default `verify` gate', 'MUST', ('activity.bdd_scenario', 'scenario.tier_2'), (55, 63), (63, 'MUST')),
        ('tier2-cost-controls', '0004', 63, 'explicit cost controls', 'MUST', ('activity.bdd_scenario', 'scenario.tier_2'), (55, 63), (63, 'MUST')),
        *[(name, '0006', 77, phrase, 'MUST', ('activity.critical_workflow', 'scenario.automation_short_term_infeasible'), (75, 77), (77, 'MUST')) for name, phrase in (
            ('short-term-gap-documented', 'document the gap'), ('short-term-gap-owner', 'the owner'), ('short-term-gap-milestone', 'milestone date'))],
        *[(name, '0007', line, phrase, 'SHOULD', ('activity.bdd_step_definition',), (99, 108), (101, 'SHOULD')) for name, line, phrase in (
            ('observable-payload', 102, 'contract payload validation'), ('observable-diagnostics', 103, 'stable diagnostic codes'),
            ('observable-transitions', 104, 'state machine transitions'), ('observable-idempotency', 105, 'idempotency keys'),
            ('observable-budgets', 106, 'budget enforcement'))],
        ('reuse-contract-fixtures', '0007', 107, 'contract hub fixtures (or repo-local fixtures that are derived from them)', 'SHOULD', ('activity.bdd_scenario',), (99, 108), (107, 'SHOULD')),
        ('ui-stable-selectors', '0007', 108, 'stable selectors defined in the UI Spec Appendix', 'SHOULD', ('activity.ui_e2e_scenario',), (99, 108), (108, 'SHOULD')),
    )),
)
# Deployment retains its actual adoption/profile conditions. Library/research
# subset choices remain in every leaf context; MAY alternatives are not gates.
PLAYBOOKS += (
    ('das.governance.verification-release', 'deployment', 'legacy-text-16280e97-', (
        ('baseline-environments', '0002', 55, 'standardize at least', 'SHOULD', ('activity.deployment_governance',), (53, 68), (55, 'SHOULD')),
        ('environment-matrix-environment', '0003', 74, 'Environment', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-purpose', '0003', 74, 'Purpose', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-data-class', '0003', 74, 'Data class allowed', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-secrets', '0003', 74, 'Secrets strategy', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-dependencies', '0003', 74, 'External deps mode', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-deploy-method', '0003', 74, 'Deploy method', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-rollback', '0003', 74, 'Rollback', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-matrix-owner', '0003', 74, 'Owner', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (70, 82), (72, 'MUST')),
        ('environment-data-class', '0004', 79, 'data classification', 'MUST', ('activity.deployment_governance', 'activity.deployed_environment'), (70, 82), (79, 'MUST')),
        ('nonprod-production-data-default-denied', '0004', 80, 'Production data MUST NOT be used in non-prod environments by default', 'MUST', ('activity.deployment_governance', 'activity.nonprod_environment'), (70, 82), (80, 'MUST NOT')),
        ('nonprod-required-prodlike-mask-and-approval', '0004', 81, 'masking/anonymization and approval controls', 'MUST', ('activity.deployment_governance', 'activity.nonprod_production_like_data'), (70, 82), (81, 'MUST')),
        ('environment-endpoints-credentials-secrets-config', '0004', 82, 'endpoints and credentials MUST be treated as secrets/config', 'MUST', ('activity.deployment_governance', 'activity.deployed_environment'), (70, 82), (82, 'MUST')),
        ('staging-production-topology-parity', '0005', 86, 'production-like in topology and dependencies, except for data', 'SHOULD', ('activity.deployment_governance', 'environment.staging'), (84, 88), (86, 'SHOULD')),
        ('l2-staging-allowed-differences-rationale', '0005', 87, 'which differences between `staging` and `prod` are allowed, and why', 'MUST', ('activity.deployment_governance', 'profile.l2', 'environment.staging'), (84, 88), (87, 'MUST')),
        ('scheduled-iac-drift', '0005', 88, 'drift checks', 'SHOULD', ('activity.deployment_governance', 'activity.iac'), (84, 88), (88, 'SHOULD')),
        ('immutable-addressable-release-artifacts', '0006', 96, 'immutable and uniquely addressable', 'MUST', ('activity.deployment_governance', 'activity.release_artifact'), (94, 99), (96, 'MUST')),
        ('container-digest-pin', '0006', 97, 'pinned by **digest**', 'SHOULD', ('activity.deployment_governance', 'artifact.container'), (94, 99), (97, 'SHOULD')),
        ('package-version', '0006', 98, 'Packages MUST have a version', 'MUST', ('activity.deployment_governance', 'artifact.package'), (94, 99), (98, 'MUST')),
        ('deployment-exact-artifact-config-identities', '0006', 99, 'exact artifact identity (digest/version) and config identity', 'MUST', ('activity.deployment_governance', 'activity.deployment'), (94, 99), (99, 'MUST')),
        ('same-artifact-promotion', '0007', 103, 'promote-the-same-artifact', 'SHOULD', ('activity.deployment_governance', 'activity.environment_promotion'), (101, 107), (103, 'SHOULD')),
        ('chosen-per-env-rebuild-reproducible', '0007', 105, 'builds MUST be reproducible', 'MUST', ('activity.deployment_governance', 'build.rebuild_per_environment'), (101, 107), (105, 'MUST')),
        ('chosen-per-env-rebuild-inputs-pinned', '0007', 106, 'build inputs MUST be pinned', 'MUST', ('activity.deployment_governance', 'build.rebuild_per_environment'), (101, 107), (106, 'MUST')),
        ('chosen-per-env-rebuild-provenance', '0007', 107, 'pipeline MUST provide provenance', 'MUST', ('activity.deployment_governance', 'build.rebuild_per_environment'), (101, 107), (107, 'MUST')),
        ('release-notes-contracts-migrations-rollback', '0008', 111, 'schema/contract changes, migrations, and rollback constraints', 'MUST', ('activity.deployment_governance', 'activity.governed_release'), (109, 112), (111, 'MUST')),
        ('unsafe-rollback-alternative', '0008', 112, 'rollback alternative', 'MUST', ('activity.deployment_governance', 'release.rollback_unsafe'), (109, 112), (112, 'MUST')),
        ('versioned-config-identity', '0009', 120, 'versioned and referenced by an identifier', 'MUST', ('activity.deployment_governance', 'activity.runtime_config'), (118, 122), (120, 'MUST')),
        ('config-code-review-approval', '0009', 121, 'reviewed like code (PR + approvals)', 'MUST', ('activity.deployment_governance', 'activity.runtime_config_change'), (118, 122), (121, 'MUST')),
        ('config-schema-validation', '0009', 122, 'schema-validated', 'SHOULD', ('activity.deployment_governance', 'activity.runtime_config'), (118, 122), (122, 'SHOULD')),
        ('approved-secret-manager', '0010', 127, 'approved secret manager', 'MUST', ('activity.deployment_governance', 'activity.secret_handling'), (124, 129), (127, 'MUST')),
        ('secret-rotation-runbook', '0010', 128, 'Secret rotation procedures MUST exist', 'MUST', ('activity.deployment_governance', 'activity.secret_handling'), (124, 129), (128, 'MUST')),
        ('separate-environment-credentials', '0010', 129, 'separate credentials per environment', 'SHOULD', ('activity.deployment_governance', 'activity.secret_handling'), (124, 129), (129, 'SHOULD')),
        ('risky-behavior-feature-flags', '0011', 133, 'Behavioral changes SHOULD be guarded by feature flags', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.high_risk'}, {'op': 'fact', 'key': 'change.rollback_hard'}, {'op': 'fact', 'key': 'change.partial_rollout_desired'}]}]}, (131, 137), (133, 'SHOULD')),
        ('l2-feature-flag-lifecycle', '0011', 137, 'feature-flag lifecycle', 'MUST', ('activity.deployment_governance', 'profile.l2'), (131, 137), (137, 'MUST')),
        ('l1-l2-production-cloud-iac', '0012', 145, 'Cloud resources used by production systems MUST be defined in IaC', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}, {'op': 'fact', 'key': 'activity.production_cloud_resources'}]}, (143, 147), (145, 'MUST')),
        ('iac-versioned-and-pr-reviewed', '0012', 146, 'version-controlled and reviewed via PRs', 'MUST', ('activity.deployment_governance', 'activity.iac'), (143, 147), (146, 'MUST')),
        ('least-privilege-cloud-iam', '0012', 147, 'least privilege for cloud IAM', 'SHOULD', ('activity.deployment_governance', 'activity.cloud_iam'), (143, 147), (147, 'SHOULD')),
        ('resource-inventory-compute', '0013', 153, 'compute', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('resource-inventory-data-stores', '0013', 154, 'data stores', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('resource-inventory-messages-streams', '0013', 155, 'message/stream systems', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('resource-inventory-observability', '0013', 156, 'observability stack', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('resource-inventory-secrets', '0013', 157, 'secrets manager', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('resource-inventory-network', '0013', 158, 'network controls', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (149, 158), (151, 'MUST')),
        ('frozen-lock-ci-build', '0014', 166, 'CI MUST build in “frozen lockfile” mode', 'MUST', ('activity.deployment_governance', 'activity.ci_build'), (164, 168), (166, 'MUST')),
        ('resolution-changes-lock-fails', '0014', 168, 'fail if dependency resolution would change the lock state', 'MUST', ('activity.deployment_governance', 'activity.repository_build'), (164, 168), (168, 'MUST')),
        ('l2-production-sbom', '0015', 172, 'Every production artifact MUST produce an SBOM', 'MUST', ('activity.deployment_governance', 'profile.l2', 'artifact.production'), (170, 173), (172, 'MUST')),
        ('sbom-asset-notes-reference', '0015', 173, 'stored alongside build artifacts and referenced', 'SHOULD', ('activity.deployment_governance', 'artifact.sbom'), (170, 173), (173, 'SHOULD')),
        ('l2-ci-direct-transitive-sca', '0016', 177, 'direct and transitive dependencies', 'MUST', ('activity.deployment_governance', 'profile.l2', 'activity.ci_verification'), (175, 181), (177, 'MUST')),
        ('vulnerability-policy-time-to-fix-gating', '0016', 178, 'time-to-fix and gating thresholds', 'MUST', ('activity.deployment_governance',), (175, 181), (178, 'MUST')),
        ('vulnerability-policy-severity', '0016', 179, 'how severity is determined', 'MUST', ('activity.deployment_governance',), (175, 181), (178, 'MUST')),
        ('vulnerability-policy-blocking-severities', '0016', 180, 'which severities block releases', 'MUST', ('activity.deployment_governance',), (175, 181), (178, 'MUST')),
        ('vulnerability-policy-waiver-expiry', '0016', 181, 'waiver / exception process (with expiry)', 'MUST', ('activity.deployment_governance',), (175, 181), (178, 'MUST')),
        ('release-artifact-signing', '0017', 185, 'Sign release artifacts', 'SHOULD', ('activity.deployment_governance', 'activity.release_artifact'), (183, 186), (185, 'SHOULD')),
        ('deployment-signature-check', '0017', 185, 'verify signatures during deployment', 'SHOULD', ('activity.deployment_governance', 'activity.deployment'), (183, 186), (185, 'SHOULD')),
        ('l2-deployment-signature-check', '0017', 186, 'deployment system MUST verify signatures', 'MUST', ('activity.deployment_governance', 'profile.l2', 'activity.deployment'), (183, 186), (186, 'MUST')),
        ('deployment-provenance-metadata', '0017', 186, 'SHOULD capture provenance metadata', 'SHOULD', ('activity.deployment_governance', 'profile.l2', 'activity.deployment'), (183, 186), (186, 'SHOULD')),
        ('base-build-environment-pins', '0018', 190, 'Base images and build environments MUST be pinned', 'MUST', ('activity.deployment_governance', 'activity.repository_build'), (188, 191), (190, 'MUST')),
        ('production-no-floating-image', '0018', 191, 'Use floating tags', 'MUST', ('activity.deployment_governance', 'activity.production_build_or_deploy'), (188, 191), (191, 'MUST NOT')),
        ('secret-history-scanning', '0019', 195, 'pre-commit and CI', 'SHOULD', ('activity.deployment_governance', 'activity.repository_verification'), (193, 196), (195, 'SHOULD')),
        ('secret-leak-incident-rotation-remediation', '0019', 196, 'rotation MUST be treated as an incident with documented remediation', 'MUST', ('activity.deployment_governance', 'incident.secret_leak'), (193, 196), (196, 'MUST')),
        ('mixed-version-schema-expand-contract', '0020', 207, 'expand/contract patterns', 'MUST', ('activity.deployment_governance', 'activity.database_migration', 'migration.mixed_versions'), (201, 209), (207, 'MUST')),
        ('mixed-version-backward-forward-window', '0020', 208, 'Backward- and forward-compatible windows MUST be documented', 'MUST', ('activity.deployment_governance', 'activity.database_migration', 'migration.mixed_versions'), (201, 209), (208, 'MUST')),
        ('additive-before-switch-before-remove', '0020', 209, 'additive columns/tables first', 'SHOULD', ('activity.deployment_governance', 'activity.database_migration', 'migration.mixed_versions'), (201, 209), (209, 'SHOULD')),
        ('changed-cache-format-versioned-key', '0021', 213, 'Cache keys MUST be versioned', 'MUST', ('activity.deployment_governance', 'activity.cache_payload_migration'), (201, 219), (213, 'MUST')),
        ('dual-cache-key-window', '0021', 214, 'new keys alongside old keys', 'SHOULD', ('activity.deployment_governance', 'activity.cache_migration_window'), (201, 219), (214, 'SHOULD')),
        ('message-schema-contract-fixtures', '0022', 218, 'fixture-backed', 'MUST', ('activity.deployment_governance', 'activity.message_contract'), (201, 219), (218, 'MUST')),
        ('message-consumer-unknown-fields', '0022', 219, 'Consumers MUST tolerate unknown fields', 'MUST', ('activity.deployment_governance', 'activity.message_contract_consumer'), (201, 219), (219, 'MUST')),
        ('dependency-registry-dependency', '0023', 229, 'Dependency', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 236), (227, 'MUST')),
        ('dependency-registry-type', '0023', 229, 'Type', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-purpose', '0023', 229, 'Purpose', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-contract', '0023', 229, 'Contract surface', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-auth', '0023', 229, 'Auth', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-rate-limits', '0023', 229, 'Rate limits', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-cost', '0023', 229, 'Cost model', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-data', '0023', 229, 'Data policy', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-service-level', '0023', 229, 'SLA/SLO', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-fallback', '0023', 229, 'Fallback', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-registry-owner', '0023', 229, 'Owner', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (225, 241), (227, 'MUST')),
        ('dependency-owner-and-escalation', '0024', 234, 'owner and an escalation path', 'MUST', ('activity.deployment_governance', 'activity.external_dependency'), (225, 241), (234, 'MUST')),
        ('vendor-failure-modes', '0024', 235, 'timeouts, throttling, partial outages', 'MUST', ('activity.deployment_governance', 'activity.external_dependency'), (225, 241), (235, 'MUST')),
        ('ci-dependency-stubs-snapshots', '0024', 236, 'avoid live dependency calls', 'SHOULD', ('activity.deployment_governance', 'activity.ci_external_dependency'), (225, 241), (236, 'SHOULD')),
        ('l2-vendor-change-notification-review', '0025', 240, 'vendor-change notifications and a review process', 'SHOULD', ('activity.deployment_governance', 'profile.l2', 'activity.external_dependency'), (238, 241), (240, 'SHOULD')),
        ('single-vendor-failure-degraded-mode', '0025', 241, 'defined degraded mode', 'MUST', ('activity.deployment_governance', 'vendor.single_point_of_failure'), (238, 241), (241, 'MUST')),
        ('model-provider-interface', '0026', 249, 'wrapped behind explicit interfaces', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (249, 'MUST')),
        ('model-provider-logging', '0026', 250, 'request/response logging policy', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (249, 'MUST')),
        ('model-provider-redaction', '0026', 251, 'redaction rules', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (249, 'MUST')),
        ('model-provider-timeout-retry', '0026', 252, 'timeout and retry rules', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (249, 'MUST')),
        ('model-provider-rate-limits', '0026', 253, 'rate-limit handling', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (249, 'MUST')),
        ('provider-versioned-traceable-prompt', '0026', 254, 'Prompt identifiers', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (254, 'MUST')),
        ('provider-versioned-traceable-model', '0026', 254, 'model identifiers', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (254, 'MUST')),
        ('provider-versioned-traceable-tool', '0026', 254, 'tool schemas', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (247, 254), (254, 'MUST')),
        ('provider-one-lawful-fallback', '0027', 258, 'at least one fallback strategy', 'SHOULD', ('activity.deployment_governance', 'activity.ai_provider_calls'), (256, 261), (258, 'SHOULD')),
        ('provider-user-data-transmission-retention-training', '0028', 265, 'whether user data is sent to providers, retained, or used for training', 'MUST', ('activity.deployment_governance', 'activity.ai_provider_calls'), (263, 265), (265, 'MUST')),
        ('production-logs-metrics-traces', '0029', 273, 'logs, metrics, and traces', 'MUST', ('activity.deployment_governance', 'component.production_system'), (271, 274), (273, 'MUST')),
        ('boundary-correlation-ids', '0029', 274, 'propagated across boundaries', 'MUST', ('activity.deployment_governance', 'component.production_system'), (271, 274), (274, 'MUST')),
        ('runbook-deploy', '0030', 278, 'deploy', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (276, 279), (278, 'MUST')),
        ('runbook-rollback', '0030', 278, 'rollback', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (276, 279), (278, 'MUST')),
        ('runbook-incidents', '0030', 278, 'key incident classes', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.deployment_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, (276, 279), (278, 'MUST')),
        ('l2-oncall-incident-process', '0030', 279, 'on-call and incident response process documented', 'MUST', ('activity.deployment_governance', 'profile.l2'), (276, 279), (279, 'MUST')),
        ('significant-incident-owned-postmortem', '0031', 283, 'postmortem with tracked remediation items', 'SHOULD', ('activity.deployment_governance', 'incident.significant'), (281, 283), (283, 'SHOULD')),
        ('chosen-release-strategy-compatible-documented', '0032', 293, 'documented and consistent with compatibility-mode requirements', 'MUST', ('activity.deployment_governance', 'activity.deployment'), (287, 295), (293, 'MUST')),
        ('explicit-rollback-constraints', '0032', 294, 'Rollback constraints MUST be explicit', 'MUST', ('activity.deployment_governance', 'activity.deployment'), (287, 295), (294, 'MUST')),
        ('risky-rollout-canary-flags', '0032', 295, 'canary + feature flags', 'SHOULD', ('activity.deployment_governance', 'activity.deployment', 'change.high_risk'), (287, 295), (295, 'SHOULD')),
        ('l2-large-program-service-catalog', '0033', 305, 'Service catalog + ownership', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-api-governance', '0033', 306, 'API governance', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-identity', '0033', 307, 'Identity and access', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-audit', '0033', 308, 'Audit logging', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-change-management', '0033', 309, 'Change management', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-data', '0033', 310, 'Data governance', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('l2-large-program-vendor', '0033', 311, 'Vendor management', 'MUST', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (303, 'MUST')),
        ('large-program-disaster-recovery', '0034', 315, 'multi-region strategy and disaster recovery', 'SHOULD', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (313, 'SHOULD')),
        ('large-program-central-observability', '0034', 316, 'central observability standards', 'SHOULD', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (313, 'SHOULD')),
        ('large-program-golden-paths', '0034', 317, 'shared platform libraries and golden paths', 'SHOULD', ('activity.deployment_governance', 'profile.l2', 'component.large_program'), (299, 317), (313, 'SHOULD')),
        ('artifact-checklist-environment-matrix', '0035', 325, 'Environment Matrix', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-pipeline', '0035', 326, 'Deployment Pipeline description', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-dependency-registry', '0035', 327, 'Dependency Registry', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-secrets-runbooks', '0035', 328, 'Secrets + rotation runbooks', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-migration', '0035', 329, 'Migration strategy notes', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-observability', '0035', 330, 'Observability and SLOs', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-checklist-rollback', '0035', 331, 'Rollback plan', 'SHOULD', ('activity.deployment_governance',), (321, 333), (323, 'SHOULD')),
        ('artifact-versioned', '0036', 333, 'versioned', 'MUST', ('activity.deployment_governance', 'activity.deployment_governed_artifact'), (321, 333), (333, 'MUST')),
        ('artifact-reviewed-with-code', '0036', 333, 'reviewed with code', 'MUST', ('activity.deployment_governance', 'activity.deployment_governed_artifact'), (321, 333), (333, 'MUST')),
    )),
)

# Governance preserves actual multi-party co-authorship and emergency controls.
# Recommended RFCs/approval matrices/edit leases are not blanket prerequisites.
PLAYBOOKS += (
    ('das.governance.verification-release', 'collaboration', 'legacy-text-1be6a1ed-', (
        ('single-versioned-intent', '0002', 43, 'single, version-controlled source of truth', 'MUST', ('activity.multiparty_document_governance',), (40, 55), (43, 'MUST')),
        ('early-mechanical-drift-checks', '0005', 52, 'mechanical checks (links, IDs, schema inventories)', 'SHOULD', ('activity.multiparty_document_governance',), (40, 55), (52, 'SHOULD')),
        ('declared-role-decision-owner', '0006', 66, 'Decision Owner', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc'), (59, 74), (63, 'MUST')),
        ('declared-role-reviewers', '0006', 67, 'Reviewers', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc'), (59, 74), (63, 'MUST')),
        ('declared-role-contributors', '0006', 68, 'Contributors', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc'), (59, 74), (63, 'MUST')),
        ('decision-domains-architecture', '0008', 80, 'Architecture/topology', 'SHOULD', ('activity.multiparty_document_governance',), (76, 86), (78, 'SHOULD')),
        ('decision-domains-contracts', '0008', 81, 'Contracts + identifiers', 'SHOULD', ('activity.multiparty_document_governance',), (76, 86), (78, 'SHOULD')),
        ('decision-domains-security', '0008', 82, 'Security/compliance', 'SHOULD', ('activity.multiparty_document_governance',), (76, 86), (78, 'SHOULD')),
        ('decision-domains-operations', '0008', 83, 'Operations/deployment', 'SHOULD', ('activity.multiparty_document_governance',), (76, 86), (78, 'SHOULD')),
        ('decision-domains-ux', '0008', 84, 'UX/system design', 'SHOULD', ('activity.multiparty_document_governance',), (76, 86), (78, 'SHOULD')),
        ('decision-domain-named-owner', '0009', 86, 'named owner group', 'SHOULD', ('activity.multiparty_document_governance', 'activity.decision_domain'), (76, 86), (86, 'SHOULD')),
        ('master-doc-set-header-title', '0011', 98, 'Doc Title', 'MUST', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (92, 112), (96, 'MUST')),
        ('master-doc-set-header-stable-id', '0011', 99, 'Doc ID (stable)', 'MUST', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (92, 112), (96, 'MUST')),
        ('master-doc-set-header-updated', '0011', 102, 'Last updated (YYYY-MM-DD)', 'MUST', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (92, 112), (96, 'MUST')),
        ('master-doc-set-header-scope', '0011', 103, 'Scope (what this doc covers / does not cover)', 'MUST', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (92, 112), (96, 'MUST')),
        ('canonical-doc-set-stable-links', '0012', 122, 'All links in the canonical doc set MUST be stable', 'MUST', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (114, 123), (122, 'MUST')),
        ('avoid-duplicating-truth', '0012', 123, 'Avoid duplicating the same truth in multiple places', 'SHOULD', ('activity.multiparty_document_governance', 'activity.master_doc_set_doc'), (114, 123), (123, 'SHOULD')),
        ('unavoidable-duplicate-explicit-ssot', '0012', 123, 'you MUST declare which one is SSOT', 'MUST', ('activity.multiparty_document_governance', 'activity.unavoidable_governed_truth_duplication'), (114, 123), (123, 'MUST')),
        ('applicable-confidentiality-classification', '0013', 131, 'declare its confidentiality classification', 'SHOULD', ('activity.multiparty_document_governance', 'activity.governed_doc', 'document.confidentiality_applicable'), (125, 133), (131, 'SHOULD')),
        ('restricted-material-no-unauthorized-copy', '0013', 132, 'Restricted material MUST NOT be copied', 'MUST', ('activity.multiparty_document_governance', 'activity.restricted_material_transfer'), (125, 133), (132, 'MUST NOT')),
        ('external-master-doc-redacted-partner-pack', '0013', 133, 'redacted “Partner Pack”', 'SHOULD', ('activity.multiparty_document_governance', 'activity.external_master_doc_sharing'), (125, 133), (133, 'SHOULD')),
        ('partner-pack-retains-ids-removes-sensitive-details', '0013', 133, 'same IDs but with sensitive details removed', 'SHOULD', ('activity.multiparty_document_governance', 'activity.external_master_doc_sharing'), (125, 133), (133, 'SHOULD')),
        ('pr-task-or-issue', '0014', 142, 'reference an issue/task', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_pr'), (137, 146), (142, 'MUST')),
        ('pr-declares-scope', '0014', 143, 'scope (docs/sections touched)', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_pr'), (137, 146), (142, 'MUST')),
        ('pr-declares-contracts-ids', '0014', 144, 'impacted contracts/IDs', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_pr'), (137, 146), (142, 'MUST')),
        ('pr-declares-verification-gates', '0014', 145, 'expected verification gates', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_pr'), (137, 146), (142, 'MUST')),
        ('pr-contract-deploy-compatibility-rollout', '0014', 146, 'explicit compatibility/rollout note', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'activity.governed_doc_pr'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.deployment_rule'}]}]}, (137, 146), (146, 'MUST')),
        ('high-impact-or-contentious-rfc', '0015', 150, 'teams SHOULD use an RFC process', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.high_impact'}, {'op': 'fact', 'key': 'change.contentious'}]}]}, (148, 166), (150, 'SHOULD')),
        ('actual-rfc-pr-merge', '0016', 163, 'merged as PRs', 'SHOULD', ('activity.multiparty_document_governance', 'activity.governed_rfc'), (148, 166), (163, 'SHOULD')),
        ('actual-rfc-explicit-outcome', '0016', 164, 'explicit outcome: Accepted / Rejected / Superseded', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_rfc'), (148, 166), (164, 'MUST')),
        ('deprecation-explicit', '0017', 170, 'Deprecations MUST be explicit', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_deprecation'), (168, 172), (170, 'MUST')),
        ('deprecation-time-bounded', '0017', 170, 'time-bounded', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_deprecation'), (168, 172), (170, 'MUST')),
        ('deprecated-doc-replacement-link', '0017', 171, 'link to its replacement', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_deprecation'), (168, 172), (171, 'MUST')),
        ('deprecated-doc-consistent-marker', '0017', 172, 'consistent front-matter marker', 'SHOULD', ('activity.multiparty_document_governance', 'activity.governed_doc_deprecation'), (168, 172), (172, 'SHOULD')),
        ('critical-doc-path-required-review-enforced', '0018', 183, 'Branch protection MUST enforce required reviews', 'MUST', ('activity.multiparty_document_governance', 'activity.governed_doc_review_policy'), (176, 184), (183, 'MUST')),
        ('program-approval-matrix', '0019', 188, 'simple approval matrix', 'SHOULD', ('activity.multiparty_document_governance',), (186, 198), (188, 'SHOULD')),
        ('break-glass-limited-to-sev1-sev2', '0020', 210, 'limited to **Sev1/Sev2 incidents**', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (210, 'MUST')),
        ('break-glass-ic', '0020', 211, 'incident commander (IC) MUST be named', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (211, 'MUST')),
        ('break-glass-incident-id', '0020', 211, 'incident ID', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (211, 'MUST')),
        ('break-glass-start-time', '0020', 211, 'start time', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (211, 'MUST')),
        ('break-glass-systems', '0020', 211, 'impacted systems', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (211, 'MUST')),
        ('break-glass-rationale', '0020', 211, 'rationale for override', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (202, 211), (211, 'MUST')),
        ('regulated-break-glass-required-compliance-no-bypass', '0021', 217, 'MUST NOT bypass required compliance gates', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change', 'profile.regulated_or_safety'), (213, 217), (217, 'MUST NOT')),
        ('regulated-break-glass-tailoring-declared', '0021', 217, 'Tailoring MUST be defined in the profile/master doc', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change', 'profile.regulated_or_safety'), (213, 217), (217, 'Tailoring MUST')),
        ('break-glass-incident-link', '0022', 223, 'linked to the incident ID', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (219, 225), (221, 'MUST')),
        ('break-glass-independent-senior-review', '0022', 224, 'reviewed by at least one senior engineer not authoring the change (two-person rule)', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (219, 225), (221, 'MUST')),
        ('break-glass-deferred-gates-explicit-list', '0022', 225, 'explicitly list which gates were deferred', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_change'), (219, 225), (225, 'MUST')),
        ('deferred-gates-payback-ticket', '0023', 229, '“debt payback” ticket (or equivalent) for each deferred gate set', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_deferred_gate_set'), (227, 231), (229, 'MUST')),
        ('deferred-gates-24h-or-next-business-day', '0023', 230, 'within **24 hours** (or the next business day)', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_deferred_gate_set'), (227, 231), (230, 'MUST')),
        ('deferred-gates-results-attached', '0023', 230, 'results attached to the ticket', 'MUST', ('activity.multiparty_document_governance', 'activity.break_glass_deferred_gate_set'), (227, 231), (230, 'MUST')),
        ('overdue-payback-merge-or-release-tightening', '0023', 231, 'automated enforcement rule', 'SHOULD', ('activity.multiparty_document_governance', 'activity.break_glass_payback_enforcement'), (227, 231), (231, 'SHOULD')),
        ('multi-company-contribution-licensing-attribution', '0024', 241, 'licensed/attributed for project repos', 'MUST', ('activity.multiparty_document_governance', 'component.multi_company_program'), (233, 243), (241, 'MUST')),
        ('chosen-contributor-agreement-documented', '0024', 242, 'it MUST be documented', 'MUST', ('activity.multiparty_document_governance', 'component.multi_company_program', 'activity.contributor_agreement'), (233, 243), (242, 'MUST')),
        ('chosen-contributor-agreement-enforced', '0024', 242, 'enforced', 'MUST', ('activity.multiparty_document_governance', 'component.multi_company_program', 'activity.contributor_agreement'), (233, 243), (242, 'MUST')),
        ('cross-org-proprietary-copy-agreement', '0024', 243, 'without an explicit agreement', 'SHOULD', ('activity.multiparty_document_governance', 'activity.cross_org_content_transfer'), (233, 243), (243, 'SHOULD')),
        ('l2-boundary-rule-trace-issue-rfc-adr', '0025', 252, 'an issue/RFC/ADR', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'profile.l2'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.deployment_rule'}, {'op': 'fact', 'key': 'change.security_posture'}]}]}, (245, 254), (251, 'MUST')),
        ('l2-boundary-rule-trace-pr-approvals', '0025', 253, 'PR approvals', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'profile.l2'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.deployment_rule'}, {'op': 'fact', 'key': 'change.security_posture'}]}]}, (245, 254), (251, 'MUST')),
        ('l2-boundary-rule-trace-release-milestone', '0025', 254, 'a release milestone', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'profile.l2'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.deployment_rule'}, {'op': 'fact', 'key': 'change.security_posture'}]}]}, (245, 254), (251, 'MUST')),
        ('parallel-doc-modularization', '0026', 262, 'doc modularization to reduce merge conflicts', 'SHOULD', ('activity.multiparty_document_governance', 'activity.parallel_doc_edit'), (258, 264), (262, 'SHOULD')),
        ('parallel-doc-stable-ids-no-casual-renames', '0026', 263, 'stable IDs and avoid renaming sections casually', 'SHOULD', ('activity.multiparty_document_governance', 'activity.parallel_doc_edit'), (258, 264), (263, 'SHOULD')),
        ('dispute-decision-owner-final-call', '0027', 270, 'Decision Owner makes the final call', 'MUST', ('activity.multiparty_document_governance', 'activity.doc_dispute'), (266, 276), (270, 'MUST')),
        ('dispute-record-change', '0027', 272, 'what changed', 'MUST', ('activity.multiparty_document_governance', 'activity.doc_dispute'), (266, 276), (271, 'MUST')),
        ('dispute-record-rationale', '0027', 273, 'why', 'MUST', ('activity.multiparty_document_governance', 'activity.doc_dispute'), (266, 276), (271, 'MUST')),
        ('dispute-record-compatibility-migration', '0027', 274, 'compatibility/migration implications', 'MUST', ('activity.multiparty_document_governance', 'activity.doc_dispute'), (266, 276), (271, 'MUST')),
        ('dispute-record-approver', '0027', 275, 'who approved', 'MUST', ('activity.multiparty_document_governance', 'activity.doc_dispute'), (266, 276), (271, 'MUST')),
        ('disputed-decision-owner-escalation', '0027', 276, 'escalate to the program’s architecture/security steering group', 'SHOULD', ('activity.multiparty_document_governance', 'activity.doc_dispute', 'dispute.decision_owner_is_party'), (266, 276), (276, 'SHOULD')),
        ('ai-doc-human-owner-review', '0028', 286, 'reviewed by a human owner', 'MUST', ('activity.multiparty_document_governance', 'activity.ai_generated_governed_doc'), (280, 289), (286, 'MUST')),
        ('ai-doc-output-nonauthoritative', '0028', 286, 'LLM output is non-authoritative', 'MUST', ('activity.multiparty_document_governance', 'activity.ai_generated_governed_doc'), (280, 289), (286, 'MUST')),
        ('material-ai-doc-native-verify', '0028', 287, 'validated by `verify`', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'activity.ai_generated_governed_doc'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.security_posture'}, {'op': 'fact', 'key': 'change.deployment_rule'}]}]}, (280, 289), (287, 'MUST')),
        ('material-ai-doc-domain-owner', '0028', 287, 'a domain owner', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.multiparty_document_governance'}, {'op': 'fact', 'key': 'activity.ai_generated_governed_doc'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'change.contract_surface'}, {'op': 'fact', 'key': 'change.security_posture'}, {'op': 'fact', 'key': 'change.deployment_rule'}]}]}, (280, 289), (287, 'MUST')),
        ('ai-doc-bounded-context-unless-deeper-required', '0028', 288, 'unless deeper docs are explicitly required', 'SHOULD', ('activity.multiparty_document_governance', 'activity.ai_generated_governed_doc'), (280, 289), (288, 'SHOULD')),
        ('ai-doc-pr-ready-diffs', '0028', 289, 'PR-ready diffs', 'SHOULD', ('activity.multiparty_document_governance', 'activity.ai_generated_governed_doc'), (280, 289), (289, 'SHOULD')),
    )),
)

# Visual companions retain surface/event conditions; normal headless projects
# have no UI obligations. Repeated main-body duties below keep their IDs.
# Title-case Must in illustrative state cells is not promoted to BCP 14 MUST.
PLAYBOOKS += (
    ('das.interaction.standard-ui', 'ui', 'legacy-text-8d48152b-', (
        ('spec-telemetry-contracts', '0001', 49, 'Telemetry event names and properties SHOULD be treated as contracts', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_telemetry'}]}, (41, 49), (49, 'SHOULD')),
        ('ambiguous-behavior-prototype-link', '0002', 55, 'Link the interactive prototype', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'ui.behavior_ambiguous_in_words'}]}, (51, 67), (55, 'MUST')),
        ('ambiguous-behavior-enough-exported-images', '0002', 55, 'embed enough exported images to disambiguate behavior', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'ui.behavior_ambiguous_in_words'}]}, (51, 67), (55, 'MUST')),
        ('embedded-annotated-key-state-pngs', '0002', 56, 'annotated PNGs', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_spec_embedded_visual'}]}, (51, 67), (56, 'SHOULD')),
        ('embedded-visual-scrubbed-or-synthetic', '0002', 58, 'scrubbed / synthetic data', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_spec_embedded_visual'}]}, (51, 67), (58, 'MUST')),
        ('embedded-visual-caption', '0002', 60, 'caption describing the intended behavior in words', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_spec_embedded_visual'}]}, (51, 67), (59, 'MUST')),
        ('embedded-visual-owner-date', '0002', 61, 'owner + last-updated date', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_spec_embedded_visual'}]}, (51, 67), (59, 'MUST')),
        ('embedded-visual-requirement-trace', '0002', 62, 'what decision/requirement it supports', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_spec_embedded_visual'}]}, (51, 67), (59, 'MUST')),
        ('workflow-screen-map', '0003', 72, 'at least one Screen ID', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_workflow'}]}, (69, 73), (71, 'MUST')),
        ('boundary-workflow-contract-map', '0003', 73, 'at least one Contract ID', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_workflow'}, {'op': 'fact', 'key': 'workflow.crosses_boundary'}]}, (69, 73), (71, 'MUST')),
        ('screen-named-design-frame', '0004', 84, 'correspond to a named Frame in the design source of truth', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}]}, (77, 86), (84, 'MUST')),
        ('failed-ui-test-capture-screenshots', '0006', 226, 'screenshot(s)', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_test_failure'}]}, (217, 229), (225, 'SHOULD')),
        ('failed-ui-test-capture-dom-trace', '0006', 227, 'DOM snapshot / trace', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_test_failure'}]}, (217, 229), (225, 'SHOULD')),
        ('failed-ui-test-capture-correlation', '0006', 228, 'correlation IDs / request IDs', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_test_failure'}]}, (217, 229), (225, 'SHOULD')),
        ('failed-ui-test-capture-pins-environment', '0006', 229, 'pins manifest / environment versions', 'SHOULD', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_test_failure'}]}, (217, 229), (225, 'SHOULD')),
    )),
    ('das.interaction.hfvi', 'hfvi', 'legacy-text-090eaa80-', (
        ('vis-header-doc-id', '0001', 25, '`Doc ID`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-owner', '0001', 26, '`Owner`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-status', '0001', 27, '`Status`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-governing-standard', '0001', 28, '`Governing standard`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-updated', '0001', 29, '`Last updated`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-scope', '0001', 30, '`Scope`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-parent-master-doc', '0001', 31, '`Parent Master Doc`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('vis-header-interaction-profile', '0001', 32, '`Interaction profile: hfvi_canvas_webgl_game`', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_vis_doc'}]}, (21, 32), (23, 'SHOULD')),
        ('scene-frame-budget', '0002', 53, 'frame budget (ms)', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_scene'}]}, (34, 53), (53, 'SHOULD')),
        ('scene-budget-measurement-method', '0002', 53, 'measurement method', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_scene'}]}, (34, 53), (53, 'SHOULD')),
        ('native-technical-anchor-vocabulary', '0005', 81, 'library-native names', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_technical_anchor'}]}, (55, 81), (81, 'SHOULD')),
        ('scene-state-contract-adjacent', '0009', 195, 'scene state', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}]}, (193, 198), (195, 'SHOULD')),
        ('interaction-state-contract-adjacent', '0009', 195, 'interaction state', 'SHOULD', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}]}, (193, 198), (195, 'SHOULD')),
    )),
)

# Reviewed remaining Appendix C/E obligations. Template rules apply only to
# actual adoption; role gates and suggested layouts keep their original SHOULD.
PLAYBOOKS += (
    ('das.architecture-modularity', 'repo', 'legacy-text-165796df-', (
        ('all-topologies-contract-explicit', '0006', 138, 'explicit', 'MUST', ('activity.contract_surface',), (105, 138), (138, 'MUST')),
        ('all-topologies-contract-testable', '0006', 138, 'testable', 'MUST', ('activity.contract_surface',), (105, 138), (138, 'MUST')),
        ('all-topologies-contract-governed', '0006', 138, 'governed', 'MUST', ('activity.contract_surface',), (105, 138), (138, 'MUST')),
        ('runtime-count-minimal-intentional', '0007', 162, 'Keep the number of runtime services small', 'MUST', ('activity.runtime_boundary_design',), (142, 162), (162, 'MUST')),
        ('pure-contract-execution-dependency-light', '0009', 184, 'dependency‑light', 'MUST', ('activity.pure_contract_execution',), (166, 184), (184, 'MUST')),
        ('pure-contract-execution-no-network-persistence', '0009', 184, 'MUST NOT require network/persistence', 'MUST', ('activity.pure_contract_execution',), (166, 184), (184, 'MUST NOT')),
        ('ai-output-schema-governed-contract', '0014', 290, 'AI output schemas are contracts', 'MUST', ('activity.ai_output_contract',), (283, 301), (290, 'MUST')),
        ('model-selection-shared-backend-algorithm-contract', '0015', 301, 'backend⇄algo contract', 'SHOULD', ('activity.model_selection',), (292, 301), (301, 'SHOULD')),
        ('boundary-single-contract-authority', '0026', 385, 'exactly one **authoring SSOT**', 'MUST', ('activity.contract_boundary',), (379, 404), (385, 'MUST')),
        ('avoid-prose-only-schema', '0027', 403, 'schema in prose only', 'SHOULD', ('activity.contract_surface',), (401, 404), (403, 'SHOULD')),
        ('predictable-small-checked-contract-upgrades', '0039', 511, 'keep upgrades small and require compatibility checks', 'SHOULD', ('activity.consumer_contract_upgrade',), (509, 513), (511, 'SHOULD')),
        ('evolution-assume-partial-upgrades-unless-enforced-atomic', '0041', 519, 'assume partial upgrades', 'MUST', ('activity.cross_repo_boundary',), (517, 525), (519, 'MUST')),
        ('algorithm-output-validation-before-emission', '0051', 615, 'Validate outputs at the boundary', 'MUST', ('activity.algorithm_boundary_output',), (605, 617), (615, 'MUST')),
        ('separate-contract-and-implementation-prs', '0057', 676, '“contract PR” plus per‑repo implementation PRs', 'SHOULD', ('activity.cross_repo_work',), (674, 681), (676, 'SHOULD')),
        ('contract-pr-automated-enforcement-change', '0060', 691, 'at least one automated check proving enforcement', 'MUST', ('activity.contract_change_pr',), (683, 700), (691, 'MUST')),
        ('stable-small-repository-interface', '0069', 794, 'small, stable interface', 'MUST', ('activity.repository_workflow',), (792, 807), (794, 'MUST')),
        ('recommended-role-gates-or-documented-equivalent', '0073', 811, 'or a documented equivalent', 'SHOULD', ('activity.repository_workflow',), (809, 820), (811, 'SHOULD')),
        ('not-applicable-gate-reason', '0075', 820, 'why', 'MUST', ('activity.gate_declared_not_applicable',), (809, 820), (820, 'MUST')),
        ('not-applicable-gate-replacement', '0075', 820, 'what replaces it', 'MUST', ('activity.gate_declared_not_applicable',), (809, 820), (820, 'MUST')),
        ('user-model-quality-at-least-one-lawful-gate', '0081', 859, 'at least one of', 'SHOULD', ('activity.user_affecting_model_output',), (857, 865), (859, 'SHOULD')),
        ('contracts-lowest-dependency-light-layer', '0083', 952, 'dependency‑light', 'SHOULD', ('component.contracts_hub',), (932, 952), (952, 'SHOULD')),
        ('algorithm-bounded-edit-adapters', '0050', 609, 'adapters/', 'SHOULD', ('component.algorithm',), (605, 617), (607, 'SHOULD')),
        ('algorithm-bounded-edit-pipelines', '0050', 610, 'pipelines/', 'SHOULD', ('component.algorithm',), (605, 617), (607, 'SHOULD')),
        ('algorithm-bounded-edit-prompts', '0050', 611, 'prompts/', 'SHOULD', ('component.algorithm',), (605, 617), (607, 'SHOULD')),
        ('algorithm-bounded-edit-tools', '0050', 612, 'tools/', 'SHOULD', ('component.algorithm',), (605, 617), (607, 'SHOULD')),
        ('algorithm-bounded-edit-evals', '0050', 613, 'evals/', 'SHOULD', ('component.algorithm',), (605, 617), (607, 'SHOULD')),
        ('user-visible-output-log-request-id', '0052', 617, '`requestId`', 'MUST', ('activity.algorithm_user_visible_output',), (605, 617), (617, 'MUST')),
        ('user-visible-output-log-prompt-id', '0052', 617, '`promptId`', 'MUST', ('activity.algorithm_user_visible_output',), (605, 617), (617, 'MUST')),
        ('user-visible-output-log-model-id', '0052', 617, '`modelId`', 'MUST', ('activity.algorithm_user_visible_output',), (605, 617), (617, 'MUST')),
        ('ai-task-folders', '0056', 646, 'which folders are in scope', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-exclusions', '0056', 647, 'explicit exclusions', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-impacted-specs-fixtures', '0056', 650, 'impacted specs + fixtures', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-stable-invariants', '0056', 651, 'invariants that must remain stable', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-change-classification', '0056', 652, 'change classification', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-evolution-mode', '0056', 653, 'Compatibility Mode unless proven otherwise', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-tier-and-deterministic-scope', '0056', 656, 'what must be deterministic', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-tier-replay-fixtures', '0056', 657, 'required replay harness / golden fixtures', 'MUST', ('activity.ai_task', 'task.tier_0_or_1'), (640, 672), (642, 'MUST')),
        ('ai-task-eval-dataset-pins', '0056', 658, 'pinned DatasetManifest(s)', 'MUST', ('activity.ai_task', 'task.eval_gates_present'), (640, 672), (642, 'MUST')),
        ('ai-task-enforced-budget-types', '0056', 661, 'tokens, time, external calls, cost', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-budget-scope', '0056', 662, 'stage/tool/pipeline', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-budget-termination', '0056', 662, 'termination behavior', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-required-artifacts', '0056', 666, 'required artifacts', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-smoke-expectations', '0056', 667, 'smoke flow expectations', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-no-opportunistic-refactor', '0056', 670, 'forbid opportunistic refactors', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-no-public-rename', '0056', 671, 'forbid renaming public identifiers', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('ai-task-no-unrequested-upgrade', '0056', 672, 'forbid dependency upgrades unless requested', 'MUST', ('activity.ai_task',), (640, 672), (642, 'MUST')),
        ('undeployed-producer-merge-tolerant-disabled-consumer', '0058', 680, 'consumer is tolerant', 'MUST', ('activity.consumer_merge_before_producer_deployment',), (674, 681), (678, 'MUST')),
        ('undeployed-producer-merge-defined-rollout-plan', '0058', 681, 'defined rollout plan', 'MUST', ('activity.consumer_merge_before_producer_deployment',), (674, 681), (678, 'MUST')),
        ('ai-change-small-prs', '0059', 687, 'many small PRs', 'SHOULD', ('activity.ai_change_pr',), (683, 691), (685, 'SHOULD')),
        ('ai-change-mergeable-releasable', '0059', 688, 'mergeable and releasable', 'SHOULD', ('activity.ai_change_pr',), (683, 691), (685, 'SHOULD')),
        ('ai-change-avoid-long-lived-drift', '0059', 689, 'avoid long‑lived branches', 'SHOULD', ('activity.ai_change_pr',), (683, 691), (685, 'SHOULD')),
        ('multi-repo-task-integration-or-fixture-run', '0061', 697, 'integration harness run (or fixture‑based compatibility run)', 'MUST', ('activity.cross_repo_work',), (693, 700), (695, 'MUST')),
        ('multi-repo-task-version-pin-updates', '0061', 698, 'explicit contract version pin updates', 'MUST', ('activity.cross_repo_work',), (693, 700), (695, 'MUST')),
        ('multi-repo-task-breaking-rollout-compat-plan', '0061', 699, 'documented rollout/compatibility plan', 'MUST', ('activity.cross_repo_work', 'change.contract_breaking'), (693, 700), (695, 'MUST')),
        ('multi-repo-overhead-automate-upgrades', '0062', 719, 'automate contract publish', 'SHOULD', ('activity.multi_repo_system',), (703, 723), (717, 'SHOULD')),
        ('multi-repo-overhead-one-pinned-harness', '0062', 720, 'one integration harness', 'SHOULD', ('activity.multi_repo_system',), (703, 723), (717, 'SHOULD')),
        ('multi-repo-overhead-standard-interfaces', '0062', 721, 'standardize repo interfaces', 'SHOULD', ('activity.multi_repo_system',), (703, 723), (717, 'SHOULD')),
        ('multi-repo-overhead-minimal-runtimes', '0062', 722, 'keep runtime services minimal', 'SHOULD', ('activity.multi_repo_system',), (703, 723), (717, 'SHOULD')),
        ('multi-repo-overhead-ci-caches', '0062', 723, 'cache CI builds/tests', 'SHOULD', ('activity.multi_repo_system',), (703, 723), (717, 'SHOULD')),
        ('retryable-boundary-keys', '0063', 751, 'idempotency keys', 'MUST', ('activity.retryable_boundary',), (747, 753), (749, 'MUST')),
        ('retryable-boundary-dedup', '0063', 752, 'dedup behavior', 'MUST', ('activity.retryable_boundary',), (747, 753), (749, 'MUST')),
        ('retryable-boundary-retry-classification', '0063', 753, 'safe retry classification', 'MUST', ('activity.retryable_boundary',), (747, 753), (749, 'MUST')),
        ('model-schema-validation-before-system-of-record', '0064', 759, 'persisting to the system of record', 'MUST', ('activity.model_output_persistence',), (755, 767), (757, 'MUST')),
        ('model-schema-validation-before-side-effects', '0064', 760, 'triggering side effects', 'MUST', ('activity.model_output_side_effect',), (755, 767), (757, 'MUST')),
        ('model-schema-validation-before-visible-nondraft-output', '0064', 761, 'unless explicitly marked “draft/unverified”', 'MUST', ('activity.model_output_display', 'output.not_explicitly_draft_or_unverified'), (755, 767), (757, 'MUST')),
        ('security-sensitive-prompt', '0066', 777, 'prompt templates', 'SHOULD', ('activity.ai_security_configuration',), (769, 777), (777, 'SHOULD')),
        ('security-sensitive-tool', '0066', 777, 'tool configurations', 'SHOULD', ('activity.ai_security_configuration',), (769, 777), (777, 'SHOULD')),
        ('security-sensitive-retrieval', '0066', 777, 'retrieval sources', 'SHOULD', ('activity.ai_security_configuration',), (769, 777), (777, 'SHOULD')),
        ('propagate-correlation-frontend', '0067', 783, 'frontend request headers', 'SHOULD', ('component.frontend',), (779, 788), (781, 'SHOULD')),
        ('propagate-correlation-backend', '0067', 784, 'backend logs and traces', 'SHOULD', ('component.backend',), (779, 788), (781, 'SHOULD')),
        ('propagate-correlation-algorithm', '0067', 785, 'algo logs', 'SHOULD', ('component.algorithm',), (779, 788), (781, 'SHOULD')),
        ('propagate-correlation-callback', '0067', 786, 'callbacks/webhooks', 'SHOULD', ('activity.callback_or_webhook',), (779, 788), (781, 'SHOULD')),
        ('recommended-role-gate-contracts-schema', '0074', 813, 'schema/spec validation', 'SHOULD', ('activity.contract_repository',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-contracts-fixture', '0074', 813, 'fixture decoding tests', 'SHOULD', ('activity.contract_repository',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-contracts-codegen', '0074', 813, 'reproducible codegen', 'SHOULD', ('activity.contract_repository',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-frontend-lint', '0074', 814, 'lint', 'SHOULD', ('component.frontend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-frontend-types', '0074', 814, 'typecheck', 'SHOULD', ('component.frontend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-frontend-tests', '0074', 814, 'tests', 'SHOULD', ('component.frontend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-frontend-build', '0074', 814, 'production build', 'SHOULD', ('component.frontend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-frontend-visible-ui-smoke', '0074', 814, 'browser-level', 'SHOULD', ('activity.user_facing_ui',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-backend-test', '0074', 815, 'tests', 'SHOULD', ('component.backend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-backend-build', '0074', 815, 'build/package', 'SHOULD', ('component.backend',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-backend-standard-static-analysis', '0074', 815, 'static analysis where standard', 'SHOULD', ('component.backend', 'repository.static_analysis_standard'), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-algorithm-boundary', '0074', 816, 'boundary checks', 'SHOULD', ('component.algorithm',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-algorithm-core-test', '0074', 816, 'unit tests for core transforms', 'SHOULD', ('component.algorithm',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-algorithm-pinned-eval', '0074', 816, 'pinned DatasetManifest split', 'SHOULD', ('component.algorithm',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-algorithm-tier0-replay', '0074', 816, 'replay verification for Tier 0', 'SHOULD', ('component.algorithm', 'repository.tier_0_pipelines'), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-algorithm-types', '0074', 816, 'lint/type checks', 'SHOULD', ('component.algorithm',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-integration-start-stop', '0074', 817, 'up/down', 'SHOULD', ('activity.integration_harness',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-integration-smoke', '0074', 817, 'smoke', 'SHOULD', ('activity.integration_harness',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-integration-compatibility', '0074', 817, 'compatibility runners', 'SHOULD', ('activity.integration_harness',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-data-evals-small-set', '0074', 818, 'small representative set', 'SHOULD', ('component.data_evals',), (809, 820), (811, 'SHOULD')),
        ('recommended-role-gate-data-evals-report', '0074', 818, 'deterministic', 'SHOULD', ('component.data_evals',), (809, 820), (811, 'SHOULD')),
        ('recommended-repository-doc-readme', '0076', 826, 'README.md', 'SHOULD', ('activity.repository_workflow',), (822, 830), (824, 'SHOULD')),
        ('recommended-repository-doc-architecture', '0076', 827, 'ARCHITECTURE.md', 'SHOULD', ('activity.repository_workflow',), (822, 830), (824, 'SHOULD')),
        ('recommended-repository-doc-contracts', '0076', 828, 'CONTRACTS.md', 'SHOULD', ('activity.repository_workflow',), (822, 830), (824, 'SHOULD')),
        ('recommended-repository-doc-ui-spec', '0076', 829, 'UI_SPEC.md', 'SHOULD', ('activity.user_facing_ui',), (822, 830), (824, 'SHOULD')),
        ('recommended-repository-doc-operational-runbook', '0076', 830, 'RUNBOOK.md', 'SHOULD', ('activity.repository_workflow', 'repository.operational_notes_applicable'), (822, 830), (824, 'SHOULD')),
        ('environment-variable-example-or-equivalent', '0077', 836, 'an `.env.example` (or equivalent)', 'MUST', ('activity.repository_workflow',), (832, 837), (834, 'MUST')),
        ('environment-secret-injection-policy', '0077', 837, 'clear policy for secret injection', 'MUST', ('activity.repository_workflow',), (832, 837), (834, 'MUST')),
        ('system-pipeline-end-to-end-smoke', '0080', 853, 'end‑to‑end smoke tests', 'MUST', ('activity.multi_repo_system',), (849, 855), (851, 'MUST')),
        ('system-pipeline-breaking-api-event-detection', '0080', 854, 'breaking‑change detection', 'MUST', ('activity.multi_repo_system',), (849, 855), (851, 'MUST')),
        ('system-pipeline-consumer-fixture-decode', '0080', 855, 'fixture decoding tests for consumers', 'MUST', ('activity.multi_repo_system',), (849, 855), (851, 'MUST')),
        ('recommended-contract-pr-schema', '0082', 888, 'updated spec/schema', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-fixtures', '0082', 889, 'updated fixtures', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-classification-and-plan', '0082', 890, 'change classification and compatibility plan', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-producer-or-staged-plan', '0082', 891, 'or a staged rollout plan', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-consumer-or-window', '0082', 892, 'or explicit compatibility window plan', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-critical-smoke-update', '0082', 893, 'integration smoke test update', 'SHOULD', ('activity.contract_change_pr', 'activity.critical_contract_boundary'), (884, 894), (886, 'SHOULD')),
        ('recommended-contract-pr-version-and-changelog', '0082', 894, 'version bump (SemVer) + changelog entry', 'SHOULD', ('activity.contract_change_pr',), (884, 894), (886, 'SHOULD')),
        ('model-output-untrusted-until-validated', '0012', 219, 'untrusted', 'MUST', ('activity.ai_model_output',), (209, 219), (219, 'MUST')),
        ('model-output-normalized-before-trust', '0012', 219, 'normalized', 'MUST', ('activity.ai_model_output',), (209, 219), (219, 'MUST')),
        ('cross-repo-change-verifiable-harness-or-fixtures', '0054', 629, 'Any cross‑repo contract change', 'MUST', ('activity.cross_repo_contract_change',), (621, 634), (629, 'MUST')),
        ('independent-deployment-version-matrix-supported-window', '0055', 634, 'compatibility matrix', 'SHOULD', ('activity.independent_deployments',), (621, 634), (634, 'SHOULD')),
        ('cross-repo-request-response-traceable-id', '0068', 788, 'requestId', 'MUST', ('activity.cross_repo_request_response',), (779, 788), (788, 'MUST')),
    )),
    ('das.governance.documentation', 'template', 'legacy-text-5046745a-', (
        ('fenced-literals-not-placeholder-replacement', '0001', 23, 'MUST NOT be treated as placeholders', 'MUST', ('activity.project_master_doc_template',), (14, 27), (23, 'MUST NOT')),
        ('canonical-doc-path-stable-across-branches', '0002', 81, 'stable across branches', 'MUST', ('activity.project_master_doc_template',), (76, 105), (81, 'MUST')),
        ('activation-filled-required-prose-table-fields', '0003', 111, 'All `{{REQUIRED_PLACEHOLDER}}` fields are filled.', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('activation-actual-hfvi-populated-vis', '0003', 112, 'Appendix K (VIS) exists and is populated for each HFVI surface', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation', 'profile.hfvi'), (107, 119), (109, 'MUST NOT')),
        ('activation-l2-current-context-pack', '0003', 113, 'Context Pack', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation', 'profile.l2'), (107, 119), (109, 'MUST NOT')),
        ('activation-blockers-resolved-or-adr-deferred', '0003', 114, 'resolved or explicitly deferred via ADR', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('activation-complete-boundary-contract-index', '0003', 115, 'complete **Contract Inventory Index**', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('activation-exact-verify-commands', '0003', 117, 'exact `verify` commands', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('activation-initial-wbs-scopes', '0003', 118, 'initial WBS', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('activation-acceptance-checklist', '0003', 119, 'acceptance checklist', 'MUST', ('activity.project_master_doc_template', 'activity.document_activation'), (107, 119), (109, 'MUST NOT')),
        ('material-doc-change-changelog', '0005', 184, '§0.7 Change Log', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_material'), (176, 186), (183, 'MUST')),
        ('material-doc-change-pr-or-adr', '0005', 185, 'PR/ADR', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_material'), (176, 186), (183, 'MUST')),
        ('material-doc-change-relevant-sections', '0005', 186, 'update relevant sections', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_material'), (176, 186), (183, 'MUST')),
        ('active-branch-plan-and-completion-copy', '0006', 204, 'reflecting its plan and completion state', 'SHOULD', ('activity.project_master_doc_template', 'activity.active_branch'), (202, 226), (204, 'SHOULD')),
        ('all-known-baseline-drift-listed', '0007', 224, 'MUST list all', 'MUST', ('activity.project_master_doc_template', 'activity.branch_baseline_review'), (202, 226), (224, 'MUST')),
        ('canonical-glossary-boundary-terminology', '0008', 230, 'SHOULD be defined here', 'SHOULD', ('activity.project_master_doc_template',), (228, 240), (230, 'SHOULD')),
        ('roles-roles', '0010', 284, 'roles', 'MUST', ('activity.project_master_doc_template',), (282, 294), (284, 'MUST')),
        ('roles-permission-boundaries', '0010', 284, 'permission boundaries', 'MUST', ('activity.project_master_doc_template',), (282, 294), (284, 'MUST')),
        ('roles-tenant-boundary', '0010', 284, 'tenant boundary', 'MUST', ('activity.project_master_doc_template', 'system.multi_tenant'), (282, 294), (284, 'MUST')),
        ('released-permission-identifiers-stable', '0011', 292, 'stable once released', 'MUST', ('activity.project_master_doc_template', 'activity.released_permission_contract'), (282, 294), (292, 'MUST')),
        ('workflow-testable-end-to-end', '0012', 298, 'testable end-to-end', 'MUST', ('activity.project_master_doc_template',), (296, 310), (298, 'MUST')),
        ('requirement-inputs', '0013', 326, 'inputs', 'MUST', ('activity.project_master_doc_template',), (324, 342), (326, 'MUST')),
        ('requirement-outputs', '0013', 326, 'outputs', 'MUST', ('activity.project_master_doc_template',), (324, 342), (326, 'MUST')),
        ('requirement-edge-cases', '0013', 326, 'edge cases', 'MUST', ('activity.project_master_doc_template',), (324, 342), (326, 'MUST')),
        ('requirement-acceptance-criteria', '0013', 326, 'acceptance criteria', 'MUST', ('activity.project_master_doc_template',), (324, 342), (326, 'MUST')),
        ('embedded-image-owner', '0016', 380, 'owner', 'MUST', ('activity.project_master_doc_template', 'activity.embedded_ui_image'), (374, 383), (379, 'MUST')),
        ('embedded-image-updated', '0016', 381, 'last updated date', 'MUST', ('activity.project_master_doc_template', 'activity.embedded_ui_image'), (374, 383), (379, 'MUST')),
        ('embedded-image-decision', '0016', 382, 'what decision it supports', 'MUST', ('activity.project_master_doc_template', 'activity.embedded_ui_image'), (374, 383), (379, 'MUST')),
        ('embedded-image-requirements', '0016', 383, 'which requirement(s) it satisfies', 'MUST', ('activity.project_master_doc_template', 'activity.embedded_ui_image'), (374, 383), (379, 'MUST')),
        ('architectural-invariants-or-recorded-adr-change', '0018', 490, 'unless an ADR changes them', 'MUST', ('activity.project_master_doc_template',), (488, 495), (490, 'MUST')),
        ('same-artifact-across-environments', '0021', 558, 'Same build artifact', 'SHOULD', ('activity.project_master_doc_template', 'activity.project_deployment'), (552, 566), (558, 'SHOULD')),
        ('environment-data-classification', '0021', 559, 'allowed data classification', 'MUST', ('activity.project_master_doc_template', 'activity.project_deployment'), (552, 566), (559, 'MUST')),
        ('environment-no-dev-production-pii-default', '0021', 559, 'no production PII in dev by default', 'MUST', ('activity.project_master_doc_template', 'activity.project_deployment'), (552, 566), (559, 'MUST')),
        ('explicit-rollback-reversibility', '0021', 560, 'what is reversible vs not', 'MUST', ('activity.project_master_doc_template', 'activity.project_deployment'), (552, 566), (560, 'MUST')),
        ('ci-avoid-live-vendor-calls', '0022', 590, 'CI SHOULD avoid live vendor calls', 'SHOULD', ('activity.project_master_doc_template', 'activity.repository_ci'), (574, 592), (590, 'SHOULD')),
        ('boundary-contract-schema', '0023', 599, 'schema', 'MUST', ('activity.project_master_doc_template', 'activity.cross_boundary_contract'), (596, 609), (598, 'MUST')),
        ('boundary-contract-semantics', '0023', 599, 'semantics', 'MUST', ('activity.project_master_doc_template', 'activity.cross_boundary_contract'), (596, 609), (598, 'MUST')),
        ('boundary-contract-fixtures', '0023', 599, 'fixtures', 'MUST', ('activity.project_master_doc_template', 'activity.cross_boundary_contract'), (596, 609), (598, 'MUST')),
        ('boundary-contract-checks', '0023', 599, 'executable checks', 'MUST', ('activity.project_master_doc_template', 'activity.cross_boundary_contract'), (596, 609), (598, 'MUST')),
        ('contract-stable-id', '0025', 605, 'stable `CONTRACT_ID`', 'MUST', ('activity.project_master_doc_template', 'activity.contract_surface'), (601, 609), (605, 'MUST')),
        ('contract-schema-version', '0025', 605, 'schema version', 'MUST', ('activity.project_master_doc_template', 'activity.contract_surface'), (601, 609), (605, 'MUST')),
        ('contract-boundary-casing-adapter', '0025', 607, 'adapt at the boundary', 'MUST', ('activity.project_master_doc_template', 'activity.contract_surface'), (601, 609), (607, 'MUST')),
        ('contract-project-inventory', '0025', 609, 'listed in §5.2', 'MUST', ('activity.project_master_doc_template', 'activity.contract_surface'), (601, 609), (609, 'MUST')),
        ('api-table-canonical-registry-index', '0026', 635, 'human-readable index', 'SHOULD', ('activity.project_master_doc_template', 'activity.api_inventory'), (632, 641), (635, 'SHOULD')),
        ('actual-job-envelope-minimum-schema-version', '0028', 652, 'schemaVersion', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-job-id', '0028', 653, 'jobId', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-job-type', '0028', 654, 'jobType', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-status', '0028', 655, 'status', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-created-at', '0028', 656, 'createdAt', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-updated-at', '0028', 656, 'updatedAt', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-attempt-retry', '0028', 657, 'attempt counters', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-applicable-correlation', '0028', 658, 'correlation IDs (as applicable)', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations', 'job.correlation_applicable'), (643, 665), (650, 'Required fields')),
        ('actual-job-envelope-minimum-diagnostics', '0028', 659, 'stable codes + structured fields', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (650, 'Required fields')),
        ('actual-job-terminal-no-regression', '0029', 663, 'Terminal states MUST NOT transition back to non-terminal states', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (663, 'MUST NOT')),
        ('actual-job-cancellation-semantics', '0029', 664, 'best-effort vs guaranteed', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (664, 'MUST')),
        ('actual-job-bounded-retry', '0029', 665, 'bounded', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (665, 'MUST')),
        ('actual-job-idempotent-retry', '0029', 665, 'idempotent', 'MUST', ('activity.project_master_doc_template', 'activity.long_running_operations'), (643, 665), (665, 'MUST')),
        ('execution-plan-precise', '0032', 888, 'precise', 'MUST', ('activity.project_master_doc_template',), (886, 909), (888, 'MUST')),
        ('execution-plan-scoped', '0032', 888, 'scoped', 'MUST', ('activity.project_master_doc_template',), (886, 909), (888, 'MUST')),
        ('execution-plan-verifiable', '0032', 888, 'verifiable', 'MUST', ('activity.project_master_doc_template',), (886, 909), (888, 'MUST')),
        ('execution-plan-contains-contracts', '0032', 889, 'contracts', 'MUST', ('activity.project_master_doc_template',), (886, 909), (889, 'MUST')),
        ('execution-plan-contains-tasks', '0032', 889, 'tasks', 'MUST', ('activity.project_master_doc_template',), (886, 909), (889, 'MUST')),
        ('execution-plan-contains-gates', '0032', 889, 'gates', 'MUST', ('activity.project_master_doc_template',), (886, 909), (889, 'MUST')),
        ('execution-plan-no-code-internals', '0032', 889, 'SHOULD NOT include code-level details', 'SHOULD', ('activity.project_master_doc_template',), (886, 909), (889, 'SHOULD NOT')),
        ('verification-exact-contracts-commands', '0033', 902, 'VERIFY_CMD_CONTRACTS', 'MUST', ('activity.project_master_doc_template', 'component.contracts'), (891, 906), (901, 'MUST')),
        ('verification-exact-frontend-commands', '0033', 903, 'VERIFY_CMD_FRONTEND', 'MUST', ('activity.project_master_doc_template', 'component.frontend'), (891, 906), (901, 'MUST')),
        ('verification-exact-backend-commands', '0033', 904, 'VERIFY_CMD_BACKEND', 'MUST', ('activity.project_master_doc_template', 'component.backend'), (891, 906), (901, 'MUST')),
        ('verification-exact-algorithm-commands', '0033', 905, 'VERIFY_CMD_ALGO', 'MUST', ('activity.project_master_doc_template', 'component.algorithm'), (891, 906), (901, 'MUST')),
        ('verification-exact-integration-commands', '0033', 906, 'VERIFY_CMD_INTEGRATION', 'MUST', ('activity.project_master_doc_template', 'component.integration'), (891, 906), (901, 'MUST')),
        ('task-starts-planned', '0034', 922, 'Every task starts as `planned`', 'MUST', ('activity.project_master_doc_template', 'activity.task_creation'), (912, 924), (922, 'MUST')),
        ('partial-or-done-objective-evidence', '0034', 923, 'objective Evidence', 'MUST', ('activity.project_master_doc_template', 'activity.task_partial_or_done'), (912, 924), (923, 'MUST')),
        ('blocked-task-dependency-record', '0034', 924, 'record the blocking dependency', 'SHOULD', ('activity.project_master_doc_template', 'activity.task_blocked'), (912, 924), (924, 'SHOULD')),
        ('overall-plan-active-copies-update-or-explicit-divergence', '0035', 1063, 'or explicitly document divergence', 'MUST', ('activity.project_master_doc_template', 'change.overall_plan'), (1060, 1091), (1063, 'MUST')),
        ('branch-sync-product-scope', '0036', 1069, 'product scope', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_product_scope'), (1060, 1091), (1067, 'MUST')),
        ('branch-sync-contract-surfaces', '0036', 1070, 'contract surfaces', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_contract_surfaces'), (1060, 1091), (1067, 'MUST')),
        ('branch-sync-architecture', '0036', 1071, 'architecture boundaries', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_architecture'), (1060, 1091), (1067, 'MUST')),
        ('branch-sync-rollout-or-window', '0036', 1072, 'rollout strategy or compatibility windows', 'MUST', ('activity.project_master_doc_template', 'change.master_doc_rollout_or_window'), (1060, 1091), (1067, 'MUST')),
        ('recommended-branch-sync-acceptance', '0037', 1076, 'acceptance criteria', 'SHOULD', ('activity.project_master_doc_template', 'change.master_doc_acceptance'), (1060, 1091), (1074, 'SHOULD')),
        ('recommended-branch-sync-test-gates', '0037', 1077, 'test gates', 'SHOULD', ('activity.project_master_doc_template', 'change.master_doc_test_gates'), (1060, 1091), (1074, 'SHOULD')),
        ('recommended-branch-sync-risk-or-question', '0037', 1078, 'risk/open-questions', 'SHOULD', ('activity.project_master_doc_template', 'change.master_doc_risk_or_question'), (1060, 1091), (1074, 'SHOULD')),
        ('boundary-errors-data-not-language-exceptions', '0030', 677, 'not language-specific exceptions across boundaries', 'MUST', ('activity.project_master_doc_template', 'activity.cross_boundary_errors'), (675, 687), (677, 'MUST')),
    )),
)

PLAYBOOK_ALIASES = (
    ('legacy-text-33cd7d6c-0001', tuple('das.governance.verification-release.verify.' + name for name in ('reproducible-tooling-lock', 'hermetic-pinned-environment', 'suite-lock', 'version-closure-manifest'))),
    ('legacy-text-33cd7d6c-0002', ('das.governance.verification-release.verify.registry-publication',)),
    ('legacy-text-33cd7d6c-0003', ('das.governance.verification-release.verify.emit-machine-report',)),
    ('legacy-text-33cd7d6c-0004', ('das.governance.verification-release.verify.high-stakes-verifier-self-tests',)),
    ('legacy-text-33cd7d6c-0005', ('das.governance.verification-release.verify.standard-immutable-snapshot', 'das.governance.verification-release.verify.mirror-originating-snapshot')),
    ('legacy-text-33cd7d6c-0006', ('das.governance.verification-release.verify.closure-structured-pins',)),
    ('legacy-text-33cd7d6c-0007', tuple('das.governance.verification-release.verify.' + name for name in ('closure-valid-kind-pin-pairs', 'critical-no-clone-tip', 'closure-no-bare-string-pins'))),
    ('legacy-text-33cd7d6c-0008', ('das.governance.verification-release.verify.no-report-as-blocking-gate',)),
    ('legacy-text-33cd7d6c-0009', ('das.governance.verification-release.verify.critical-no-clone-tip', 'das.governance.verification-release.verify.release-tool-no-floating-source')),
    ('legacy-text-33cd7d6c-0010', ('das.governance.verification-release.verify.pre-release-lock-closure-check',)),
    ('legacy-text-33cd7d6c-0011', tuple('das.governance.verification-release.verify.registry-' + name for name in ('gate-id', 'kind', 'cadence', 'enforcement', 'command', 'owner', 'no-result-policy', 'expected-artifacts'))),
    ('legacy-text-33cd7d6c-0012', ('das.governance.verification-release.verify.report-gate-outcomes',)),
    ('legacy-text-33cd7d6c-0013', ('das.governance.verification-release.verify.report-no-results-fails',)),
    ('legacy-text-33cd7d6c-0014', ('das.core.manifest.published-required-paths', 'das.core.manifest.published-link-closure')),
    ('legacy-text-33cd7d6c-0015', tuple('das.core.manifest.release-check-' + name for name in ('required-paths', 'normative-refs', 'supporting-refs'))),
    ('legacy-text-33cd7d6c-0016', tuple('das.governance.verification-release.verify.' + name for name in ('mirror-declared', 'mirror-originating-snapshot', 'mirror-no-local-edits-or-extension', 'pre-upgrade-mirror-comparison'))),
    ('legacy-text-e80f2d11-0002', tuple('das.ai-runtime-evaluation.algorithm.' + name for name in ('replay-golden-fixtures', 'replay-harness', 'replay-ci'))),
    ('legacy-text-d2a39e69-0001', tuple('das.architecture-modularity.domain.scenario-trace-' + name for name in ('workflow-requirement', 'contracts', 'gate'))),
    ('legacy-text-d2a39e69-0002', ('das.architecture-modularity.domain.cross-repo-integration-harness',)),
    ('legacy-text-d2a39e69-0004', ('das.architecture-modularity.domain.tier-bdd-offline-default',)),
    ('legacy-text-d2a39e69-0005', ('das.architecture-modularity.domain.critical-executable-scenarios',)),
    ('legacy-text-329162a7-0004', tuple('das.architecture-modularity.domain.boundary-event-' + name for name in ('fixtures', 'executable-checks'))),
    ('legacy-text-329162a7-0006', ('das.architecture-modularity.domain.domain-class-invariants',)),
    ('legacy-text-4d6c4f21-0003', tuple('das.interaction.standard-ui.ui.default-gate-' + name for name in ('boundary', 'unit', 'smoke'))),
    ('legacy-guide-4d6c4f21-checklist', tuple('das.interaction.standard-ui.ui.citation-' + name for name in ('structured-contract', 'integrity', 'specified-interactions', 'accessible', 'graceful-missing-invalid'))),
    ('legacy-guide-4d6c4f21-checklist', tuple('das.interaction.standard-ui.ui.' + name for name in ('kit-storybook', 'kit-stories-canonical', 'kit-state-snapshots'))),
    ('legacy-text-4d6c4f21-0003', tuple('das.interaction.standard-ui.ui.' + name for name in ('kit-storybook', 'kit-stories-canonical', 'kit-state-snapshots'))),
)

PLAYBOOK_ALIASES += (
    ('legacy-text-16280e97-0001', ('das.core.principles.keyword-synonym-interpretation',)),
    ('legacy-text-16280e97-0010', ('das.security-agent.operational.no-secrets-in-source',)),
    ('legacy-text-16280e97-0014', ('das.governance.verification-release.platform.dependency-and-tool-locks',)),
)

PLAYBOOK_ALIASES += (
    ('legacy-text-1be6a1ed-0001', ('das.core.principles.keyword-synonym-interpretation',)),
    ('legacy-text-1be6a1ed-0003', ('das.governance.documentation.doc.boundary-decision-owner', 'das.contracts-compatibility.multirepo.contract-one-decision-owner')),
    ('legacy-text-1be6a1ed-0004', ('das.governance.documentation.doc.material-change-doc-or-waiver',)),
    ('legacy-text-1be6a1ed-0006', ('das.governance.documentation.doc.doc-owner',)),
    ('legacy-text-1be6a1ed-0007', ('das.governance.documentation.doc.doc-owner', 'das.governance.documentation.doc.boundary-decision-owner', 'das.governance.documentation.doc.doc-approval-rule')),
    ('legacy-text-1be6a1ed-0010', ('das.governance.documentation.doc.sub-doc-control-header',)),
    ('legacy-text-1be6a1ed-0011', ('das.governance.documentation.doc.doc-owner', 'das.governance.documentation.doc.sub-doc-status', 'das.governance.documentation.doc.master-doc-status')),
    ('legacy-text-1be6a1ed-0012', ('das.governance.documentation.doc.one-master-doc-entrypoint', 'das.governance.documentation.doc.delegated-index-profiles', 'das.governance.documentation.doc.delegated-index-topology-hub', 'das.governance.documentation.doc.delegated-index-contract-inventory', 'das.governance.documentation.doc.delegated-index-traceability', 'das.governance.documentation.doc.delegated-index-verify', 'das.governance.documentation.doc.delegated-index-execution-plan')),
    ('legacy-text-1be6a1ed-0014', ('das.governance.documentation.doc.doc-pr-flow',)),
    ('legacy-text-1be6a1ed-0018', ('das.governance.documentation.doc.doc-approval-rule', 'das.governance.documentation.doc.doc-verify-links', 'das.governance.documentation.doc.doc-verify-metadata', 'das.governance.documentation.doc.doc-verify-unique-ids')),
    ('legacy-text-1be6a1ed-0021', ('das.core.profile.external-compatibility',)),
    ('legacy-text-1be6a1ed-0022', ('das.governance.documentation.doc.doc-pr-flow',)),
    ('legacy-text-1be6a1ed-0027', ('das.governance.documentation.doc.dispute-decision-record',)),
)

PLAYBOOK_ALIASES += (
    ('legacy-text-8d48152b-0001', ('das.governance.documentation.doc.ui-spec-screen-route-ids', 'das.governance.documentation.doc.ui-spec-selectors')),
    ('legacy-text-8d48152b-0003', ('das.governance.documentation.doc.ui-spec-traceability',)),
    ('legacy-text-8d48152b-0004', ('das.interaction.standard-ui.ui.design-code-traceability',)),
    ('legacy-text-8d48152b-0005', ('das.interaction.standard-ui.ui.ai-distinct-thinking', 'das.interaction.standard-ui.ui.repair-ux')),
    ('legacy-text-090eaa80-0002', ('das.interaction.hfvi.hfvi.ui-vis-scene-links',)),
    ('legacy-text-090eaa80-0003', ('das.interaction.hfvi.hfvi.vis-invariants',)),
    ('legacy-text-090eaa80-0004', ('das.interaction.hfvi.hfvi.vis-invariants', 'das.interaction.hfvi.hfvi.debug-explicit-invariants', 'das.interaction.hfvi.hfvi.debug-validate-invariants')),
    ('legacy-text-090eaa80-0005', ('das.interaction.hfvi.hfvi.technical-anchors',)),
    ('legacy-text-090eaa80-0006', ('das.interaction.hfvi.hfvi.motion-token-expression', 'das.interaction.hfvi.hfvi.motion-stable-ids')),
    ('legacy-text-090eaa80-0007', ('das.interaction.hfvi.hfvi.no-hardcoded-motion', 'das.interaction.hfvi.hfvi.prototype-motion-bounds', 'das.interaction.hfvi.hfvi.prototype-motion-owner', 'das.interaction.hfvi.hfvi.prototype-motion-expiry')),
    ('legacy-text-090eaa80-0008', ('das.interaction.hfvi.hfvi.debug-hit-areas', 'das.interaction.hfvi.hfvi.debug-boxes', 'das.interaction.hfvi.hfvi.debug-anchors')),
    ('legacy-text-090eaa80-0009', ('das.interaction.hfvi.hfvi.deterministic-input-replay', 'das.interaction.hfvi.hfvi.invariants-plus-diffs', 'das.interaction.hfvi.hfvi.visual-gate')),
)

# Repeated carriers reuse the existing ID, force and applicability. Full
# scopes preserve examples, legal alternatives and precedence.
PLAYBOOK_ALIASES += (
    ('legacy-text-de7276bb-0001', ('das.core.principles.keyword-synonym-interpretation', 'das.core.principles.prefer-primary-keywords')),
    ('legacy-text-de7276bb-0002', ('das.core.principles.keyword-synonym-interpretation', 'das.core.principles.should-deviation-justification-controls')),
    ('legacy-text-de7276bb-0003', ('das.core.principles.no-repo-rule-weakening',)),
    ('legacy-text-de7276bb-0004', ('das.core.profile.conformance-one',)),
    ('legacy-text-de7276bb-0006', ('das.governance.verification-release.verify.default-fast-mode', 'das.governance.verification-release.verify.fast-five-minute-target', 'das.core.profile.external-compatibility', 'das.governance.documentation.doc.master-doc-canonical')),
    ('legacy-text-de7276bb-0008', ('das.core.profile.interaction-one',)),
    ('legacy-text-de7276bb-0032', ('das.contracts-compatibility.contract.serialized-camel-case',)),
    ('legacy-text-de7276bb-0064', ('das.architecture-modularity.sdmm.compatible-additive', 'das.architecture-modularity.sdmm.compatible-reader', 'das.architecture-modularity.sdmm.breaking-migration-window')),
    ('legacy-text-de7276bb-0102', ('das.ai-runtime-evaluation.algorithm.pipeline-result', 'das.ai-runtime-evaluation.algorithm.exact-manifest-pointer', 'das.ai-runtime-evaluation.algorithm.lossless-job-wrapping', 'das.architecture-modularity.backend.canonical-error-mapping', 'das.architecture-modularity.backend.full-pipeline-result-every-attempt')),
    ('legacy-text-de7276bb-0106', ('das.governance.documentation.doc.sub-doc-control-header', 'das.governance.documentation.doc.sub-doc-id', 'das.governance.documentation.doc.sub-doc-owner', 'das.governance.documentation.doc.sub-doc-status', 'das.governance.documentation.doc.sub-doc-standard', 'das.governance.documentation.doc.sub-doc-updated', 'das.governance.documentation.doc.sub-doc-scope')),
    ('legacy-text-de7276bb-0111', ('das.governance.documentation.doc.module-master-doc', 'das.governance.documentation.doc.module-determinism-applicability', 'das.governance.documentation.doc.module-determinism-section', 'das.governance.documentation.doc.module-na-determinism-reason')),
    ('legacy-text-de7276bb-0160', ('das.architecture-modularity.sdmm.explicit-graph', 'das.architecture-modularity.sdmm.enforce-graph')),
    ('legacy-text-de7276bb-0161', ('das.architecture-modularity.topology.contract-schema', 'das.architecture-modularity.topology.contract-positive-fixtures', 'das.architecture-modularity.topology.contract-negative-fixtures')),
    ('legacy-text-de7276bb-0162', ('das.architecture-modularity.topology.contract-schema', 'das.architecture-modularity.topology.contract-positive-fixtures', 'das.architecture-modularity.topology.contract-negative-fixtures', 'das.governance.verification-release.verify.one-canonical-entrypoint', 'das.governance.verification-release.minimum.contracts-changed-compatibility')),
    ('legacy-text-38706f1d-0002', ('das.core.principles.keyword-synonym-interpretation', 'das.core.principles.should-deviation-justification-controls')),
    ('legacy-text-38706f1d-0003', ('das.core.principles.keyword-synonym-interpretation',)),
    ('legacy-text-06572a96-0001', ('das.core.manifest.artifact-version', 'das.core.manifest.manifest-version')),
    ('legacy-text-06572a96-0002', ('das.core.profile.conformance-one', 'das.core.profile.conformance-explicit-new-document', 'das.core.profile.conformance-legacy-declaration', 'das.core.profile.interaction-one', 'das.core.profile.interaction-explicit-new-document', 'das.core.profile.interaction-legacy-declaration')),
    ('legacy-text-f39710c0-0001', ('das.core.profile.conformance-one', 'das.core.profile.interaction-one', 'das.core.profile.external-compatibility', 'das.governance.documentation.doc.master-doc-canonical', 'das.governance.documentation.doc.master-doc-versioned', 'das.governance.documentation.doc.master-doc-contract-inventory', 'das.governance.documentation.doc.master-doc-requirement-trace', 'das.governance.documentation.doc.master-doc-verify', 'das.governance.documentation.doc.master-doc-execution-plan', 'das.governance.documentation.doc.drift-record-immediately', 'das.governance.documentation.doc.drift-one-outcome', 'das.governance.documentation.doc.drift-decision-record', 'das.architecture-modularity.topology.contract-schema', 'das.architecture-modularity.topology.contract-semantics', 'das.architecture-modularity.topology.contract-positive-fixtures', 'das.architecture-modularity.topology.contract-negative-fixtures', 'das.architecture-modularity.topology.contract-ci-checks', 'das.architecture-modularity.topology.contract-compatibility-runners', 'das.governance.verification-release.verify.one-canonical-entrypoint', 'das.core.manifest.machine-readable-release', 'das.core.manifest.extension-machine-manifest', 'das.core.manifest.extension-no-silent-enum-widening')),
    ('legacy-text-165796df-0001', ('das.core.principles.keyword-synonym-interpretation', 'das.core.principles.prefer-primary-keywords')),
    ('legacy-text-165796df-0002', ('das.core.principles.keyword-synonym-interpretation', 'das.core.principles.should-deviation-justification-controls')),
    ('legacy-text-165796df-0003', ('das.architecture-modularity.topology.cross-repo-compatible-or-atomic',)),
    ('legacy-text-165796df-0004', ('das.architecture-modularity.topology.no-size-only-runtime-split',)),
    ('legacy-text-165796df-0005', ('das.architecture-modularity.topology.prefer-sdmm',)),
    ('legacy-text-165796df-0008', ('das.architecture-modularity.topology.hub-no-business-logic', 'das.architecture-modularity.topology.hub-no-orchestration')),
    ('legacy-text-165796df-0010', ('das.architecture-modularity.topology.frontend-sdmm',)),
    ('legacy-text-165796df-0011', ('das.architecture-modularity.topology.backend-modular-monolith',)),
    ('legacy-text-165796df-0012', ('das.security-agent.operational.untrusted-model-schema',)),
    ('legacy-text-165796df-0013', ('das.architecture-modularity.topology.eval-data-scrubbed-or-approved',)),
    ('legacy-text-165796df-0026', ('das.architecture-modularity.topology.one-authoring-ssot', 'das.architecture-modularity.topology.generated-other-representations', 'das.architecture-modularity.topology.representation-drift-checks')),
    ('legacy-text-165796df-0027', ('das.architecture-modularity.topology.linkable-semantics-doc', 'das.architecture-modularity.topology.stable-semantics-reference')),
    ('legacy-text-165796df-0042', ('das.architecture-modularity.topology.cross-repo-compatible-or-atomic',)),
    ('legacy-text-165796df-0045', ('das.contracts-compatibility.contract.breaking-expand-contract', 'das.contracts-compatibility.contract.breaking-window')),
    ('legacy-text-165796df-0047', ('das.architecture-modularity.topology.frontend-sdmm',)),
    ('legacy-text-165796df-0048', ('das.architecture-modularity.topology.backend-modular-monolith',)),
    ('legacy-text-165796df-0049', ('das.architecture-modularity.backend.boundary-validation', 'das.architecture-modularity.backend.canonical-error-mapping')),
    ('legacy-text-165796df-0053', ('das.governance.verification-release.integration.one-command-startup', 'das.governance.verification-release.integration.minimal-critical-smoke-suite', 'das.governance.verification-release.integration.critical-consumer-golden-decode', 'das.architecture-modularity.topology.minimal-system-harness', 'das.architecture-modularity.topology.system-smoke-flow', 'das.architecture-modularity.topology.harness-compatibility-decode')),
    ('legacy-text-165796df-0054', ('das.governance.verification-release.integration.contract-change-fixtures', 'das.governance.verification-release.integration.contract-change-checks')),
    ('legacy-text-165796df-0055', ('das.governance.verification-release.integration.supported-window-documented-tested',)),
    ('legacy-text-165796df-0064', ('das.architecture-modularity.backend.model-output-before-state-effects',)),
    ('legacy-text-165796df-0065', ('das.security-agent.operational.no-secrets-in-source', 'das.security-agent.operational.runtime-secret-manager-injection', 'das.security-agent.operational.ci-secret-sast-scanning')),
    ('legacy-text-165796df-0068', ('das.architecture-modularity.backend.end-to-end-correlation',)),
    ('legacy-text-165796df-0070', ('das.governance.verification-release.verify.one-canonical-entrypoint',)),
    ('legacy-text-165796df-0071', ('das.governance.verification-release.verify.canonical-local-ci-gate', 'das.governance.verification-release.verify.fail-fast-boundary-contract')),
    ('legacy-text-165796df-0072', ('das.governance.verification-release.verify.fast-hermetic-or-documented-stubs',)),
    ('legacy-text-165796df-0078', ('das.governance.verification-release.verify.canonical-local-ci-gate',)),
    ('legacy-text-165796df-0079', ('das.governance.verification-release.verify.verify-machine-summary',)),
    ('legacy-text-5046745a-0002', ('das.governance.documentation.doc.master-doc-canonical', 'das.governance.documentation.doc.master-doc-versioned', 'das.governance.documentation.doc.master-doc-conformance', 'das.governance.documentation.doc.master-doc-interaction', 'das.governance.documentation.doc.master-doc-status', 'das.governance.documentation.doc.master-doc-standard')),
    ('legacy-text-5046745a-0004', ('das.core.principles.keyword-synonym-interpretation',)),
    ('legacy-text-5046745a-0005', ('das.governance.documentation.doc.material-change-doc-or-waiver',)),
    ('legacy-text-5046745a-0009', ('das.contracts-compatibility.contract.stable-profile-id', 'das.contracts-compatibility.contract.stable-config-identity', 'das.contracts-compatibility.contract.run-config-identity', 'das.contracts-compatibility.contract.job-config-identity')),
    ('legacy-text-5046745a-0013', ('das.governance.documentation.doc.master-doc-requirement-trace',)),
    ('legacy-text-5046745a-0014', ('das.governance.documentation.doc.ui-spec-appendix',)),
    ('legacy-text-5046745a-0015', ('das.interaction.standard-ui.ui.design-code-traceability',)),
    ('legacy-text-5046745a-0019', ('das.governance.verification-release.verify.one-canonical-entrypoint', 'das.governance.verification-release.verify.fast-hermetic-or-documented-stubs')),
    ('legacy-text-5046745a-0020', ('das.architecture-modularity.sdmm.public-imports', 'das.architecture-modularity.sdmm.no-deep-imports')),
    ('legacy-text-5046745a-0024', ('das.contracts-compatibility.contract.serialized-camel-case', 'das.contracts-compatibility.contract.compat-api', 'das.contracts-compatibility.contract.compat-events', 'das.contracts-compatibility.contract.compat-persisted')),
    ('legacy-text-5046745a-0025', ('das.contracts-compatibility.contract.serialized-camel-case', 'das.contracts-compatibility.contract.compat-api', 'das.contracts-compatibility.contract.compat-events', 'das.contracts-compatibility.contract.compat-persisted')),
    ('legacy-text-5046745a-0027', ('das.architecture-modularity.topology.one-authoring-ssot', 'das.architecture-modularity.topology.generated-other-representations', 'das.architecture-modularity.topology.representation-drift-checks')),
    ('legacy-text-5046745a-0030', ('das.architecture-modularity.backend.no-raw-error-contract',)),
    ('legacy-text-5046745a-0038', ('das.governance.documentation.doc.ui-spec-appendix',)),
    ('legacy-text-5046745a-0017', ('das.governance.documentation.template.boundary-contract-schema', 'das.governance.documentation.template.boundary-contract-semantics', 'das.governance.documentation.template.boundary-contract-fixtures', 'das.governance.documentation.template.boundary-contract-checks')),
    ('legacy-text-5046745a-0031', ('das.contracts-compatibility.contract.serialized-camel-case',)),
)

REPEATED_CONTEXT_SCOPES = {
    'legacy-text-06572a96-0001': (5, 14),
    'legacy-text-06572a96-0002': (23, 27),
    'legacy-text-165796df-0001': (11, 23),
    'legacy-text-165796df-0002': (11, 23),
    'legacy-text-165796df-0003': (40, 53),
    'legacy-text-165796df-0004': (75, 101),
    'legacy-text-165796df-0005': (105, 138),
    'legacy-text-165796df-0008': (166, 184),
    'legacy-text-165796df-0010': (186, 194),
    'legacy-text-165796df-0011': (196, 207),
    'legacy-text-165796df-0012': (209, 219),
    'legacy-text-165796df-0013': (232, 241),
    'legacy-text-165796df-0026': (379, 404),
    'legacy-text-165796df-0027': (379, 404),
    'legacy-text-165796df-0042': (517, 525),
    'legacy-text-165796df-0045': (546, 582),
    'legacy-text-165796df-0047': (590, 596),
    'legacy-text-165796df-0048': (594, 603),
    'legacy-text-165796df-0049': (594, 603),
    'legacy-text-165796df-0053': (621, 629),
    'legacy-text-165796df-0054': (621, 629),
    'legacy-text-165796df-0055': (621, 634),
    'legacy-text-165796df-0056': (640, 672),
    'legacy-text-165796df-0064': (755, 767),
    'legacy-text-165796df-0065': (769, 775),
    'legacy-text-165796df-0068': (779, 788),
    'legacy-text-165796df-0070': (796, 807),
    'legacy-text-165796df-0071': (796, 807),
    'legacy-text-165796df-0072': (796, 807),
    'legacy-text-165796df-0078': (843, 847),
    'legacy-text-165796df-0079': (843, 847),
    'legacy-text-38706f1d-0002': (13, 33),
    'legacy-text-38706f1d-0003': (13, 33),
    'legacy-text-5046745a-0002': (76, 119),
    'legacy-text-5046745a-0004': (121, 123),
    'legacy-text-5046745a-0005': (176, 186),
    'legacy-text-5046745a-0009': (228, 240),
    'legacy-text-5046745a-0013': (324, 342),
    'legacy-text-5046745a-0014': (358, 392),
    'legacy-text-5046745a-0015': (358, 392),
    'legacy-text-5046745a-0017': (449, 461),
    'legacy-text-5046745a-0019': (502, 523),
    'legacy-text-5046745a-0020': (519, 523),
    'legacy-text-5046745a-0023': (596, 609),
    'legacy-text-5046745a-0024': (596, 609),
    'legacy-text-5046745a-0025': (601, 609),
    'legacy-text-5046745a-0027': (632, 641),
    'legacy-text-5046745a-0030': (675, 687),
    'legacy-text-5046745a-0031': (814, 821),
    'legacy-text-5046745a-0038': (1099, 1116),
    'legacy-text-de7276bb-0001': (30, 40),
    'legacy-text-de7276bb-0002': (30, 40),
    'legacy-text-de7276bb-0003': (70, 79),
    'legacy-text-de7276bb-0004': (98, 128),
    'legacy-text-de7276bb-0006': (103, 128),
    'legacy-text-de7276bb-0008': (131, 150),
    'legacy-text-de7276bb-0032': (463, 468),
    'legacy-text-de7276bb-0064': (1033, 1045),
    'legacy-text-de7276bb-0102': (1444, 1447),
    'legacy-text-de7276bb-0106': (1483, 1510),
    'legacy-text-de7276bb-0111': (1543, 1576),
    'legacy-text-de7276bb-0160': (1999, 2116),
    'legacy-text-de7276bb-0161': (1999, 2116),
    'legacy-text-de7276bb-0162': (1999, 2116),
    'legacy-text-f39710c0-0001': (24, 35),
}


# Original required information; no mandatory mechanism or example layout.
PLAYBOOKS += (
    ('das.governance.documentation', 'template', '', (
        ('required-traceability-workflows', 'legacy-guide-c-traceability', 246, '**Workflows**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('required-traceability-features', 'legacy-guide-c-traceability', 247, '**Features**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('required-traceability-requirements', 'legacy-guide-c-traceability', 248, '**Functional Requirements**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('required-traceability-contracts', 'legacy-guide-c-traceability', 249, '**Contracts**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('required-traceability-tests', 'legacy-guide-c-traceability', 250, '**Tests/Gates**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('required-traceability-tasks', 'legacy-guide-c-traceability', 251, '**Implementation tasks**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [242, 255], [242, 'required; keep current']),
        ('nontrivial-domain-glossary-term', 'legacy-guide-c-domain-glossary', 440, 'Term:', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'domain.non_trivial'}]}, [435, 445], [439, 'required for non-trivial domains']),
        ('nontrivial-domain-glossary-definition', 'legacy-guide-c-domain-glossary', 440, 'Definition:', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'domain.non_trivial'}]}, [435, 445], [439, 'required for non-trivial domains']),
        ('nontrivial-domain-glossary-avoided-synonyms', 'legacy-guide-c-domain-glossary', 440, 'Synonyms to avoid:', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'domain.non_trivial'}]}, [435, 445], [439, 'required for non-trivial domains']),
        ('nontrivial-domain-glossary-owner', 'legacy-guide-c-domain-glossary', 440, 'Owner:', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'domain.non_trivial'}]}, [435, 445], [439, 'required for non-trivial domains']),
        ('l1-l2-environment-matrix', 'legacy-guide-c-environment-matrix', 564, 'Environment | Purpose | Data class allowed | External deps mode | Deployment method | Rollback plan', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, [552, 569], [562, 'required for L1/L2']),
        ('l1-l2-deployment-record-artifacts', 'legacy-guide-c-deployment-record', 573, 'Build artifact(s)', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, [552, 578], [571, 'required for L1/L2']),
        ('l1-l2-deployment-record-promotion-rule', 'legacy-guide-c-deployment-record', 574, 'SAME_ARTIFACT_OR_REBUILD', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, [552, 578], [571, 'required for L1/L2']),
        ('l1-l2-deployment-record-db-migrations', 'legacy-guide-c-deployment-record', 575, 'DB migrations', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}, {'op': 'fact', 'key': 'component.database'}]}, [552, 578], [571, 'required for L1/L2']),
        ('l1-l2-deployment-record-queue-event-compatibility', 'legacy-guide-c-deployment-record', 576, 'Queue/event compatibility', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}, {'op': 'fact', 'key': 'activity.queue_event_interface'}]}, [552, 578], [571, 'required for L1/L2']),
        ('l1-l2-deployment-record-feature-flags', 'legacy-guide-c-deployment-record', 577, 'Feature flags', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}, {'op': 'fact', 'key': 'activity.feature_flags'}]}, [552, 578], [571, 'required for L1/L2']),
        ('l1-l2-deployment-record-runbooks', 'legacy-guide-c-deployment-record', 578, 'Runbooks', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.project_deployment'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}, [552, 578], [571, 'required for L1/L2']),
        ('actual-vendor-record-inventory', 'legacy-guide-c-vendor-record', 584, 'Dependency/Vendor | Purpose | Contract surface | Auth | Rate limits | Data policy | SLA/SLO | Fallback / degraded mode | Owner', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'material.external_dependencies'}]}, [580, 594], [580, 'required if any']),
        ('actual-vendor-record-test-strategy', 'legacy-guide-c-vendor-record', 590, '**Test strategy:**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'material.external_dependencies'}]}, [580, 594], [588, 'Required notes']),
        ('actual-vendor-record-cost-controls', 'legacy-guide-c-vendor-record', 591, '**Cost controls:**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'material.external_dependencies'}]}, [580, 594], [588, 'Required notes']),
        ('actual-vendor-record-operational-ownership', 'legacy-guide-c-vendor-record', 592, '**Operational ownership:**', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'material.external_dependencies'}]}, [580, 594], [588, 'Required notes']),
        ('minimum-security-declaration-enforcement-points', 'legacy-guide-c-security-declarations', 735, 'Authn/authz enforcement point(s)', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [718, 742], [733, 'Security baseline (minimum)']),
        ('minimum-security-declaration-at-rest-data-scope', 'legacy-guide-c-security-declarations', 736, 'Encryption at rest', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [718, 742], [733, 'Security baseline (minimum)']),
        ('minimum-security-declaration-secret-management', 'legacy-guide-c-security-declarations', 737, 'Secrets management', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [718, 742], [733, 'Security baseline (minimum)']),
        ('minimum-security-declaration-logging-policy', 'legacy-guide-c-security-declarations', 738, 'Logging policy', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}]}, [718, 742], [733, 'Security baseline (minimum)']),
        ('production-output-replay-record-manifest-schema', 'legacy-guide-c-production-replay-record', 775, 'Run manifest schema', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-version-fingerprints', 'legacy-guide-c-production-replay-record', 776, 'version fingerprints', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-config-profile-id', 'legacy-guide-c-production-replay-record', 776, 'config/profile id', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-budgets', 'legacy-guide-c-production-replay-record', 776, 'budgets', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-determinism-tier', 'legacy-guide-c-production-replay-record', 776, 'determinism tier', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-snapshots', 'legacy-guide-c-production-replay-record', 776, 'snapshots', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-tool-model-identifiers', 'legacy-guide-c-production-replay-record', 776, 'tool/model identifiers', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('production-output-replay-record-command', 'legacy-guide-c-production-replay-record', 777, 'Replay command(s)', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'algorithm.production_visible_outputs'}]}, [760, 777], [773, 'required for production-visible outputs']),
        ('breaking-migration-record-window', 'legacy-guide-c-breaking-migration-record', 860, 'Compatibility window', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'change.breaking_contract'}]}, [852, 862], [858, 'required when breaking changes exist']),
        ('breaking-migration-record-expand-contract', 'legacy-guide-c-breaking-migration-record', 861, 'Expand/contract steps', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'change.breaking_contract'}]}, [852, 862], [858, 'required when breaking changes exist']),
        ('breaking-migration-record-consumer-upgrade', 'legacy-guide-c-breaking-migration-record', 862, 'Consumer upgrade plan', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.project_master_doc_template'}, {'op': 'any', 'args': [{'op': 'fact', 'key': 'activity.document_activation'}, {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}, {'op': 'fact', 'key': 'change.breaking_contract'}]}, [852, 862], [858, 'required when breaking changes exist']),
    )),
    ('das.interaction.standard-ui', 'ui', '', (
        ('required-screen-controls-record', 'legacy-guide-d-controls-record', 153, 'Element | Selector (test id) | Interaction | Validation | System effect | Contracts | Notes', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.ui_control'}]}, [151, 169], [151, 'required']),
        ('citation-screen-record-contract', 'legacy-guide-d-citation-record', 174, 'Citation contract', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-rendering', 'legacy-guide-d-citation-record', 175, 'Rendering', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-marker-or-offset-rules', 'legacy-guide-d-citation-record', 176, 'if marker-based', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-integrity-behavior', 'legacy-guide-d-citation-record', 177, 'Integrity handling', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-interaction', 'legacy-guide-d-citation-record', 178, 'Interaction', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-fallback', 'legacy-guide-d-citation-record', 179, 'Fallback', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('citation-screen-record-accessible-references', 'legacy-guide-d-citation-record', 180, 'keyboard navigation + screen-reader labels', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'activity.citation_interaction_ui'}]}, [172, 180], [172, 'required if the screen renders citations']),
        ('required-accessibility-record-keyboard', 'legacy-guide-d-accessibility-record', 187, 'Keyboard navigation', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}]}, [186, 190], [186, 'required']),
        ('required-accessibility-record-aria', 'legacy-guide-d-accessibility-record', 188, 'Screen reader / ARIA', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}]}, [186, 190], [186, 'required']),
        ('required-accessibility-record-focus', 'legacy-guide-d-accessibility-record', 189, 'Focus management', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}]}, [186, 190], [186, 'required']),
        ('required-accessibility-record-contrast-motion', 'legacy-guide-d-accessibility-record', 190, 'Contrast / motion reduction', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}]}, [186, 190], [186, 'required']),
        ('multidevice-record-breakpoints', 'legacy-guide-d-multidevice-record', 193, 'Breakpoints', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'ui.multi_device'}]}, [192, 198], [192, 'required if multi-device']),
        ('multidevice-record-layout-changes', 'legacy-guide-d-multidevice-record', 194, 'Layout changes', 'MUST', {'op': 'all', 'args': [{'op': 'any', 'args': [{'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}, {'op': 'fact', 'key': 'activity.ui_spec_doc'}, {'op': 'fact', 'key': 'activity.ui_screen'}, {'op': 'fact', 'key': 'ui.multi_device'}]}, [192, 198], [192, 'required if multi-device']),
    )),
    ('das.interaction.hfvi', 'hfvi', '', (
        ('required-vis-determinism-controls', 'legacy-guide-k-conventions-inventory', 42, 'random seeds, time sources, and replay mode behavior', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}]}, [34, 48], [34, 'required']),
        ('required-vis-scene-inventory', 'legacy-guide-k-conventions-inventory', 46, 'Scene ID | Name | Engine surface | Target FPS', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}]}, [34, 48], [34, 'required']),
        ('critical-interaction-verification-cassette-id-path', 'legacy-guide-k-critical-verification', 111, 'Cassette ID (input event sequence) and storage path', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_critical_interaction'}]}, [107, 124], [107, 'required']),
        ('critical-interaction-verification-replay-command', 'legacy-guide-k-critical-verification', 112, 'Replay runner command', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_critical_interaction'}]}, [107, 124], [107, 'required']),
        ('critical-interaction-verification-baseline-id', 'legacy-guide-k-critical-verification', 113, 'Screenshot baseline IDs', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_critical_interaction'}]}, [107, 124], [107, 'required']),
        ('critical-interaction-verification-capture-time', 'legacy-guide-k-critical-verification', 113, 'capture timestamps', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_critical_interaction'}]}, [107, 124], [107, 'required']),
        ('critical-interaction-verification-assertions', 'legacy-guide-k-critical-verification', 114, 'invariants + key-frame diffs', 'MUST', {'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'activity.hfvi_critical_interaction'}]}, [107, 124], [107, 'required']),
    )),
)
PLAYBOOK_ALIASES += (('legacy-guide-d-primary-states', ('das.governance.documentation.doc.ui-spec-standard-states',)), ('legacy-guide-d-ai-states', ('das.governance.documentation.doc.ui-spec-ai-states',)), ('legacy-guide-k-conventions-inventory', ('das.interaction.hfvi.hfvi.vis-coordinates', 'das.interaction.hfvi.hfvi.vis-layers', 'das.interaction.hfvi.hfvi.vis-input')))

PLAYBOOKS += (('das.interaction.standard-ui', 'ui', '', (
    ('ui-test-map-ci-artifact-location', 'legacy-guide-g-ui-content', 935, 'where CI artifacts (screenshots/traces) are stored', 'MUST', ('activity.user_facing_ui',), (923, 935), (930, 'Minimum required content')),
)),)
PLAYBOOK_ALIASES += (
    ('legacy-guide-c-contract-index', ('das.governance.documentation.doc.master-doc-contract-inventory',)),
    ('legacy-guide-d-workflow-map', ('das.interaction.standard-ui.ui.workflow-screen-map',)),
    ('legacy-guide-g-ui-content', ('das.governance.documentation.doc.ui-spec-screen-route-ids', 'das.governance.documentation.doc.ui-spec-standard-states', 'das.governance.documentation.doc.ui-spec-traceability', 'das.interaction.standard-ui.ui.workflow-screen-map')),
)

# Repeated E1 duties keep their original IDs and conditions. Only the independent
# dual-pointer invariant needs a distinct leaf; the illustrative template is optional.
PLAYBOOKS += (('das.ai-runtime-evaluation', 'data', '', (
    ('dual-primary-pointers-same-bytes', 'legacy-guide-g-dataset-pointer', 820,
     'If both are present, they MUST refer to the same bytes/snapshot.', 'MUST',
     ('activity.dataset_manifest', 'dataset.content_hash_present', 'dataset.snapshot_id_used'),
     (780, 840), (820, 'MUST')),
)),)
PLAYBOOK_ALIASES += (('legacy-guide-g-dataset-pointer', (
    'das.contracts-compatibility.contract.dataset-content-identity',
    'das.contracts-compatibility.contract.dataset-hash-method',
    'das.ai-runtime-evaluation.data.gating-hash-preferred',
    'das.ai-runtime-evaluation.data.gating-snapshot-when-hash-infeasible',
    'das.ai-runtime-evaluation.data.optional-uri-immutable-same-bytes',
)),)

def reviewed_legacy_requirements(root, baseline):
    """Produce the exact reviewed fragment mapping, never resample the baseline."""
    units = legacy_units(root, baseline)
    source_name = 'SPECIFICATION.md'
    source_lines = {source_name: local_file(root, source_name).read_text().splitlines()}
    lines = source_lines[source_name]
    registry = load(root / 'ids/standard_ids.json')

    def reference(first, last, phrase=None):
        if not 1 <= first <= last <= len(lines):
            raise ValueError('reviewed fragment range is outside its source')
        text = '\n'.join(lines[first - 1:last])
        if phrase is not None and phrase not in text:
            raise ValueError(f'reviewed fragment absent at {source_name}:{first}-{last}: {phrase!r}')
        start = 0 if phrase is None else text.index(phrase)
        end = len(text) if phrase is None else start + len(phrase)
        return dict(path=source_name, startLine=first, endLine=last,
                    startColumn=start, endColumn=end,
                    textSha256=hashlib.sha256(text[start:end].encode()).hexdigest())

    result = []
    descriptors = [('das.core', 'profile', item) for item in PROFILE_LEAVES]
    descriptors += [('das.core', 'manifest', item) for item in MANIFEST_LEAVES]
    descriptors += [('das.architecture-modularity', 'sdmm', item) for item in SDMM_LEAVES]
    descriptors += [('das.architecture-modularity', 'topology', item) for item in TOPOLOGY_LEAVES]
    descriptors += [('das.contracts-compatibility', 'contract', item) for item in CONTRACT_LEAVES]
    descriptors += [('das.ai-runtime-evaluation', 'algorithm', item) for item in ALGORITHM_LEAVES]
    descriptors += [('das.governance.documentation', 'doc', item) for item in DOCUMENTATION_LEAVES]
    descriptors += [('das.interaction.standard-ui', 'ui', item) for item in UI_LEAVES]
    descriptors += [('das.interaction.hfvi', 'hfvi', item) for item in HFVI_LEAVES]
    descriptors += [('das.governance.verification-release', 'verify', item) for item in VERIFICATION_LEAVES]
    descriptors += [('das.architecture-modularity', 'domain', item) for item in DOMAIN_LEAVES]
    descriptors += [('das.contracts-compatibility', 'multirepo',
                     (criterion, 'legacy-text-165796df-' + suffix, line, phrase, strength, keys))
                    for criterion, suffix, line, phrase, strength, keys in MULTIREPO_LEAVES]
    descriptors += [('das.governance.verification-release', 'minimum',
                     (criterion, 'legacy-minimum-de7276bb-10-2-' + name, line, phrase, strength, keys))
                    for criterion, name, line, phrase, strength, keys in MINIMUM_LEAVES]
    descriptors += [('das.architecture-modularity', 'backend',
                     (criterion, 'legacy-text-38706f1d-' + suffix, line, phrase, strength, keys))
                    for criterion, suffix, line, phrase, strength, keys in BACKEND_LEAVES]
    descriptors += [('das.ai-runtime-evaluation', 'data',
                     (criterion, 'legacy-text-38706f1d-' + suffix, line, phrase, strength, keys))
                    for criterion, suffix, line, phrase, strength, keys in DATA_LEAVES]
    for owner, family, reviewed in (
            ('das.governance.verification-release', 'integration', INTEGRATION_LEAVES),
            ('das.governance.verification-release', 'platform', PLATFORM_LEAVES),
            ('das.security-agent', 'operational', OPERATIONAL_LEAVES),
            ('das.core', 'principles', PRINCIPLES_LEAVES)):
        descriptors += [(owner, family, (criterion, 'legacy-text-38706f1d-' + suffix, line, phrase, strength, keys))
                        for criterion, suffix, line, phrase, strength, keys in reviewed]
    playbook_scopes, playbook_force = {}, {}
    for owner, family, prefix, rows in PLAYBOOKS:
        for criterion, suffix, line, phrase, strength, keys, scope, force in rows:
            unit_id = suffix if suffix.startswith('legacy-') else prefix + suffix
            descriptors.append((owner, family, (criterion, unit_id, line, phrase, strength, keys)))
            playbook_scopes[family, criterion] = scope
            playbook_force[family, criterion] = force
    for owner, family, (criterion, suffix, line, phrase, strength, keys) in descriptors:
        unit = units[suffix if suffix.startswith('legacy-') else 'legacy-text-de7276bb-' + suffix]
        source_name = unit['source']
        if source_name not in source_lines:
            source_lines[source_name] = local_file(root, source_name).read_text().splitlines()
        lines = source_lines[source_name]
        if '\n'.join(lines[unit['startLine'] - 1:unit['endLine']]) != unit['text']:
            raise ValueError('profile carrier differs from the independent legacy body')
        first, last = unit['startLine'], unit['endLine']
        if suffix == '0010': first, last = 154, 182
        if suffix == '0012': first, last = 184, 215
        if family == 'contract': first, last = CONTRACT_SCOPES[suffix]
        if family == 'algorithm': first, last = ALGORITHM_SCOPES[suffix]
        if family == 'doc': first, last = DOCUMENTATION_SCOPES[suffix]
        if family == 'ui' and suffix in UI_SCOPES: first, last = UI_SCOPES[suffix]
        if family == 'hfvi' and suffix in HFVI_SCOPES: first, last = HFVI_SCOPES[suffix]
        if family == 'verify': first, last = VERIFICATION_SCOPES[suffix]
        if family == 'domain': first, last = DOMAIN_SCOPES[suffix]
        if family == 'multirepo': first, last = MULTIREPO_SCOPES[suffix.rsplit('-', 1)[-1]]
        if family == 'minimum': first, last = 1685, 1692
        if family == 'backend' and suffix.rsplit('-', 1)[-1] in ('0014', '0015', '0016', '0017', '0018'):
            first, last = 222, 255
        if family == 'data' and suffix.rsplit('-', 1)[-1] == '0045':
            first, last = 481, 488
        if family == 'principles':
            first, last = (13, 33) if suffix.endswith('-0001') else (35, 63)
        if (family, criterion) in playbook_scopes:
            first, last = playbook_scopes[family, criterion]
        if family == 'topology' and suffix in TOPOLOGY_SCOPES: first, last = TOPOLOGY_SCOPES[suffix]
        scope = reference(first, last)
        activation = edition_activation(keys if isinstance(keys, dict) else
                                        None if not keys else keys[0] if len(keys) == 1 else keys)
        if criterion == 'ui-spec':
            activation = dict(op='any', args=[dict(op='fact', key=key) for key in keys])
        if (family, criterion) in (('migration', 'required-playbook'), ('ddd', 'playbook-suitability')):
            activation = dict(op='any', args=[dict(op='fact', key=key) for key in keys])
        if family == 'review' or (family == 'bdd' and criterion == 'ui-stable-selectors'):
            activation = dict(op='all', args=[dict(op='any', args=[
                dict(op='fact', key=key) for key in ('surface.ui', 'surface.hfvi')]), activation])
        if family == 'doc' and criterion == 'module-master-doc':
            activation = dict(op='all', args=[activation, dict(op='any', args=[
                dict(op='fact', key=key) for key in (
                    'module.published_outside_boundary', 'module.shared_across_repos_or_teams',
                    'module.codegen_or_verify_consumed', 'module.persisted_contract_policy_or_runtime_critical')])])
        if family == 'ui' and criterion in ('token-enforcement', 'accessibility-gate'):
            profile_keys = ('profile.l1', 'profile.l2') + (('ui.kit_exists',) if criterion == 'token-enforcement' else ())
            activation = dict(op='all', args=[activation, dict(op='any', args=[
                dict(op='fact', key=key) for key in profile_keys])])
        if family == 'contract' and suffix == '0038':
            key = 'identifier.' + criterion.removeprefix('stable-').replace('-', '_') + '_surface'
            activation = edition_activation((*keys, key))
        force_line = 154 if suffix == '0010' else 184 if suffix == '0012' else 1038 if suffix == '0063' else line
        force = 'but only through' if line == 236 else strength
        if strength == 'MUST' and 'MUST NOT' in lines[force_line - 1]:
            force = 'MUST NOT'
        if family == 'contract':
            if suffix in ('0034', '0038'): force_line, force = (478 if suffix == '0034' else 506), 'MUST'
            if suffix == '0044' and criterion != 'run-immutable-config':
                force_line, force = 583, 'Minimum required fields (normative)'
            if criterion == 'external-manifest-hash': force = 'and MUST live'
            if criterion == 'citation-web-utf16': force = 'RECOMMENDED'
            if line == 977: force_line, force = 975, 'MUST'
            if suffix == '0057' and strength == 'MUST': force_line, force = 986, 'MUST'
        if family == 'topology' and suffix in TOPOLOGY_SCOPES:
            force_line = TOPOLOGY_SCOPES[suffix][0]
        if family == 'algorithm' and suffix == '0099': force_line = 1418
        if family == 'doc' and line in (1632, 1633, 1634): force_line = 1631
        if family == 'doc' and criterion in DOCUMENTATION_FORCE: force_line, force = DOCUMENTATION_FORCE[criterion]
        if family in ('ui', 'hfvi') and criterion in INTERACTION_FORCE: force_line, force = INTERACTION_FORCE[criterion]
        if family == 'verify' and criterion in VERIFICATION_FORCE: force_line, force = VERIFICATION_FORCE[criterion]
        if family == 'domain' and criterion in DOMAIN_FORCE: force_line, force = DOMAIN_FORCE[criterion]
        if family == 'multirepo' and criterion in MULTIREPO_FORCE: force_line, force = MULTIREPO_FORCE[criterion]
        if family == 'minimum': force_line, force = 1685, 'Minimum per-repo gates'
        if family == 'backend': force_line, force = BACKEND_FORCE[criterion]
        if family == 'data' and criterion in DATA_FORCE: force_line, force = DATA_FORCE[criterion]
        operational_force = {'integration': INTEGRATION_FORCE, 'platform': PLATFORM_FORCE,
                             'operational': OPERATIONAL_FORCE, 'principles': PRINCIPLES_FORCE}.get(family, {})
        if criterion in operational_force: force_line, force = operational_force[criterion]
        if (family, criterion) in playbook_force:
            force_line, force = playbook_force[family, criterion]
        contexts = [scope]
        if family == 'deployment':
            contexts.append(reference(23, 37))  # Libraries/research MAY use a reduced subset.
        if family == 'template':
            contexts.append(reference(5, 47))  # Prose/table minima, optional fields, precedence.
        if family == 'collaboration':
            contexts.append(reference(20, 36))  # Actual co-authorship; security/compliance wins.
        result.append(dict(id=owner + '.' + family + '.' + criterion, ownerModule=owner,
                           parentClause=legacy_navigation_parent(unit, registry), legacyUnitId=unit['id'],
                           strength=strength, applicability={
                               'profile': 'original-declared-profile-and-activity',
                               'manifest': 'original-standard-release-status-and-extension',
                               'sdmm': 'original-module-boundary-and-evolution-mode',
                               'topology': 'original-topology-role-and-contract-activity',
                               'contract': 'original-contract-surface-and-actual-use',
                               'algorithm': 'original-algorithm-tier-and-execution-activity',
                               'doc': 'original-documentation-event-and-governance-scope',
                               'ui': 'original-ui-surface-and-activity',
                               'hfvi': 'original-hfvi-profile-and-surface',
                               'verify': 'original-verification-cadence-and-artifact-scope',
                               'domain': 'original-domain-and-scenario-activity',
                               'multirepo': 'original-cross-repository-contract-role-and-activity',
                               'minimum': 'original-minimum-repository-role-and-doc-set',
                               'backend': 'original-backend-operation-job-and-artifact-scope',
                               'data': 'original-dataset-evaluation-use-and-sensitive-capture-scope',
                               'integration': 'original-harness-ui-shared-environment-and-ci-scope',
                               'platform': 'original-build-rollout-config-budget-and-incident-scope',
                               'operational': 'original-operational-security-privacy-and-actual-surface',
                               'principles': 'original-principles-interpretation-and-exception-event',
                               'migration': 'original-required-migration-replay-and-cutover-activity',
                               'review': 'original-ui-severity-judgement-and-actual-review-surface',
                               'ddd': 'original-domain-context-language-and-model-activity',
                               'bdd': 'original-scenario-tier-gate-and-observable-step-activity',
                               'tooling': 'original-governed-tooling-artifact-presence-and-release-activity',
                               'deployment': 'original-deployment-adoption-profile-surface-and-event',
                               'collaboration': 'original-multiparty-document-event-and-actual-profile',
                               'repo': 'original-repository-role-contract-event-and-actual-interface',
                               'template': 'original-master-template-adoption-readiness-and-project-surface'}[family],
                           criterion=criterion, conditionRefs=list(contexts), contextRefs=list(contexts),
                           strengthRef=reference(force_line, force_line, force),
                           bodyRefs=[reference(line, line, phrase)], activation=activation))
    by_id = {leaf['id']: leaf for leaf in result}
    source_name = 'SPECIFICATION.md'
    lines = source_lines[source_name]
    # Same existing requirement IDs/activation/strength; this additional original
    # context records the repeated §10.2 minima instead of inflating the denominator.
    for identities in MINIMUM_ALIASES.values():
        for identity in identities:
            by_id[identity]['contextRefs'].append(reference(1685, 1692))
    source_name = 'appendices/appendix-g-ai-product-engineering-principles-addendum.md'
    lines = source_lines[source_name]
    for suffix, identities in (*BACKEND_ALIASES, *DATA_ALIASES, *OPERATIONAL_ALIASES):
        unit = units['legacy-text-38706f1d-' + suffix]
        context = reference(unit['startLine'], unit['endLine'])
        for identity in identities:
            if context not in by_id[identity]['contextRefs']:
                by_id[identity]['contextRefs'].append(context)
    for unit_id, identities in PLAYBOOK_ALIASES:
        unit = units[unit_id]
        source_name = unit['source']
        if source_name not in source_lines:
            source_lines[source_name] = local_file(root, source_name).read_text().splitlines()
        lines = source_lines[source_name]
        first, last = unit['startLine'], unit['endLine']
        if unit_id == 'legacy-text-4d6c4f21-0003': first, last = 42, 53
        if unit_id == 'legacy-guide-4d6c4f21-checklist': first, last = 11, 38
        if unit_id == 'legacy-text-e80f2d11-0002': first, last = 56, 65
        if unit_id == 'legacy-text-d2a39e69-0005': first, last = 75, 77
        if unit_id.startswith('legacy-text-33cd7d6c-'):
            first, last = {
                '0001': (12, 37), '0002': (22, 22), '0003': (25, 25),
                '0004': (28, 28), '0005': (37, 37), '0006': (41, 61),
                '0007': (41, 61), '0008': (65, 71), '0009': (75, 75),
                '0010': (79, 84), '0011': (88, 96), '0012': (99, 107),
                '0013': (99, 107), '0014': (111, 115), '0015': (117, 124),
                '0016': (128, 133),
            }[unit_id.rsplit('-', 1)[-1]]
        if unit_id in REPEATED_CONTEXT_SCOPES:
            first, last = REPEATED_CONTEXT_SCOPES[unit_id]
        context = reference(first, last)
        for identity in identities:
            if context not in by_id[identity]['contextRefs']:
                by_id[identity]['contextRefs'].append(context)
    result.extend(manifest_rule_requirements(root, baseline))
    return result

# Reviewed sub-obligations of the adopted Z table, not all S13 prose. The row
# and its preapproval qualifier remain each leaf's normative context.
# These are applicability predicates, never checks that an obligation was met.
EDITION_LEAVES = (
    ('policy-approval', 'Z02', '当前政策', None),
    ('facts-approval', 'Z02', '适用事实', None),
    ('acceptance-scope-approval', 'Z02', '验收范围', None),
    ('unknown-risk-block', 'Z02', '未知风险事实阻断相应资格', None),
    ('subject-recheck', 'Z04', '主体', 'activity.protected_action'),
    ('resource-recheck', 'Z04', '资源', 'activity.protected_action'),
    ('action-recheck', 'Z04', '动作', 'activity.protected_action'),
    ('expiry-recheck', 'Z04', '期限', 'activity.protected_action'),
    ('budget-recheck', 'Z04', '预算', 'activity.protected_action'),
    ('generation-recheck', 'Z04', '当前授权代次', 'activity.protected_action'),
    ('delegation-ceiling', 'Z04', '委派不能扩大权限', 'activity.delegation'),
    ('report-source', 'Z08', '来源', 'activity.evidence_consumption'),
    ('report-integrity', 'Z08', '完整性', 'activity.evidence_consumption'),
    ('report-audience', 'Z08', '受众', 'activity.evidence_consumption'),
    ('report-scope', 'Z08', '范围', 'activity.evidence_consumption'),
    ('report-policy', 'Z08', '政策', 'activity.evidence_consumption'),
    ('report-candidate', 'Z08', '候选', 'activity.evidence_consumption'),
    ('report-validity', 'Z08', '有效期', 'activity.evidence_consumption'),
    ('report-trust', 'Z08', '本地自签和裸 hash 不构成可信证明', 'activity.evidence_consumption'),
    ('unidentified-denial', 'Z01', '未识别', 'activity.protected_action'),
    ('unauthorized-denial', 'Z01', '未授权', 'activity.protected_action'),
    ('expired-denial', 'Z01', '授权过期', 'activity.protected_action'),
    ('no-self-approval', 'Z01', 'Agent 不得自批', 'activity.agent_execution'),
    ('validator-write-denial', 'Z03', '当前验证器', 'activity.worker_execution'),
    ('policy-write-denial', 'Z03', '政策', 'activity.worker_execution'),
    ('protection-write-denial', 'Z03', '保护规则', 'activity.worker_execution'),
    ('key-write-denial', 'Z03', '签发密钥', 'activity.worker_execution'),
    ('evidence-store-write-denial', 'Z03', '可信证据库', 'activity.worker_execution'),
    ('proven-isolation', 'Z05', '已证明可用的隔离环境', 'activity.untrusted_execution'),
    ('host-secret-denial', 'Z05', '宿主秘密', 'activity.untrusted_execution'),
    ('control-socket-denial', 'Z05', '控制 socket', 'activity.untrusted_execution'),
    ('unapproved-network-denial', 'Z05', '未批准网络', 'activity.untrusted_execution'),
    ('verification-candidate-binding', 'Z06', ('验证', '不可变候选'), 'activity.verification'),
    ('verification-code-binding', 'Z06', ('验证', '代码'), 'activity.verification'),
    ('verification-document-binding', 'Z06', ('验证', '文档'), 'activity.verification'),
    ('verification-config-binding', 'Z06', ('验证', '配置'), 'activity.verification'),
    ('verification-dependency-binding', 'Z06', ('验证', '依赖'), 'activity.verification'),
    ('verification-external-binding', 'Z06', ('验证', '必要外部工件'), ('activity.verification', 'material.external_required')),
    ('integration-candidate-binding', 'Z06', ('集成', '不可变候选'), 'activity.integration'),
    ('integration-code-binding', 'Z06', ('集成', '代码'), 'activity.integration'),
    ('integration-document-binding', 'Z06', ('集成', '文档'), 'activity.integration'),
    ('integration-config-binding', 'Z06', ('集成', '配置'), 'activity.integration'),
    ('integration-dependency-binding', 'Z06', ('集成', '依赖'), 'activity.integration'),
    ('integration-external-binding', 'Z06', ('集成', '必要外部工件'), ('activity.integration', 'material.external_required')),
    ('independent-verification', 'Z07', '验证独立于候选编写者', 'activity.verification'),
    ('agent-tests-not-sole-acceptance', 'Z07', 'Agent 编写的测试不得单独定义验收成功', ('activity.verification', 'risk.agent_authored_tests')),
    ('target-baseline-check', 'Z09', '集成检查目标基线', 'activity.integration'),
    ('competition-reverification', 'Z09', ('竞争', '重新验证'), ('activity.integration', 'change.integration_competition')),
    ('rebase-reverification', 'Z09', ('重基', '重新验证'), ('activity.integration', 'change.integration_rebase')),
    ('merge-result-reverification', 'Z09', ('merge 结果改变', '重新验证'), ('activity.integration', 'change.integration_merge_result')),
    ('applicable-completion-evidence', 'Z10', '完成状态依赖适用证据', 'activity.completion'),
    ('done-no-conformance', 'Z10', ('`DONE`', '不得产生合规完成'), 'activity.completion'),
    ('force-no-conformance', 'Z10', ('`--force`', '不得产生合规完成'), 'activity.completion'),
    ('waiver-no-conformance', 'Z10', ('waiver', '不得产生合规完成'), 'activity.completion'),
    ('audit-delete-denial', 'Z11', '删除', 'activity.worker_execution'),
    ('audit-replace-denial', 'Z11', '替换', 'activity.worker_execution'),
    ('audit-rollback-denial', 'Z11', '回滚', 'activity.worker_execution'),
    ('log-secret-exclusion', 'Z11', ('秘密不进入', '普通日志'), 'activity.log_emission'),
    ('artifact-secret-exclusion', 'Z11', ('秘密不进入', '工件'), 'activity.artifact_output'),
    ('tool-provenance', 'Z12', ('工具', '有受控来源'), None),
    ('plugin-provenance', 'Z12', ('插件', '有受控来源'), None),
    ('rule-provenance', 'Z12', ('规则', '有受控来源'), None),
    ('cache-provenance', 'Z12', ('缓存', '有受控来源'), None),
    ('adapter-provenance', 'Z12', ('适配器', '有受控来源'), None),
    ('missing-capability-stop', 'Z12', ('缺失能力', '安全停止'), None),
    ('revocation-stop', 'Z12', ('撤销', '安全停止'), None),
    ('incident-stop', 'Z12', ('事故', '安全停止'), None),
    ('downgrade-stop', 'Z12', ('降级尝试', '安全停止'), None),
)
EDITION_CONTROL_RESULTS = {
    'Z01': '未识别、未授权、授权过期的主体没有受保护操作权限；Agent 不得自批',
    'Z02': '当前政策、适用事实和验收范围有独立批准；未知风险事实阻断相应资格',
    'Z03': 'Worker 不能修改当前验证器、政策、保护规则、签发密钥或可信证据库',
    'Z04': '每次受保护动作都重新校验主体、资源、动作、期限、预算和当前授权代次；委派不能扩大权限',
    'Z05': '不可信代码在已证明可用的隔离环境运行；不可访问宿主秘密、控制 socket 或未批准网络',
    'Z06': '验证与集成绑定不可变候选，以及代码、文档、配置、依赖和必要外部工件的完整身份',
    'Z07': '验证独立于候选编写者；Agent 编写的测试不得单独定义验收成功',
    'Z08': '报告需验证来源、完整性、受众、范围、政策、候选与有效期；本地自签和裸 hash 不构成可信证明',
    'Z09': '集成检查目标基线；竞争、重基、merge 结果改变时重新验证',
    'Z10': '完成状态依赖适用证据；Agent 的 `DONE`、`--force` 或 waiver 不得产生合规完成',
    'Z11': '审计不可被 Worker 删除、替换或回滚；秘密不进入普通日志和工件',
    'Z12': '工具、插件、规则、缓存和适配器有受控来源；缺失能力、撤销、事故和降级尝试安全停止',
}
EDITION_PREAPPROVAL = ('上述控制不要求每次动作均由人类点击批准。低风险、可逆、范围确定的动作可以由有权主体预先批准政策，'
                     '再由独立控制面逐次执行。策略提升、保护规则修改和高风险动作必须走相应独立批准路径。')
# Independently compared with all twelve frozen Z rows, including enforcement
# and required evidence cells. Regenerated source references cannot waive them.
EDITION_TABLE_SHA256 = '27f0f20ffe1790a7cb80bc4d7223c1fc28c068ef654cdfd8a3a3c5484e106b83'

# Reviewed explicit storage obligations in S13 prose. Whole paragraph groups
# retain exceptions, failure semantics and unexpanded obligations. These are
# path/operation predicates, never permission, durability or success flags.
# In particular the connection proof is SHOULD, not a table-derived MUST.
# (criterion, line, body, force phrase, strength, activity facts, context span)
EDITION_STORAGE_LEAVES = (
    ('durable-confirmation', 352, '须达到已声明故障模型下的持久化边界', '须', 'MUST', 'activity.authoritative_write', (352, 356)),
    ('nonmissing-dedup-key', 356, '不得使用缺失或 `NULL` 值参与去重', '不得', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('conflict-fingerprint', 356, '比较同一不可变请求指纹', '必须', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('conflict-original-or-deny', 356, '返回原状态或拒绝', '必须', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('connection-constraint-proof', 358, '每条承担权威写入的连接实际启用其依赖的约束', '应', 'SHOULD', 'activity.authoritative_write', (356, 358)),
    ('failed-write-no-success', 358, '约束错误、更新零行、事务提交失败或未知不得映射为成功', '不得', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('failed-transaction-state', 358, '明确核对事务状态', '须', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('failed-transaction-rollback', 358, '回滚未提交权威变更', '须', 'MUST', 'activity.authoritative_write', (356, 358)),
    ('transaction-before-read', 360, '数据库内用于决定写入的集合/状态读取之前实际开始', '必须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('transaction-budget', 360, '关联的预算', '必须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('transaction-parent-child', 360, '父子状态', '必须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('transaction-unique-key', 360, '唯一键', '必须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('transaction-audit-intent', 360, '审计意图提交', '必须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('serializable-shared-budget', 360, '共享预算剩余额度', '须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('serializable-task-set', 360, '父 Change 的完整必需任务集合', '须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('serializable-no-pending', 360, '“没有未决动作”', '须', 'MUST', 'activity.authoritative_write', (360, 362)),
    ('backup-consistent-boundary', 370, '对应经过确认的一致状态边界', '必须', 'MUST', 'activity.state_backup', (368, 370)),
    ('backup-transaction-store', 370, '覆盖实际事务存储', '必须', 'MUST', 'activity.state_backup', (368, 370)),
    ('backup-recovery-material', 370, '必要恢复材料', '必须', 'MUST', 'activity.state_backup', (368, 370)),
    ('artifact-complete-bytes', 372, '完整字节校验', '须完成', 'MUST', ('activity.artifact_registration', 'storage.system_crash_covered'), (372, 374)),
    ('artifact-storage-durability', 372, '存储持久化', '须完成', 'MUST', ('activity.artifact_registration', 'storage.system_crash_covered'), (372, 374)),
    ('artifact-protected-reference', 372, '引用关系的受保护提交', '须完成', 'MUST', ('activity.artifact_registration', 'storage.system_crash_covered'), (372, 374)),
    ('artifact-directory-sync', 372, '同步所需目录', '具体协议须', 'MUST', ('activity.artifact_registration', 'storage.system_crash_covered', 'storage.linux_filesystem'), (372, 374)),
    ('artifact-sync-results', 372, '核对所有返回结果', '具体协议须', 'MUST', ('activity.artifact_registration', 'storage.system_crash_covered', 'storage.linux_filesystem'), (372, 374)),
    ('recovery-no-different-bytes', 374, '重建不同字节', '不得', 'MUST', 'activity.artifact_recovery', (372, 374)),
    ('recovery-no-erase-failure', 374, '删除失败', '不得', 'MUST', 'activity.artifact_recovery', (372, 374)),
    ('recovery-no-reset-action-budget', 374, '清空动作/预算', '不得', 'MUST', 'activity.artifact_recovery', (372, 374)),
    ('qualification-durable-evidence', 376, '缺少必需持久证据时不得签发依赖它的资格', '不得', 'MUST', 'activity.qualification_issuance', (376, 376)),
)
EDITION_STORAGE_SHA256 = '08028bb73722cc1df7bae72cedbcfb84e0568c720f77bb00245e02ed0b00f888'

# Explicit S13 audit/read/disclosure carriers. Whole contexts preserve the
# restricted-read scope, public-data exception, in-flight disclosure limits and
# independent bounded stop. Failure/permission claims do not define the scope.
EDITION_CONTROL_LEAVES = (
    ('audit-checkpoint', 338, '锚定到 Worker 不可回滚的检查点', '必须', 'MUST', 'activity.audit_recording', (338, 340)),
    ('no-backfilled-success', 340, '倒填成功', '不得', 'MUST', 'activity.authoritative_write', (338, 340)),
    ('no-automatic-replay', 340, '自动重放', '不得', 'MUST', 'activity.authoritative_write', (338, 340)),
    ('no-absence-as-nonexecution', 340, '假定“没记录就没发生”', '不得', 'MUST', 'activity.authoritative_write', (338, 340)),
    ('bounded-stop-without-record-channel', 344, '执行有界停止', '仍须', 'MUST', 'activity.protected_action', (342, 344)),
    ('read-resource-domain-binding', 346, '资源域', '须绑定', 'MUST', 'activity.protected_read', (346, 350)),
    ('read-caller-binding', 346, '调用主体', '须绑定', 'MUST', 'activity.protected_read', (346, 350)),
    ('read-purpose-binding', 346, '用途', '须绑定', 'MUST', 'activity.protected_read', (346, 350)),
    ('read-audience-binding', 346, '输出受众', '须绑定', 'MUST', 'activity.protected_read', (346, 350)),
    ('capability-no-public-artifact', 346, '公开', '不得', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-no-transfer-artifact', 346, '转交', '不得', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-no-log-artifact', 346, '写入日志', '不得', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-current-identity', 346, '当前调用身份', '仍须满足', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-audience', 346, '受众', '仍须满足', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-resource-scope', 346, '资源范围', '仍须满足', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('capability-revocation', 346, '撤销要求', '仍须满足', 'MUST', 'activity.capability_url_handling', (346, 350)),
    ('redaction-no-enumerable-hash-claim', 346, '可枚举的裸 hash', '审计脱敏不得', 'MUST', 'activity.log_emission', (346, 350)),
    ('redaction-no-plaintext-only-claim', 346, '仅去除原文', '审计脱敏不得', 'MUST', 'activity.log_emission', (346, 350)),
    ('disclosure-bounded-unit', 348, '有界发送单元', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-byte-record-limit', 348, '字节/记录', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-unit-time-limit', 348, '时间上限', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-continuation-checkpoint', 348, '续读检查点', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-revocation-effect', 348, '撤销生效', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-revocation-confirmation', 348, '确认语义', '须定义', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-inflight-volume-limit', 348, '可能剩余的在途数据量', '合同须限制', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('disclosure-inflight-time-limit', 348, '时长', '合同须限制', 'MUST', ('activity.protected_read', 'activity.continuous_disclosure'), (346, 350)),
    ('revocation-no-confirmation-with-old-path', 350, '报告该范围撤销完成', '不得', 'MUST', 'activity.protected_read', (346, 350)),
)
EDITION_CONTROL_SHA256 = '1f069bbc4f032d845868acb0671ba27de182a1523b7ac249b20a780d800cccc4'


EDITION_COMPLETION_GROUPS = (
    dict(owner="das.governance.documentation", section=14, scope=[379,418],
         sha256="a38ddb828750cd272db1e094bd05977e59d30ac03e7236a00273ff7baf0b23ff", rows=(
        ["identity-protected-namespace",381,"受保护命名空间解析",381,"不能","MUST",["activity.protected_task_governance"],[381,383]],
        ["identity-full-exchange",381,"正式交换必须携带完整 taskKey",381,"必须","MUST",["activity.protected_task_governance","activity.task_binding_exchange"],[381,383]],
        ["identity-no-reassignment",383,"转交另一对象",383,"不得","MUST",["activity.protected_task_governance"],[381,383]],
        ["identity-local-history",383,"同一 Change 内已使用的局部 taskId 保留其历史指向",383,"不得","MUST",["activity.protected_task_governance"],[381,383]],
        ["identity-new-object-mapping",383,"不同的受保护身份",383,"须","MUST",["activity.protected_task_governance","activity.task_object_creation"],[381,383]],
        ["identity-versioned-lossless-mapping",383,"不在旧闭合 schema 中暗加字段",383,"不在","MUST",["activity.protected_task_governance","activity.task_identity_mapping"],[381,383]],
        ["identity-retirement-history",383,"退役记录与映射历史保存在受保护状态",383,"不得","MUST",["activity.protected_task_governance","activity.task_identity_retirement"],[381,383]],
        ["identity-recovery-continuity",383,"证明其身份及历史连续性",383,"须","MUST",["activity.protected_task_governance","activity.task_recovery"],[381,383]],
        ["identity-recovery-no-completion-or-budget-reset",383,"不能借重建空记录继承旧 Completion 或重新发放额度",383,"不能借","MUST",["activity.protected_task_governance","activity.task_recovery"],[381,383]],
        ["material-change-new-task-lineage",385,"实质变更目标/范围/合同/责任/验收义务时新建 Task 并保留 lineage",385,"新建 Task","MUST",["activity.protected_task_governance","change.task_material"],[385,387]],
        ["retry-attempt",385,"失败重试增 attempt",385,"增 attempt","MUST",["activity.protected_task_governance","activity.task_retry"],[385,387]],
        ["rework-cycle",385,"同一义务完成后返工增 cycle",385,"增 cycle","MUST",["activity.protected_task_governance","activity.task_rework"],[385,387]],
        ["rework-parent-state",387,"closed/cancelled/superseded 后通过关联新 Change 承接",387,"通过关联新 Change","MUST",["activity.protected_task_governance","activity.task_rework"],[385,400]],
        ["rescind-narrow-proof",387,"无部署、无迁移、无外部依赖影响",387,"仅适用于","MUST",["activity.protected_task_governance","activity.change_closure_rescind"],[387,400]],
        ["rescind-consumption-check",387,"核对该关闭是否已被后续资格或动作消费",387,"核对","MUST",["activity.protected_task_governance","activity.change_closure_rescind"],[387,400]],
        ["rescind-independent-approval-history-generation",387,"独立有权主体批准，追加 `closureRescinded`、保留原关闭事件并更新状态代次",387,"由独立有权主体批准","MUST",["activity.protected_task_governance","activity.change_closure_rescind"],[387,400]],
        ["rescind-no-obligation-outcome-rewrite",387,"不得改写原义务、原结果或把取消/替代包装成行政误关闭",387,"不得","MUST",["activity.protected_task_governance","activity.change_closure_rescind"],[387,400]],
        ["parent-protected-authority",389,"当前状态、受批准任务集合、任务集合摘要、关闭义务与状态代次属于受保护权威",389,"不能","MUST",["activity.protected_task_governance"],[389,400]],
        ["closing-frozen-task-set",389,"固定当前任务集合及关闭条件",389,"禁止","MUST",["activity.protected_task_governance","activity.change_closing_prepare"],[389,400]],
        ["closing-no-new-delete-or-cycle",389,"禁止并发新增、删除任务或开启返工周期",389,"禁止","MUST",["activity.protected_task_governance","activity.change_closing_settlement"],[389,400]],
        ["close-atomic-complete-set-current-cycle-and-evidence",389,"同一受保护事务内核对状态代次、完整任务集合、各必需任务当前 cycle 的有效完成、Change 级验收及不存在未决副作用",389,"须","MUST",["activity.protected_task_governance","activity.change_success_close"],[389,400]],
        ["parent-completion-rework-close-serialization",389,"任务完成、返工和关闭使用同一串行化边界",389,"使用同一串行化边界","MUST",["activity.protected_task_governance"],[389,400]],
        ["terminal-not-success-or-scope-shrink",389,"不能删掉失败任务来关闭原义务",389,"不能删掉","MUST",["activity.protected_task_governance","activity.change_terminal_transition"],[389,400]],
        ["state-current-action-boundary",392,"必须拒绝或另行处理",392,"必须","MUST",["activity.protected_task_governance","activity.governed_task_action"],[392,400]],
        ["history-no-terminal-new-completion",400,"不能在终态后创造新的合规完成",400,"不能","MUST",["activity.protected_task_governance","activity.task_history_reconciliation"],[392,400]],
        ["terminal-stop-unsent-reconcile-inflight",400,"终态转换停止尚未发出的普通业务动作",400,"停止","MUST",["activity.protected_task_governance","activity.change_terminal_transition"],[392,400]],
        ["completion-current-evidence",402,"当前候选的验证、必要责任确认、适用集成及迁移/回滚证据",402,"需满足","MUST",["activity.protected_task_governance","activity.completion"],[400,404]],
        ["revision-independent-equivalence-rebinding",404,"明确的受权等价/重绑定记录",404,"必须经独立判定","MUST",["activity.protected_task_governance","change.task_revision"],[402,404]],
        ["attempt-no-budget-or-history-reset",404,"attempt 变化不允许重置预算或丢弃失败历史",404,"不允许","MUST",["activity.protected_task_governance","activity.task_retry"],[402,404]],
        ["obligation-approved-digest-not-status-or-log",404,"目标、范围、约束、验收与责任",404,"不作为义务作者源","MUST",["activity.protected_task_governance","activity.task_binding_exchange"],[402,404]],
        ["candidate-actual-files-not-projection-exclusion",404,"覆盖实际纳管文件",404,"仍须","MUST",["activity.protected_task_governance","activity.candidate_binding"],[402,404]],
        ["completion-unique-task-cycle",404,"每个 `(taskKey, cycle)` 至多有一次合规完成提交",404,"至多有一次","MUST",["activity.protected_task_governance","activity.completion"],[402,404]],
        ["completion-no-identity-change-bypass",404,"revision、attempt、显示 ID、授权代次或请求 ID 的变化不能绕过该唯一性",404,"不能绕过","MUST",["activity.protected_task_governance","activity.completion"],[402,404]],
        ["integration-source-and-actual-candidate-distinct",406,"源候选与实际集成候选分别记录",406,"分别记录","MUST",["activity.protected_task_governance","activity.integration"],[406,408]],
        ["integration-current-content-target-verification",406,"匹配该内容和目标基线的新验证",406,"须","MUST",["activity.protected_task_governance","activity.integration"],[406,408]],
        ["integration-receipt-binding",406,"绑定原候选、实际集成候选、验证引用、目标及提交前后版本",406,"绑定","MUST",["activity.protected_task_governance","activity.integration"],[406,408]],
        ["integration-durable-action-cas-recovery",406,"持久化动作 ID、CAS 和可恢复记录",406,"不能声称","MUST",["activity.protected_task_governance","activity.integration"],[406,408]],
        ["integration-no-unimplemented-cross-system-atomicity",406,"不能声称存在未实现的跨系统原子事务",406,"不能声称","MUST",["activity.protected_task_governance","activity.integration"],[406,408]],
        ["completion-outside-candidate",408,"Completion 置于候选之外的受保护事件存储",408,"置于候选之外","MUST",["activity.protected_task_governance","activity.completion"],[406,408]],
        ["projection-changes-candidate-no-old-digest",408,"不能继续使用原候选摘要",408,"不能","MUST",["activity.protected_task_governance","activity.committed_completion_projection"],[406,408]],
        ["projection-separate-governed-change",408,"单独受治理的确定性元数据变更验证与集成",408,"作为单独受治理","MUST",["activity.protected_task_governance","activity.committed_completion_projection"],[406,408]],
        ["projection-no-future-completion-or-loop",408,"不把未来 Completion 纳入其所证明候选的摘要，也不以回写投影重新触发同一任务的完成循环",408,"不把未来 Completion","MUST",["activity.protected_task_governance","activity.committed_completion_projection"],[406,408]],
        ["completion-historical-not-permanent-current-content",408,"不证明分支之后永远保持该内容",408,"不证明","MUST",["activity.protected_task_governance","activity.completion_consumption"],[406,410]],
        ["expiry-no-reopen-new-cycle-or-second-completion",410,"不自动重开 Task、增加 cycle 或产生第二份 Completion",410,"不自动","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["revalidation-current-plan-verification-authorization-budget",410,"当前批准的验收计划、验证专用授权及预算",410,"当前批准","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["revalidation-no-worker-business-authority",410,"不恢复终态 Task 的 Worker 业务权限",410,"不恢复","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["revalidation-no-mutation-side-effects-or-integration",410,"不得修改候选、触发任务业务副作用或重做集成",410,"不得","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["revalidation-append-new-evidence-decision-original-completion",410,"追加新的 Verification Evidence 与动作专属 Decision，并引用原 Completion",410,"追加新的","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["revalidation-failure-history-retained-current-denied",410,"保留历史完成，拒绝依赖现时资格的后续动作",410,"拒绝","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation","result.revalidation_failed_or_insufficient"],[410,414]],
        ["revalidation-test-space-bounded-authority",412,"验证服务本次有界授权和额度",412,"不恢复","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,414]],
        ["current-close-release-adoption-target-and-change-acceptance",414,"满足其当前计划规定的目标状态与 Change 级验收",414,"须","MUST",["activity.protected_task_governance","activity.change_close_release_or_adoption"],[410,418]],
        ["revalidation-no-cancel-success-or-past-authority",414,"不能通过重新验证恢复为成功",414,"不能","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,418]],
        ["revalidation-no-retroactive-control-proof",414,"不追授过去缺失的授权、隔离或执行证明",414,"不追授","MUST",["activity.protected_task_governance","activity.task_evidence_revalidation"],[410,418]],
        ["close-collection-predicates-not-per-child-cas",416,"每个子行独立 CAS 成功不代表“全部任务已经完成”这个决定仍有效",416,"不代表","MUST",["activity.protected_task_governance","activity.change_success_close"],[416,418]],
        ["transaction-retry-current-parent-set-authority",416,"不得跨越新的父状态、任务集合代次或授权条件",416,"不得","MUST",["activity.protected_task_governance","activity.task_state_transaction_retry"],[416,418]],
        ["transaction-retry-single-current-record",416,"只形成一个当前有效完成/关闭记录",416,"只形成一个","MUST",["activity.protected_task_governance","activity.task_state_transaction_retry"],[416,418]],
        ["completion-current-identity-set-generation-evidence-atomic",418,"完整身份、当前任务集合、状态代次和可信证据",418,"共享原子边界","MUST",["activity.protected_task_governance","activity.completion_or_change_close"],[416,418]],
        ["legacy-state-no-new-completion",418,"旧状态保持读取与历史展示，不直接映射为新完成",418,"不直接映射","MUST",["activity.protected_task_governance","activity.legacy_task_state_handling"],[416,418]],
        ["authority-state-versioned-binding-contract",418,"明确版本的绑定/事件合同承载",418,"明确版本","MUST",["activity.protected_task_governance","activity.task_binding_exchange"],[416,418]],
        ["completion-applicable-integration-evidence",402,"适用集成",402,"需满足","MUST",["activity.protected_task_governance","activity.completion","task.integration_applicable"],[400,404]],
        ["completion-applicable-migration-rollback-evidence",402,"迁移/回滚证据",402,"需满足","MUST",["activity.protected_task_governance","activity.completion","task.migration_rollback_applicable"],[400,404]],
        ["completion-applicable-responsibility",402,"必要责任确认",402,"需满足","MUST",["activity.protected_task_governance","activity.completion","task.responsibility_confirmation_applicable"],[400,404]],
    )),
    dict(owner="das.security-agent", section=20, scope=[549,592],
         sha256="1cc4fc02626320b50f2582719a200850ef3fc3b493cf7f865a9e73c8660d9579", rows=(
        ["activation-schema-semantics-positive-negative-errors-interop",551,"schema、语义说明、合法/非法 fixtures、错误契约与 producer/consumer 互操作测试",551,"必须","MUST",["activity.formal_exchange_object_activation"],[549,567]],
        ["contract-single-governed-author",551,"每份 schema/签名合同只有一个受治理作者源",551,"只有一个","MUST",["activity.formal_exchange_contract"],[549,567]],
        ["release-locked-contract-version-digest-mapping",551,"发布闭包固定其版本、摘要和规范映射",551,"固定","MUST",["activity.formal_contract_release"],[549,567]],
        ["consumer-same-contract",551,"各消费者使用同一合同",551,"使用同一合同","MUST",["activity.formal_exchange_contract"],[549,567]],
        ["tool-not-normative-authority",551,"不得将某个可执行工具或未经锁定的上游分支变成规范权威",551,"不得","MUST",["activity.formal_exchange_contract"],[549,567]],
        ["adapter-approved-lossless-exact-binding",551,"明确批准的无损适配",551,"不能绕过","MUST",["activity.formal_contract_representation_adapter"],[549,567]],
        ["wire-separate-identity-schema-purpose-scope",567,"区分 `contract identity`、schema 身份、消息用途与范围",567,"必须","MUST",["activity.formal_security_object"],[555,567]],
        ["wire-required-optional-defaults-types-limits-algorithms-signature-errors",567,"required/optional、缺省值、时间/代次类型、消息大小、摘要算法、签名覆盖范围和错误行为",567,"必须","MUST",["activity.formal_exchange_contract"],[555,567]],
        ["wire-no-lossy-numeric-conversion",567,"编号、时间和预算不能依赖可能丢精度的隐式数字转换",567,"不能","MUST",["activity.formal_security_object"],[555,567]],
        ["wire-new-identity-when-old-not-lossless",567,"无法无损承载的部分用明确的新契约身份，保持旧 schema 的读写承诺",567,"保持旧 schema 的读写承诺","MUST",["activity.formal_contract_representation_adapter"],[555,567]],
        ["decision-report-outcome-separate",571,"原 verify report 仍使用原有 outcome",571,"仍使用原有 outcome","MUST",["activity.protected_decision"],[569,575]],
        ["decision-machine-reasons",571,"授权缺失、上下文不匹配、验收未满足、必需证据缺失、前提已变化、能力不支持、信任状态不可用、外部结果未知",571,"不能默认允许","MUST",["activity.protected_decision"],[569,575]],
        ["decision-unknown-error-missing-deny",571,"任何未知、错误或缺失不能默认允许",571,"不能","MUST",["activity.protected_decision"],[569,575]],
        ["decision-no-cross-stage-permission",573,"仅允许提交候选的 Decision 不能用于 integrate、complete、close 或 release",573,"不能","MUST",["activity.protected_decision_consumption"],[569,575]],
        ["resource-current-authentication-and-independent-grant",573,"重新认证当前调用者，取得独立有效授权",573,"重新认证","MUST",["activity.protected_action"],[569,575]],
        ["resource-current-decision-context-evidence-recheck",573,"用途、受众、taskKey、候选、规范化资源/目标版本/代次、父子状态、政策、有效授权依赖及必需证据有效性",573,"复核","MUST",["activity.protected_action"],[569,575]],
        ["resource-changed-context-redecide-or-protected-equivalence",573,"重新裁定或经受保护等价规则确认",573,"不足以继续执行","MUST",["activity.protected_action","change.decision_context"],[569,575]],
        ["minimum-control-actual-enforcement-not-signature",575,"实际拒绝/隔离/不可篡改结果必须由强制机制和实测证据支持",575,"必须","MUST",["activity.minimum_control_qualification"],[569,575]],
        ["qualitative-review-bound-scope-candidate-duty-decision-window",575,"scope、候选、义务、决策和有效期",575,"必须","MUST",["activity.qualitative_acceptance_review"],[569,575]],
        ["exception-original-failure-separate-limited-not-full-pass",575,"原失败和例外分别保存",575,"不能标为无条件完整通过","MUST",["activity.engineering_acceptance_exception"],[569,575]],
        ["completion-ordered-current-control-to-projection",580,"当前控制面 → 批准 Task / 事实 / 验收",555,"最低绑定","MUST",["activity.protected_completion_chain"],[577,592]],
        ["no-integration-preapproved-branch",592,"不需要集成的任务使用预先批准的完成分支",592,"预先批准","MUST",["activity.protected_completion_chain","task.integration_not_applicable"],[577,592]],
        ["post-integration-completion-recovery-actual-history-only",592,"根据动作 ID 与可信目标历史恢复",592,"只补记真实完成所需事实","MUST",["activity.integration_completion_recovery"],[577,592]],
        ["post-integration-no-reintegration-or-false-completion",592,"不再次执行集成",592,"不再次执行","MUST",["activity.integration_completion_recovery"],[577,592]],
        ["target-aba-protected-generation-not-reusable-value",592,"受保护目标代次或等效不可回滚事务序列检测",592,"不能仅比较","MUST",["activity.integration_or_completion"],[577,592]],
        ["bundle-minimum-binding",557,"scope、来源、批准、标准/规则/事实/政策摘要、目标、unknown/conflict",555,"最低绑定","MUST",["activity.bundle_resolution_exchange"],[555,567]],
        ["bundle-authorized-producer",557,"事实由有权控制面批准；Bundle 由受保护解析器计算",555,"有权产生者","MUST",["activity.bundle_resolution_exchange"],[555,567]],
        ["bundle-no-role-substitution",557,"不能让扫描结果自我批准或让派生列表成为作者源",555,"不得承担的职责","MUST",["activity.bundle_resolution_exchange"],[555,567]],
        ["task-minimum-binding",558,"不重新分配的受保护 Change/Task 身份、状态代次/任务集合、完整 taskKey、义务摘要、revision、cycle、目标与 required-for-action、批准主体",555,"最低绑定","MUST",["activity.task_binding_exchange"],[555,567]],
        ["task-authorized-producer",558,"受保护治理批准入口",555,"有权产生者","MUST",["activity.task_binding_exchange"],[555,567]],
        ["task-no-role-substitution",558,"不能仅凭可编辑任务列表产生当前权威，不能把取消或替代当成功",555,"不得承担的职责","MUST",["activity.task_binding_exchange"],[555,567]],
        ["decision-minimum-binding",559,"指定主体/受众/scope/action、taskKey、候选/目标前提、计划/证据引用、事实/政策/信任状态摘要、有效区间、限定结论及原因",555,"最低绑定","MUST",["activity.protected_decision"],[555,567]],
        ["decision-authorized-producer",559,"受信 Cadence 裁定链",555,"有权产生者","MUST",["activity.protected_decision"],[555,567]],
        ["decision-no-role-substitution",559,"不授予业务权限，不证明动作已经发生，不允许跨阶段复用为许可",555,"不得承担的职责","MUST",["activity.protected_decision"],[555,567]],
        ["candidate-minimum-binding",560,"内容闭包摘要、Task 引用、源版本、外部材料与构建来源",555,"最低绑定","MUST",["activity.candidate_binding_exchange"],[555,567]],
        ["candidate-authorized-producer",560,"受保护快照执行器",555,"有权产生者","MUST",["activity.candidate_binding_exchange"],[555,567]],
        ["candidate-no-role-substitution",560,"不证明测试通过，不包括未来验证/完成记录",555,"不得承担的职责","MUST",["activity.candidate_binding_exchange"],[555,567]],
        ["authorization-minimum-binding",561,"发起/当前行为主体、受众、动作、规范化资源及创建实例、taskKey、businessActionId、参数摘要、有效授权依赖、有效期、policy、authority epoch、授权代次及共享额度",555,"最低绑定","MUST",["activity.action_authorization_exchange"],[555,567]],
        ["authorization-authorized-producer",561,"当前受权政策/批准服务",555,"有权产生者","MUST",["activity.action_authorization_exchange"],[555,567]],
        ["authorization-no-role-substitution",561,"不兼任执行结果；不授权合同以外动作",555,"不得承担的职责","MUST",["activity.action_authorization_exchange"],[555,567]],
        ["verification-minimum-binding",562,"精确候选、已批准验收/计划槽位、实际 run/attempt 与原始来源、分母/聚合、制品、工具、环境、结果与时效",555,"最低绑定","MUST",["activity.verification_evidence_exchange"],[555,567]],
        ["verification-authorized-producer",562,"受信采集/裁定/签发链",555,"有权产生者","MUST",["activity.verification_evidence_exchange"],[555,567]],
        ["verification-no-role-substitution",562,"不直接授予资源写入权限，不把候选原始输出当可信断言",555,"不得承担的职责","MUST",["activity.verification_evidence_exchange"],[555,567]],
        ["action-receipt-minimum-binding",563,"稳定业务动作 ID、含原发起主体的不可变请求指纹、实际执行主体/授权引用、最终资源前提、受理/发送/提交阶段、执行结果、可信顺序与副作用状态",555,"最低绑定","MUST",["activity.action_receipt_exchange"],[555,567]],
        ["action-receipt-authorized-producer",563,"实际受保护资源执行点",555,"有权产生者","MUST",["activity.action_receipt_exchange"],[555,567]],
        ["action-receipt-no-role-substitution",563,"不作为新动作授权，不以超时代表未执行",555,"不得承担的职责","MUST",["activity.action_receipt_exchange"],[555,567]],
        ["integration-receipt-minimum-binding",564,"源候选、实际集成候选、后者的验证、目标、提交前后版本、动作 ID",555,"最低绑定","MUST",["activity.integration_receipt_exchange"],[555,567]],
        ["integration-receipt-authorized-producer",564,"受保护集成入口",555,"有权产生者","MUST",["activity.integration_receipt_exchange"],[555,567]],
        ["integration-receipt-no-role-substitution",564,"不把旧分支名或准备状态当已集成",555,"不得承担的职责","MUST",["activity.integration_receipt_exchange"],[555,567]],
        ["completion-minimum-binding",565,"taskKey/revision/cycle、父 Change 及状态前提、适用验证/集成/责任证据、当前政策、完成唯一键",555,"最低绑定","MUST",["activity.completion_record_exchange"],[555,567]],
        ["completion-authorized-producer",565,"受保护完成入口",555,"有权产生者","MUST",["activity.completion_record_exchange"],[555,567]],
        ["completion-no-role-substitution",565,"不修改原始 outcome，不作为无限期现时许可",555,"不得承担的职责","MUST",["activity.completion_record_exchange"],[555,567]],
    )),
)


EDITION_COMPLETION_GROUPS += (
    dict(owner="das.security-agent", section=13, scope=[338,376],
         sha256="7c09403031bb144d03484113d84591fdff6f656997afcd8f1ac5910460f9498c", rows=(
        ["audit-event-binding",338,"主体、动作、对象、决策、授权/政策身份、候选和可信时间/顺序",338,"至少绑定","MUST",["activity.audit_recording"],[338,340]],
        ["audit-redaction-and-access-control",338,"秘密脱敏与访问控制同时执行",338,"同时执行","MUST",["activity.audit_recording"],[338,340]],
        ["audit-no-ordinary-waiver-or-emergency-qualification",338,"零信任底线不允许普通 waiver",338,"不允许","MUST",["activity.minimum_control_qualification"],[338,340]],
        ["audit-durable-intent-before-effect-and-result",340,"先持久化意图/预留，再执行副作用，再追加结果",340,"先持久化","MUST",["activity.authoritative_write"],[338,344]],
        ["audit-side-effect-result-unknown-freeze-reconcile",340,"保留 `unknown`/待核对状态并冻结相关后续动作",340,"不得倒填成功","MUST",["activity.authoritative_write"],[338,344]],
        ["audit-emergency-not-passed",340,"不能把非合规动作投影为 v1.5 已通过",340,"不能","MUST",["activity.emergency_recovery"],[338,344]],
        ["audit-historical-not-unlimited-current-permission",340,"历史证据不能被无限期当作现时许可",340,"不能","MUST",["activity.evidence_consumption"],[338,344]],
        ["audit-service-failure-stops-normal-write",342,"审计或授权服务不可用时，正常受保护写入停止",342,"停止","MUST",["activity.authoritative_write"],[342,344]],
        ["audit-independent-preapproved-local-stop",342,"不以先成功写入故障中的主审计库或取得新的业务授权为前提",342,"不以","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-stop-bounded-scope-not-business-recovery",342,"不包含扩大权限、解除保护、业务补偿、重新发送外部请求或宣布完成",342,"不包含","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-stop-not-worker-emergency-switch",342,"不能由 Worker 通过通用应急参数取得",342,"不能","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-stop-only-approved-deployment-actions",342,"仅允许部署预先核准的安全动作",342,"仅允许","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-stop-independent-record-or-truthful-gap",344,"恢复后追加所能证实的故障区间与证据缺口",344,"不倒填不存在的原记录或成功结论","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-local-stop-not-global-revocation",344,"对不可达入口和已发出的远端动作保留未确认状态",344,"才能宣布","MUST",["activity.protected_local_stop"],[342,344]],
        ["audit-reopen-current-authority-audit-pending-deployment",344,"重新核对当前权威、审计能力、未决动作及部署条件",344,"必须","MUST",["activity.business_recovery_reopen"],[342,344]],
        ["audit-protected-read-authentication",346,"受保护读取也要鉴权",346,"要鉴权","MUST",["activity.protected_read"],[346,350]],
        ["audit-diagnostic-no-other-project-or-sealed-data",346,"诊断模式不能借只读名义获取其他项目或密封评分域的数据",346,"不能","MUST",["activity.protected_diagnostic_read"],[346,350]],
        ["audit-private-digest-domain-safe-developer-reference",346,"完整性摘要保存在获准域，面向开发侧的索引使用不暴露受限值的引用",346,"不得靠","MUST",["activity.restricted_artifact_index"],[346,350]],
        ["audit-disclosure-current-identity-purpose-policy-budget",348,"每个新发送单元在实际释放前核对当前身份、用途、披露政策和适用额度",348,"须定义","MUST",["activity.protected_read","activity.continuous_disclosure"],[346,350]],
        ["audit-cached-data-not-release-authority",348,"不自动取得随后向开发域释放的权利",348,"不自动取得","MUST",["activity.protected_read","activity.continuous_disclosure"],[346,350]],
        ["audit-expiry-revocation-unavailable-stop-release",348,"停止新单元和仍可中止的释放",348,"停止","MUST",["activity.protected_read","activity.continuous_disclosure"],[346,350]],
        ["audit-inflight-disclosure-truth-no-recall-claim",348,"不可撤回发出的单元作为在途披露如实核对",348,"不声称撤销能收回","MUST",["activity.protected_read","activity.continuous_disclosure"],[346,350]],
        ["audit-revocation-session-range-capability-coverage",350,"相关持续会话、重连/Range 请求及此前发出的带权地址",350,"不得","MUST",["activity.protected_read","activity.disclosure_revocation_confirmation"],[346,350]],
        ["audit-revocation-not-only-new-address-stop",350,"仅停止签发新地址或等待客户端自行停读不满足该确认条件",350,"不满足","MUST",["activity.protected_read","activity.disclosure_revocation_confirmation"],[346,350]],
        ["audit-external-address-insufficient-boundary-closed",350,"无法满足所需边界时不向该受众开放该路径",350,"不向","MUST",["activity.external_capability_delivery"],[346,350]],
        ["audit-protected-storage-fault-model-configuration",352,"实际存储、journal/WAL、同步设置、文件系统与恢复前提列入受保护部署配置",352,"须达到","MUST",["activity.authoritative_write"],[352,354]],
        ["audit-distinct-process-system-crash-proof",352,"主机/系统崩溃与仅进程崩溃分开测试",352,"分开测试","MUST",["activity.storage_durability_verification"],[352,354]],
        ["audit-undurable-no-effects-budget-reuse-or-completion",354,"不发送新的正常副作用、不确认预算可再次使用，也不签发已持久完成",354,"不发送","MUST",["activity.authoritative_write"],[352,354]],
        ["audit-unknown-commit-original-action-key",354,"按同一业务动作键核对，保留 unknown",354,"保留 unknown","MUST",["activity.authoritative_write"],[352,354]],
        ["audit-restore-no-authority-dedup-budget-history-rollback",354,"不能回退授权、去重、预算或审计历史",354,"不能","MUST",["activity.state_recovery"],[352,358]],
        ["audit-completion-close-atomic-relations-generation-evidence-unique",356,"同时核对父子关系、当前代次、必需证据和唯一完成约束",356,"不得","MUST",["activity.completion_or_change_close"],[356,362]],
        ["audit-no-candidate-association-or-schema-only-proof",356,"不能依赖候选提供的关联 ID 或仅验证 schema",356,"不能","MUST",["activity.completion_or_change_close"],[356,362]],
        ["audit-no-replace-history-or-dedup",356,"已有历史与去重记录不可被通用“存在则替换”写入覆盖",356,"不可","MUST",["activity.authoritative_write"],[356,358]],
        ["audit-authorization-update-allowed-fields-append-history",356,"授权更新只修改合同允许的字段，另追加历史",356,"只修改","MUST",["activity.authorization_update"],[356,358]],
        ["audit-sqlite-actual-nonnull-foreign-key-conflicts",358,"验证非空键、连接级外键和冲突处理",358,"必须","MUST",["activity.authoritative_write","storage.sqlite_reference"],[356,362]],
        ["audit-retry-confirmed-rollback-current-full-logic",362,"确认事务回滚后",362,"不能只重放失败 UPDATE","MUST",["activity.authoritative_transaction_retry"],[360,362]],
        ["audit-retry-stable-key-total-attempt-time-current-permission",362,"重试保留稳定业务动作键，受累计尝试/时间和当前权限限制",362,"受累计尝试/时间和当前权限限制","MUST",["activity.authoritative_transaction_retry"],[360,362]],
        ["audit-uncommitted-values-not-external-effects",362,"未提交事务中的读到值或暂定成功不得触发外部动作",362,"不得","MUST",["activity.authoritative_write"],[360,362]],
        ["audit-external-send-durable-intent-independent-point",362,"外部发送通过已持久化意图的独立执行点",362,"通过已持久化意图","MUST",["activity.external_side_effect"],[360,362]],
        ["audit-no-long-network-or-effects-in-retryable-transaction",362,"副作用和长时间网络请求不放入可自动重试的数据库事务体",362,"不放入","MUST",["activity.authoritative_transaction_retry"],[360,362]],
        ["audit-collected-candidate-content-still-untrusted",364,"内容仍属所声明来源的数据",364,"不能","MUST",["activity.untrusted_output_collection"],[364,366]],
        ["audit-closed-trusted-fields-no-text-command-injection",364,"不能把候选多行文本拼进事件头、批准字段、CI 命令或可执行模板",364,"不能","MUST",["activity.untrusted_output_collection"],[364,366]],
        ["audit-context-specific-safe-display-distinct-raw-data",364,"明确区分结构化事件、受限原始字节和展示副本",364,"不能","MUST",["activity.untrusted_output_display"],[364,366]],
        ["audit-raw-provenance-secrecy-retention",366,"来源、保密及保留范围进入受限工件库",366,"不能","MUST",["activity.untrusted_output_collection"],[364,366]],
        ["audit-derived-view-original-rule-and-new-digest",366,"记录原引用、转换规则及必要的新摘要",366,"不能","MUST",["activity.untrusted_output_display"],[364,366]],
        ["audit-display-no-original-signature-or-trusted-event-rewrite",366,"不能改写原签名所绑定内容",366,"不能","MUST",["activity.untrusted_output_display"],[364,366]],
        ["audit-actual-loaded-engine-driver-config-source-fix-proof",368,"实际加载的引擎/驱动/编译配置、制品来源、已知完整性缺陷适用性及修复依据",368,"不能","MUST",["activity.authoritative_write"],[368,370]],
        ["audit-host-cli-version-not-loaded-library-proof",368,"不能用宿主命令行版本替代进程实际库",368,"不能","MUST",["activity.authoritative_write"],[368,370]],
        ["audit-unfixed-or-unknown-integrity-defect-stops-writes",368,"停止相应受保护写路径",368,"停止","MUST",["activity.authoritative_write"],[368,370]],
        ["audit-stress-nonreproduction-not-fix-proof",368,"一次压力测试未复现不能替代修复证据",368,"不能","MUST",["activity.storage_integrity_verification"],[368,370]],
        ["audit-sqlite-protected-mode-loaded-source-fix-record",368,"模式、实际加载制品、修复条件和回补证据在受保护部署记录中登记",368,"不能","MUST",["activity.authoritative_write","storage.sqlite_reference"],[368,370]],
        ["audit-backup-not-copy-delete-log-or-open-proof",370,"普通文件逐个复制、无条件删除恢复日志或只检查数据库能打开",370,"不足以证明","MUST",["activity.state_backup"],[368,370]],
        ["audit-multiple-physical-stores-no-unproved-atomicity",370,"只在机制明确保证时才声明共同原子性",370,"只在","MUST",["activity.multi_store_authoritative_write"],[368,374]],
        ["audit-restore-checkpoint-external-effects-current-revocation",370,"独立检查点、已发生外部动作及当前撤销核对",370,"不能重置预算或开放重复执行","MUST",["activity.state_recovery"],[368,370]],
        ["audit-restore-unknown-gap-no-budget-or-execution-reset",370,"历史缺口和未决动作保持待核对",370,"不能重置预算或开放重复执行","MUST",["activity.state_recovery"],[368,370]],
        ["audit-artifact-reference-and-storage-separate-confirmation",372,"数据库事务与其文件/对象存储提交分别确认",372,"分别确认","MUST",["activity.artifact_registration"],[372,374]],
        ["audit-orphan-register-original-identity-and-operation",374,"孤立工件只在核对身份及原操作后恢复登记",374,"只在","MUST",["activity.artifact_recovery"],[372,374]],
        ["audit-missing-artifact-stops-qualification-incident-record",374,"必需工件缺失/不完整时，停止其相关资格并如实记录事故",374,"停止","MUST",["activity.artifact_recovery"],[372,374]],
        ["audit-unknown-storage-not-file-visibility-as-success-or-absence",374,"不能因临时文件/最终文件可见就假定整个操作已成功或未发生",374,"不能","MUST",["activity.artifact_registration","activity.artifact_recovery"],[372,374]],
        ["audit-actual-unwritable-audit-control-unavailable-fault-test",376,"实际注入主审计不可写和控制面不可达故障",376,"不得","MUST",["activity.minimum_control_qualification"],[372,376]],
        ["audit-fault-every-storage-reference-recovery-handoff",376,"对存储确认、引用提交及恢复的每个交接点注入故障",376,"不得","MUST",["activity.storage_durability_verification"],[372,376]],
    )),
)




# Reviewed edition semantics; these mappings preserve the normative author and
# its complete exceptions. The independent 1.4 baseline remains unchanged.
EDITION_COMPLETION_GROUPS += (
    dict(owner=EDITION_OWNERS[1], section=1, scope=[41, 47],
         sha256="67d39434aae65e4d97dfcbf83c70a8db322e073bd182b6fbd0ad29e9df138b03", rows=(
        ["standard-module-distinct-sdmm", 41, "Standard Module / 规范模块", 41, "保留", "MUST", None, [41, 47]],
        ["core-adoption-profiles-minimum-controls", 41, "Core 保留采用规则、既有 profile、兼容原则、零信任最低原则及统一 verify 入口", 41, "Core 保留采用规则、既有 profile、兼容原则、零信任最低原则及统一 verify 入口", "MUST", None, [41, 47]],
        ["module-responsibilities", 41, "规范模块按职责分为", 41, "规范模块按职责分为", "MUST", None, [41, 47]],
        ["single-security-author", 41, "安全控制正文只在 security-agent 有一处权威定义", 41, "安全控制正文只在 security-agent 有一处权威定义", "MUST", None, [41, 47]],
        ["guides-informative", 43, "Guide 明确 informative", 43, "Guide 明确 informative", "MUST", None, [41, 47]],
        ["template-effect-explicit", 43, "Template 必须逐一声明哪些部分为规范性要求、哪些为示例", 43, "必须", "MUST", None, [41, 47]],
        ["draft-no-force-waiver", 43, "不自动撤销规范效力", 43, "不自动撤销规范效力", "MUST", None, [41, 47]],
        ["no-must-relocation-loss", 43, "不得把现有有效 MUST 移入 informative 文件后使之失效", 43, "不得", "MUST", None, [41, 47]],
        ["stable-module-ids", 45, "其他模块使用 `das.` 前缀的稳定 ID", 45, "其他模块使用 `das.` 前缀的稳定 ID", "MUST", None, [41, 47]],
        ["single-body-catalog-view-authors", 45, "语义正文、目录映射和生成视图分别只有一个作者源", 45, "语义正文、目录映射和生成视图分别只有一个作者源", "MUST", None, [41, 47]],
        ["unique-leaf-owner", 45, "其可执行叶子要求各有唯一模块归属", 45, "其可执行叶子要求各有唯一模块归属", "MUST", None, [41, 47]],
        ["cross-domain-parent-mapping", 45, "跨域旧章节通过父子映射连接", 45, "跨域旧章节通过父子映射连接", "MUST", None, [41, 47]],
        ["no-duplicate-or-reinterpreted-must", 45, "禁止为满足目录树形状而复制 MUST 或改变旧条款含义", 45, "禁止", "MUST", None, [41, 47]],
        ["effect-owner-dependency-selfcheck", 47, "每个规范来源的效力标记、条款唯一归属和依赖闭包", 47, "每个规范来源的效力标记、条款唯一归属和依赖闭包", "MUST", None, [41, 47]],
        ["independent-force-comparison", 47, "建立提取前后规范文本/规则强度对照", 47, "建立提取前后规范文本/规则强度对照", "MUST", None, [41, 47]],
        ["extraction-no-applicability-force-change", 47, "纯提取提交不得改变适用性或 MUST/SHOULD", 47, "不得", "MUST", None, [41, 47]],
        ["missing-conflict-effect-gap-blocks-release", 47, "发现缺失条款、冲突归属或规范效力空档时阻断发布", 47, "发现缺失条款、冲突归属或规范效力空档时阻断发布", "MUST", None, [41, 47]],
    )),
    dict(owner=EDITION_OWNERS[2], section=2, scope=[52, 72],
         sha256="7425663c4452487a6f589dd6d17050ff3caa7446252cbc32cd5385fcfbf76e3b", rows=(
        ["preserve-cost-and-interaction-profiles", 52, "保留 `L0/L1/L2` 和三个 interaction profile 的既有含义", 52, "保留 `L0/L1/L2` 和三个 interaction profile 的既有含义", "MUST", None, [52, 72]],
        ["record-actual-capabilities-and-risks", 52, "实际交互 surface、产品能力、Agent 可达动作、数据和运行风险", 52, "实际交互 surface、产品能力、Agent 可达动作、数据和运行风险", "MUST", None, [52, 72]],
        ["separate-repo-and-component-roles", 52, "不与产品组件角色合并", 52, "不与产品组件角色合并", "MUST", None, [52, 72]],
        ["facts-scope", 54, "scope", 54, "必须", "MUST", None, [52, 72]],
        ["facts-source", 54, "来源", 54, "必须", "MUST", None, [52, 72]],
        ["facts-confirmation-owner", 54, "确认责任", 54, "必须", "MUST", None, [52, 72]],
        ["facts-candidate-deployment", 54, "候选/部署基线", 54, "必须", "MUST", None, [52, 72]],
        ["facts-policy", 54, "生效政策", 54, "必须", "MUST", None, [52, 72]],
        ["independent-fact-approval-before-evaluation", 54, "独立控制面批准后才进入当前求值", 54, "独立控制面批准后才进入当前求值", "MUST", None, [52, 72]],
        ["derived-modules-no-obligation-reduction", 54, "不能通过编辑结果文件减少义务", 54, "不能", "MUST", None, [52, 72]],
        ["fixed-source-rule-closure-applicability-profile-floor-order", 56, "确认事实来源 → 执行受限声明式规则 → 求依赖闭包 → 计算条款级适用性 → 依据既有 profile 决定相应工程 gate 强度 → 检查不可减免的零信任底线", 56, "确认事实来源 → 执行受限声明式规则 → 求依赖闭包 → 计算条款级适用性 → 依据既有 profile 决定相应工程 gate 强度 → 检查不可减免的零信任底线", "MUST", None, [52, 72]],
        ["hfvi-applicable-ui-base", 56, "HFVI 包含适用的 Standard UI 基础要求", 56, "HFVI 包含适用的 Standard UI 基础要求", "MUST", None, [52, 72]],
        ["mixed-actual-surfaces", 56, "混合项目还须按实际 surface 纳入 headless/UI 要求", 56, "须", "MUST", None, [52, 72]],
        ["three-value-not-unknown", 58, "`not unknown = unknown`", 58, "`not unknown = unknown`", "MUST", None, [52, 72]],
        ["exists-not-safe-negation", 58, "不能把存在的 unknown 变成安全否定事实", 58, "不能", "MUST", None, [52, 72]],
        ["unknown-missing-conflict-deny-affected", 58, "安全相关 unknown、来源缺失或事实冲突阻断对应资格", 58, "安全相关 unknown、来源缺失或事实冲突阻断对应资格", "MUST", None, [52, 72]],
        ["risk-rules-additive-monotone", 58, "风险控制规则采用可证明单调的添加式规则", 58, "风险控制规则采用可证明单调的添加式规则", "MUST", None, [52, 72]],
        ["display-negation-no-security-floor-reduction", 58, "不得借此降低安全最低控制", 58, "不得", "MUST", None, [52, 72]],
        ["missing-facts-stay-unknown", 60, "缺失值先转换为 `unknown`", 60, "缺失值先转换为 `unknown`", "MUST", None, [52, 72]],
        ["conflicting-provenance-retained", 60, "冲突保留各来源并阻断受影响裁定", 60, "冲突保留各来源并阻断受影响裁定", "MUST", None, [52, 72]],
        ["no-last-write-conflict-folding", 60, "不能按字段覆盖顺序取最后值", 60, "不能", "MUST", None, [52, 72]],
        ["strong-kleene-and-or", 60, "安全规则中的 AND/OR 采用强 Kleene 三值逻辑", 60, "安全规则中的 AND/OR 采用强 Kleene 三值逻辑", "MUST", None, [52, 72]],
        ["retirement-new-approved-facts-and-evidence", 60, "真实能力退役可经独立批准形成新事实快照，并重算受影响证据", 60, "真实能力退役可经独立批准形成新事实快照，并重算受影响证据", "MUST", None, [52, 72]],
        ["no-scan-retirement-substitution", 60, "不能伪装成普通扫描结果覆盖", 60, "不能", "MUST", None, [52, 72]],
        ["unresolved-mandatory-no-full-conformance", 60, "受影响的强制义务未决时不得宣称完整符合", 60, "不得", "MUST", None, [52, 72]],
        ["engine-errors-fail-not-false-or-unknown", 62, "解析器异常、类型错误、超限、插件失效和没有输出属于求值失败", 62, "解析器异常、类型错误、超限、插件失效和没有输出属于求值失败", "MUST", None, [52, 72]],
        ["affected-engine-decision-denies", 62, "受影响决定失败关闭", 62, "受影响决定失败关闭", "MUST", None, [52, 72]],
        ["engine-adapter-explicit-states-errors-output-fixtures", 62, "适配器须显式保留事实状态、错误类别和规则输出，独立通过 DAS fixtures", 62, "须", "MUST", ["engine.native_policy_adapter"], [52, 72]],
        ["successful-false-no-other-rule-inference", 69, "自动推断其他规则也不适用", 69, "自动推断其他规则也不适用", "MUST", None, [52, 72]],
        ["layered-policy-intersection", 70, "按 S10 取各层约束的交集", 70, "按 S10 取各层约束的交集", "MUST", None, [52, 72]],
        ["independent-bundle-recomputation-and-identities", 72, "合格验证实现重算 Bundle，并核对事实、政策、规则及解析器身份", 72, "合格验证实现重算 Bundle，并核对事实、政策、规则及解析器身份", "MUST", None, [52, 72]],
        ["rules-no-project-code-or-network", 72, "模块规则不得执行项目代码或联网", 72, "不得", "MUST", None, [52, 72]],
        ["combination-unknown-conflict-and-monotonic-fixtures", 72, "冻结组合 fixtures、unknown/冲突 fixtures、风险增加不能减少控制的性质测试", 72, "冻结组合 fixtures、unknown/冲突 fixtures、风险增加不能减少控制的性质测试", "MUST", None, [52, 72]],
        ["actual-declared-conflict-no-full-conformance", 72, "发现实际能力与声明冲突时不能输出完整符合结论", 72, "不能", "MUST", None, [52, 72]],
    )),
    dict(owner=EDITION_OWNERS[3], section=3, scope=[77, 87],
         sha256="0344ca873a50dc7388793b2abbd28c77cab40cf7c50762577502bcfff5f4007f", rows=(
        ["module-catalog-governed-release-closure", 77, "通过现有 `normativeArtifactRefs` 引用，并进入 `requiredArtifacts` 和发布快照", 77, "通过现有 `normativeArtifactRefs` 引用，并进入 `requiredArtifacts` 和发布快照", "MUST", None, [77, 87]],
        ["catalog-author-generated-index-and-view", 77, "派生索引和完整视图不得独立编辑", 77, "不得", "MUST", None, [77, 87]],
        ["module-id", 79, "稳定 ID", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-title", 79, "title", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-source", 79, "规范来源", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-effect", 79, "效力", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-status", 79, "status", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-activation", 79, "activation", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-dependencies", 79, "dependsOn", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-clauses", 79, "clauseIds", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-artifacts", 79, "requiredArtifactRefs", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-gates", 79, "gate 映射", 79, "至少具有", "MUST", None, [77, 87]],
        ["module-change-history", 79, "引入/修改记录", 79, "至少具有", "MUST", None, [77, 87]],
        ["modules-share-standard-edition", 79, "所有模块共享标准版次，不独立发版", 79, "所有模块共享标准版次，不独立发版", "MUST", None, [77, 87]],
        ["stable-old-parent-and-new-leaf-identities", 79, "登记稳定 requirement ID，并保留父 clause 关系", 79, "登记稳定 requirement ID，并保留父 clause 关系", "MUST", None, [77, 87]],
        ["no-renumbered-old-meaning", 79, "不能用重新编号覆盖旧语义", 79, "不能", "MUST", None, [77, 87]],
        ["enhanced-index-explicit-identity-negotiation", 81, "明确 schema 身份和能力协商", 81, "使用", "MUST", ["activity.enhanced_index_export"], [77, 87]],
        ["shared-artifact-references-legal", 81, "不应禁止合法共享引用", 81, "不应", "SHOULD", None, [77, 87]],
        ["independent-text-and-mapping-denominators", 83, "规范文本清单与独立维护的映射基线检验", 83, "规范文本清单与独立维护的映射基线检验", "MUST", None, [77, 87]],
        ["no-coedited-index-as-completeness-proof", 83, "不能让“目录”和“检查分母”同时从已被删减的索引生成后互相证明完整", 83, "不能", "MUST", None, [77, 87]],
        ["locked-schema-parser-and-reference-closure", 83, "`$ref` 只能解析到已锁定工件，禁止校验过程中隐式联网获取新规则", 83, "只能", "MUST", None, [77, 87]],
        ["conditional-rule-stable-identity-author-direction-edition", 85, "按稳定 requirement 身份映射，登记作者位置、生成方向和适用版次", 85, "按稳定 requirement 身份映射，登记作者位置、生成方向和适用版次", "MUST", None, [77, 87]],
        ["unmigrated-original-remains-author", 85, "尚未迁出的规则继续以原位置为作者源", 85, "尚未迁出的规则继续以原位置为作者源", "MUST", None, [77, 87]],
        ["migrated-original-generated-compatibility-view", 85, "迁出后原位置仅保留由同一作者源生成的兼容视图", 85, "迁出后原位置仅保留由同一作者源生成的兼容视图", "MUST", None, [77, 87]],
        ["no-dual-condition-author-or-loading-precedence", 85, "两处不得独立维护同一规范条件", 85, "不得", "MUST", None, [77, 87]],
        ["merge-all-obligations-conflict-missing-mapping-deny", 85, "解析器合成全部适用义务", 85, "解析器合成全部适用义务", "MUST", None, [77, 87]],
        ["rule-change-not-view-generation", 85, "不能借视图生成改变", 85, "不能", "MUST", None, [77, 87]],
        ["id-dag-effect-path-digest-and-schema-gates", 87, "verifier 检查 ID、引用存在、DAG、效力和发布闭包", 87, "verifier 检查 ID、引用存在、DAG、效力和发布闭包", "MUST", None, [77, 87]],
        ["actual-old-consumer-release-compatibility", 87, "旧消费者与新发布包仍需真实兼容测试", 87, "旧消费者与新发布包仍需真实兼容测试", "MUST", None, [77, 87]],
    )),
    dict(owner=EDITION_OWNERS[4], section=4, scope=[92, 104],
         sha256="a1930f23e67edd5a56152e9e5b2d764366db1b74ca0bef316ec9822b0a0ebb3c", rows=(
        ["explicit-definition-classification", 92, "每个定义显式标注三类之一", 92, "每个定义显式标注三类之一", "MUST", ["activity.contract_definition"], [92, 104]],
        ["preserve-exact-reference-contract-meaning", 92, "保留 Reference Profile 的“精确机器表示”含义", 92, "保留 Reference Profile 的“精确机器表示”含义", "MUST", ["activity.contract_definition"], [92, 104]],
        ["semantic-model-old-meaning-lossless-mapping", 96, "保留已有规范语义及无损映射", 96, "保留已有规范语义及无损映射", "MUST", ["activity.contract_definition"], [92, 104]],
        ["citation-minimum-sanitization-and-degradation", 97, "保留最低映射、消毒、引用一致性和降级语义", 97, "保留最低映射、消毒、引用一致性和降级语义", "MUST", ["activity.contract_definition"], [92, 104]],
        ["legacy-stream-distinct-exact-delta-contract", 98, "保留 legacy 语义和映射", 98, "保留 legacy 语义和映射", "MUST", ["activity.contract_definition"], [92, 104]],
        ["published-machine-schemas-stay-normative", 99, "不降级成可任意改字段的模型", 99, "不降级成可任意改字段的模型", "MUST", ["activity.contract_definition"], [92, 104]],
        ["new-authority-evidence-completion-exact-contract-fixtures", 100, "精确 Reference Contract，含失败行为及兼容 fixtures", 100, "精确 Reference Contract，含失败行为及兼容 fixtures", "MUST", ["activity.contract_definition"], [92, 104]],
        ["classification-no-required-semantics-removal", 102, "文档分类不得撤销已有 required 字段语义", 102, "不得", "MUST", ["activity.contract_definition"], [92, 104]],
        ["examples-no-forced-field-layout", 102, "不据此强制示例字段布局", 102, "不据此强制示例字段布局", "MUST", ["activity.contract_definition"], [92, 104]],
        ["mapping-retains-errors-defaults-enums-identity-security", 102, "映射必须同时保存错误、缺省、枚举、身份和安全限制的含义", 102, "必须", "MUST", ["activity.contract_definition"], [92, 104]],
        ["json-convertibility-not-lossless-proof", 102, "仅能将对象转成 JSON 不构成无损证明", 102, "仅能将对象转成 JSON 不构成无损证明", "MUST", ["activity.contract_definition"], [92, 104]],
        ["classification-schema-fixture-roundtrip-release-gate", 104, "Round-trip 测试覆盖最低信息义务", 104, "Round-trip 测试覆盖最低信息义务", "MUST", ["activity.contract_definition"], [92, 104]],
        ["lost-normative-field-mapping-fails", 104, "规范性字段被映射丢失时失败", 104, "规范性字段被映射丢失时失败", "MUST", ["activity.contract_definition"], [92, 104]],
    )),
)



# Reviewed edition semantics; these mappings preserve the normative author and
# its complete exceptions. The independent 1.4 baseline remains unchanged.
EDITION_COMPLETION_GROUPS += (
    dict(owner=EDITION_OWNERS[5], section=5, scope=[109, 121],
         sha256="1a0ee26d2e384449e2877693fd11986d21d7d5a2d38163c9b973c9cf5cbcfe34", rows=(
        ["distinct-rfc6901-contract-result-root-and-allowed-paths", 109, "path 使用 RFC 6901 的 JSON string representation，根为最终物化的 PipelineResult", 109, "path 使用 RFC 6901 的 JSON string representation，根为最终物化的 PipelineResult", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["root-pointer-no-whole-object-authority", 109, "RFC 允许的 root pointer 不自动取得替换整个对象的权限", 109, "RFC 允许的 root pointer 不自动取得替换整个对象的权限", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["append-existing-string", 111, "`append` 仅向已存在字符串末尾追加 `text`", 111, "仅", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["replace-existing-authorized-string", 111, "`replace` 仅替换已存在且获准的字符串", 111, "仅", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["invalid-missing-type-path-operation-reject", 111, "不存在路径、类型不符、越权路径、无效转义或不支持操作均拒绝", 111, "不存在路径、类型不符、越权路径、无效转义或不支持操作均拒绝", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["no-implicit-create-array-append-or-patch", 111, "不暗含 JSON Patch/merge 语义", 111, "不暗含 JSON Patch/merge 语义", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["stream-lane-sequence-content-dedup", 113, "按 `(streamId, laneId, seq)` 去重", 113, "按 `(streamId, laneId, seq)` 去重", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["same-position-different-content-conflict", 113, "不同内容视为冲突", 113, "不同内容视为冲突", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["locked-transport-gap-cursor-reconnect-bounds", 113, "正式交换必须选择已锁定的 transport 契约", 113, "必须", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["reference-zero-contiguous-sequences", 113, "至少交付一个逐 lane 从 0 起连续递增的参考 transport", 113, "至少交付一个逐 lane 从 0 起连续递增的参考 transport", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["gap-prevents-completion-and-limit-explicit-stop", 113, "缺口未补齐前不能确认最终完成", 113, "不能", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["initial-final-lane-watermarks-and-materialized-digest", 113, "初始化状态和结束时的 lane 水位、受控物化内容摘要必须可核对", 113, "必须", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["end-frame-not-complete-history-proof", 113, "结束帧不能单独证明此前增量完整", 113, "不能", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["shared-target-total-order", 113, "共享目标需契约声明全序规则", 113, "需", "MUST", ["activity.text_delta_transport", "stream.shared_target"], [109, 121]],
        ["terminal-no-new-delta-legal-replay", 113, "终结后拒绝新增量", 113, "终结后拒绝新增量", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["decoded-tokens-and-own-json-node-authority", 115, "路径授权以解码后的 token 序列及实际 JSON 节点为准", 115, "路径授权以解码后的 token 序列及实际 JSON 节点为准", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["no-prototype-or-accessor-traversal", 115, "不遍历语言原型或执行属性访问器", 115, "不遍历语言原型或执行属性访问器", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["array-index-object-number-distinction", 115, "数组下的 `01` 非法，对象中名为 `01` 的成员可合法存在", 115, "数组下的 `01` 非法，对象中名为 `01` 的成员可合法存在", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["no-implicit-fragment-percent-extra-decode", 115, "不自动解码 URI fragment、百分号或额外转义", 115, "不自动解码 URI fragment、百分号或额外转义", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["independent-pointer-attack-fixtures", 115, "独立 fixtures 包含 `/outputX`、`~01`、对象数字 key 与数组索引的区分", 115, "独立 fixtures 包含 `/outputX`、`~01`、对象数字 key 与数组索引的区分", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["approved-whole-stream-resource-and-time-plan", 117, "同时限定单帧、累计接收字节/帧数、物化字符串大小、lane数、乱序缓冲、总运行时长和重连/重传额度", 117, "同时限定单帧、累计接收字节/帧数、物化字符串大小、lane数、乱序缓冲、总运行时长和重连/重传额度", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["replay-metered-no-history-budget-reset", 117, "重连、游标清空或重建客户端不能重置同一受治理操作的历史与额度", 117, "不能", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["atomic-materialization-and-watermarks", 117, "检查通过后原子更新物化状态及水位", 117, "检查通过后原子更新物化状态及水位", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["over-limit-preserves-consistency-no-truncated-success", 117, "不截断后签发成功", 117, "不截断后签发成功", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["sse-native-framing-no-eof-event", 119, "EOF处尚未终结的事件不分发", 119, "不分发", "MUST", ["activity.text_delta_transport", "transport.sse"], [109, 121]],
        ["sse-last-event-id-not-authority-or-completion", 119, "`Last-Event-ID`仅是传输恢复线索", 119, "仅", "MUST", ["activity.text_delta_transport", "transport.sse"], [109, 121]],
        ["sse-reconnect-current-authority-budget", 119, "自动重连受同一操作预算和当前授权约束", 119, "受", "MUST", ["activity.text_delta_transport", "transport.sse"], [109, 121]],
        ["sse-close-not-business-completion", 119, "业务最终完成仍依赖完整结束证据", 119, "依赖", "MUST", ["activity.text_delta_transport", "transport.sse"], [109, 121]],
        ["new-old-identities-no-silent-path-reinterpretation", 121, "禁止在同一旧 schemaVersion 下静默重解释 path", 121, "禁止", "MUST", ["activity.text_delta_transport"], [109, 121]],
        ["legacy-dot-path-unambiguous-only", 121, "含有点号的 key 等歧义必须失败或使用项目明确映射", 121, "必须", "MUST", ["activity.text_delta_transport", "activity.legacy_dot_path_mapping"], [109, 121]],
        ["trusted-receiver-limits-watermarks-end-evidence", 121, "在可信接收/物化入口核对累计限额、原子水位和应用结束证据", 121, "在可信接收/物化入口核对累计限额、原子水位和应用结束证据", "MUST", ["activity.text_delta_transport"], [109, 121]],
    )),
    dict(owner=EDITION_OWNERS[6], section=6, scope=[126, 148],
         sha256="032eb72c07bc2375fff61be553534cc4b9f6b326f572976ffdaa72e6ed17b406", rows=(
        ["open-noncritical-fields-known-validation", 126, "仍执行已知字段校验", 126, "仍执行已知字段校验", "MUST", ["activity.security_input"], [126, 148]],
        ["security-commands-policy-default-closed", 126, "命令、授权、policy、部署控制配置与影响安全判断的报告 envelope 默认关闭", 126, "命令、授权、policy、部署控制配置与影响安全判断的报告 envelope 默认关闭", "MUST", ["activity.security_input"], [126, 148]],
        ["namespaced-extension-no-implicit-authority", 126, "扩展只能进入显式命名空间且不能自动获得安全语义", 126, "只能", "MUST", ["activity.security_input"], [126, 148]],
        ["closed-object-rejects-unknown", 126, "已声明 closed 的对象依其契约拒绝未知字段", 126, "已声明 closed 的对象依其契约拒绝未知字段", "MUST", ["activity.security_input"], [126, 148]],
        ["unsupported-critical-extension-rejects-action", 126, "旧消费者不理解即拒绝该动作", 126, "旧消费者不理解即拒绝该动作", "MUST", ["activity.security_input"], [126, 148]],
        ["size-depth-parse-cost-bounds", 128, "接收方必须限制大小、嵌套和解析成本", 128, "必须", "MUST", ["activity.security_input"], [126, 148]],
        ["duplicates-types-enums-coercions-reject", 128, "安全对象拒绝重复 key、歧义类型、未定义枚举和隐式类型转换", 128, "安全对象拒绝重复 key、歧义类型、未定义枚举和隐式类型转换", "MUST", ["activity.security_input"], [126, 148]],
        ["unknown-forwarded-data-not-authority", 128, "允许透传的未知字段不得被中间代理解释成权限", 128, "不得", "MUST", ["activity.security_input"], [126, 148]],
        ["dialect-vocabulary-validator-format-numeric-unicode-reference-profile", 130, "精确交换合同登记 schema dialect、词汇表、验证器与配置、格式断言、数值/Unicode 行为和引用闭包", 130, "精确交换合同登记 schema dialect、词汇表、验证器与配置、格式断言、数值/Unicode 行为和引用闭包", "MUST", ["activity.security_input"], [126, 148]],
        ["crossfield-id-uniqueness-and-permissions-independent", 130, "安全入口另行验证跨字段、按 ID 的唯一性及权限约束", 130, "安全入口另行验证跨字段、按 ID 的唯一性及权限约束", "MUST", ["activity.security_input"], [126, 148]],
        ["required-format-real-assertion", 130, "必需格式用真实断言或等效语义检查实施", 130, "必需格式用真实断言或等效语义检查实施", "MUST", ["activity.security_input"], [126, 148]],
        ["unsupported-required-vocabulary-dialect-no-silent-ignore", 130, "未支持的必需词汇/方言拒绝", 130, "未支持的必需词汇/方言拒绝", "MUST", ["activity.security_input"], [126, 148]],
        ["same-validated-value-parser-schema-decision", 132, "解析、schema 校验和语义裁定使用同一份经验证输入", 132, "解析、schema 校验和语义裁定使用同一份经验证输入", "MUST", ["activity.security_input"], [126, 148]],
        ["no-reparse-default-delete-coerce-after-validation", 132, "禁止验证后重新解析未固定的原文", 132, "禁止", "MUST", ["activity.security_input"], [126, 148]],
        ["approved-fixed-mapping-original-and-identity", 132, "保留原始输入与映射身份", 132, "保留原始输入与映射身份", "MUST", ["activity.security_input"], [126, 148]],
        ["legacy-no-global-schema-reinterpretation", 132, "历史格式仍按已承诺规则读取", 132, "历史格式仍按已承诺规则读取", "MUST", ["activity.security_input"], [126, 148]],
        ["archive-format-member-type-budget-before-consumption", 134, "在解析/解压前确定支持格式、成员类型和资源预算", 134, "确定", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["archive-actual-transfer-expanded-bytes-members-path-cpu-memory-deadline", 134, "消费中同时约束实际传输字节、展开后累计/单项字节、成员数量、路径长度/深度及 CPU、内存和截止时间", 134, "约束", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["archive-length-compression-signature-type-not-consumption", 134, "均不替代实际消耗计量", 134, "不替代", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["nested-archive-shared-budget-no-reset", 134, "不能每层重置计数", 134, "不能", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["separate-new-staging-no-path-link-type-collision", 136, "规范化后的重复成员、跨平台路径碰撞、未批准链接/特殊文件及文件—目录类型冲突直接拒绝", 136, "拒绝", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["archive-no-warning-downgrade", 136, "安全关键拒绝不得被“记录 warning 后跳过”降为完整包成功", 136, "不得", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["archive-complete-member-format-manifest-digest-before-register", 136, "只有全部必需成员、格式完整性、清单和摘要校验完成", 136, "只有", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["partial-archive-not-validation-or-activation", 136, "解压中断或超限后的部分目录不能参与验证或激活", 136, "不能", "MUST", ["activity.security_input", "activity.archive_input"], [126, 148]],
        ["http-framing-before-json-and-effects", 138, "在JSON/schema之前先建立无歧义的消息边界", 138, "先", "MUST", ["activity.security_input", "transport.http_security_command"], [126, 148]],
        ["decoded-case-sensitive-duplicate-keys-before-host-map", 140, "按解码后的精确成员名检查重复项", 140, "按解码后的精确成员名检查重复项", "MUST", ["activity.security_input"], [126, 148]],
        ["one-complete-json-value-no-trailing-value-or-garbage", 140, "禁止读取首个值成功后忽略第二个值或垃圾尾部", 140, "禁止", "MUST", ["activity.security_input"], [126, 148]],
        ["missing-null-zero-false-empty-distinct", 142, "字段的缺失、`null`、零、`false` 和空集合分别按 schema/语义判断", 142, "字段的缺失、`null`、零、`false` 和空集合分别按 schema/语义判断", "MUST", ["activity.security_input"], [126, 148]],
        ["no-old-default-or-partial-request-state", 142, "解析时不得把前一请求对象的旧字段、未定义默认值或部分错误结果带入本次决定", 142, "不得", "MUST", ["activity.security_input"], [126, 148]],
        ["invalid-unicode-and-unrepresentable-numbers-reject-before-decision", 142, "无效 UTF-8、孤立 UTF-16 代理项及超出字段可表示域的数值，在安全判断前明确拒绝", 142, "无效 UTF-8、孤立 UTF-16 代理项及超出字段可表示域的数值，在安全判断前明确拒绝", "MUST", ["activity.security_input"], [126, 148]],
        ["exact-bounded-sequence-budget-generation-arithmetic", 142, "序号、额度和代次的解析、比较及加法均须精确且检查界限", 142, "须", "MUST", ["activity.security_input"], [126, 148]],
        ["yaml-fixed-version-parser-tag-document-mapping", 144, "登记实际版本、解析器/标量解析规则、标签、文档数量及到受治理对象的映射", 144, "登记", "MUST", ["activity.security_input", "format.yaml_security_config"], [126, 148]],
        ["yaml-single-document-string-keys-contract-scalars", 144, "单文档、字符串 key 和合同明确的标量类型", 144, "限定", "MUST", ["activity.security_input", "format.yaml_security_config"], [126, 148]],
        ["yaml-no-unapproved-merge-object-cyclic-alias-expansion", 144, "默认禁用 merge key、自定义对象构造、循环 alias 及未批准的 alias 展开", 144, "禁用", "MUST", ["activity.security_input", "format.yaml_security_config"], [126, 148]],
        ["yaml-approved-expansion-conflict-cost-lossless", 144, "独立批准的确定性展开、冲突处理、成本上限和无损映射", 144, "必须", "MUST", ["activity.security_input", "format.yaml_security_config", "yaml.reference_expansion"], [126, 148]],
        ["yaml-key-tag-scalar-before-lossy-host-map", 146, "重复 key、标签和标量类型须在构造成可能覆盖或合并键值的宿主 map 前检查", 146, "须", "MUST", ["activity.security_input", "format.yaml_security_config"], [126, 148]],
        ["yaml-directives-no-parser-switch-or-historic-reinterpretation", 146, "版本指令、锚点和多文档输入不能临时切换已批准解析规则", 146, "不能", "MUST", ["activity.security_input", "format.yaml_security_config"], [126, 148]],
        ["historic-open-fields-preserved", 148, "禁止把历史合法开放字段一律按“安全修复”删除", 148, "禁止", "MUST", ["activity.security_input"], [126, 148]],
        ["partial-parse-no-state-write", 148, "解析失败后的部分对象不得进入状态写入", 148, "不得", "MUST", ["activity.security_input"], [126, 148]],
        ["parser-upgrade-differential-compatible-fixtures", 148, "解析器或配置升级须重跑差分与兼容 fixtures", 148, "须", "MUST", ["activity.security_input", "activity.parser_upgrade"], [126, 148]],
    )),
    dict(owner=EDITION_OWNERS[7], section=7, scope=[153, 155],
         sha256="e49cf19338773c2c366ee12ea6f678520555d6136c652b2a61d6ef1670b489b4", rows=(
        ["das-json-camel-case", 153, "DAS 自有的 canonical JSON 字段继续使用 camelCase", 153, "DAS 自有的 canonical JSON 字段继续使用 camelCase", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["native-protocol-name-recorded-lossless-boundary", 153, "有记录、确定性且不丢失语义的适配边界", 153, "有记录、确定性且不丢失语义的适配边界", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["no-data-content-header-key-renaming", 153, "动态数据 key、用户内容、HTTP header 名等不得被误当作 DAS schema 字段统一改名", 153, "不得", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["existing-protobuf-rules-preserved", 153, "Protobuf 现有规则保留", 153, "Protobuf 现有规则保留", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["inventory-owner-and-mapping-ref", 155, "契约 inventory 标注格式所有者与 mappingRef", 155, "契约 inventory 标注格式所有者与 mappingRef", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["collision-case-loss-or-irreversibility-fails", 155, "字段碰撞、大小写折叠丢失和不可逆转换失败", 155, "字段碰撞、大小写折叠丢失和不可逆转换失败", "MUST", ["activity.canonical_serialization"], [153, 155]],
        ["no-native-exception-rewrites-das-fields", 155, "不得借外部例外改写已经发布的 DAS 自有字段", 155, "不得", "MUST", ["activity.canonical_serialization"], [153, 155]],
    )),
    dict(owner=EDITION_OWNERS[8], section=8, scope=[160, 178],
         sha256="3179b90cf9dd03152f86c906062020234345062600cca03d444a6115bc1d6b7d", rows=(
        ["artifact-explicit-byte-stream-digest", 160, "文件/制品完整性采用明确字节流的摘要", 160, "文件/制品完整性采用明确字节流的摘要", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.artifact_digest"}, {"op": "fact", "key": "activity.new_json_semantic_digest"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["new-json-jcs-utf8-sha256-identity-method", 160, "RFC 8785 JCS + UTF-8 + SHA-256", 160, "RFC 8785 JCS + UTF-8 + SHA-256", "MUST", ["activity.new_json_semantic_digest"], [160, 178]],
        ["json-duplicate-nonfinite-invalid-unicode-no-rounding", 160, "不能静默四舍五入", 160, "不能", "MUST", ["activity.new_json_semantic_digest"], [160, 178]],
        ["jcs-no-unicode-normalization", 160, "JCS 不进行 Unicode 归一化", 160, "JCS 不进行 Unicode 归一化", "MUST", ["activity.new_json_semantic_digest"], [160, 178]],
        ["envelope-payload-no-self-digest-cycle", 162, "签名/授权 envelope 与被摘要 payload 分开，避免循环", 162, "签名/授权 envelope 与被摘要 payload 分开，避免循环", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.artifact_digest"}, {"op": "fact", "key": "activity.new_json_semantic_digest"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["legacy-digest-meaning-new-method-distinct-identity", 162, "不复用原名伪装相同含义", 162, "不复用原名伪装相同含义", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.artifact_digest"}, {"op": "fact", "key": "activity.new_json_semantic_digest"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["signed-identity-purpose-audience-binding", 164, "安全关键的契约身份、消息用途、受众及绑定字段必须处于已签名载荷内", 164, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.signed_object_exchange"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["no-unsigned-policy-task-from-signed-hash", 164, "不能仅签 reportDigest 后信任未签名的 policy 或 task 字段", 164, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.signed_object_exchange"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["task-candidate-verification-integration-completion-dag", 164, "后产生的证据不得进入前一对象的自身摘要", 164, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.signed_object_exchange"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["dsse-original-pae-before-application-parse", 166, "签名输入为协议定义的类型与 payload 的 PAE 编码", 166, "为", "MUST", ["format.dsse"], [160, 178]],
        ["dsse-same-payload-no-json-reorder-or-envelope-switch", 166, "不能先重排 JSON 再验签", 166, "不能", "MUST", ["format.dsse"], [160, 178]],
        ["dsse-keyid-not-trust-distinct-keys-principals", 166, "重复签名不增加批准数", 166, "不增加", "MUST", ["format.dsse"], [160, 178]],
        ["certificate-issuer-identity-purpose-candidate-time-current-policy", 168, "消费端仍须核对受信 issuer、批准的签发身份/工作流、用途、候选与制品摘要、签发时间依据及当前资格政策", 168, "须", "MUST", ["format.certificate_evidence"], [160, 178]],
        ["transparency-or-chain-not-authority-execution-completion", 168, "不能代替授权、测试执行或业务完成", 168, "不能", "MUST", ["format.certificate_evidence"], [160, 178]],
        ["jwt-mutually-exclusive-message-purpose-rules", 170, "必须为访问授权、身份登录、验证证据及动作回执定义不可混用的接收规则", 170, "必须", "MUST", ["format.jwt_adapter"], [160, 178]],
        ["jwt-protected-algorithm-issuer-key-and-claims", 170, "入口从受保护配置选择协议、允许算法和 issuer—key 绑定", 170, "从", "MUST", ["format.jwt_adapter"], [160, 178]],
        ["jwt-kid-bounded-approved-key-lookup-no-untrusted-fetch", 172, "不能拼接 SQL、文件路径或执行命令", 172, "不能", "MUST", ["format.jwt_adapter"], [160, 178]],
        ["jwt-key-refresh-current-approved-provider-boundaries", 172, "只访问当前批准的提供者及端点", 172, "只", "MUST", ["format.jwt_adapter", "activity.key_refresh"], [160, 178]],
        ["portable-evidence-no-unsigned-or-algorithm-confusion", 172, "拒绝无签名、错误算法、错误密钥类型和算法混淆", 172, "拒绝无签名、错误算法、错误密钥类型和算法混淆", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.signed_object_exchange"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["local-channel-record-not-portable-signature", 172, "不能标成已经具备独立可携带签名", 172, "不能", "MUST", ["format.local_authenticated_record"], [160, 178]],
        ["http-digest-explicit-object-algorithm-byte-domain", 174, "每个被验证摘要须明确其对象、算法和字节边界", 174, "须", "MUST", ["activity.http_artifact_download"], [160, 178]],
        ["http-content-representation-partial-encoding-distinct", 174, "不能当成完整 representation 的摘要", 174, "不能", "MUST", ["activity.http_artifact_download"], [160, 178]],
        ["http-data-and-hash-not-independent-origin", 174, "服务端同时提供数据和一个相符 hash 不独立证明来源或任务适用性", 174, "不独立证明", "MUST", ["activity.http_artifact_download"], [160, 178]],
        ["download-original-view-approved-decoding-final-artifact", 176, "下载器须记录实际获取视图与工件合同的映射", 176, "须", "MUST", ["activity.http_artifact_download"], [160, 178]],
        ["no-recompression-as-original-byte-proof", 176, "不能把已解码内容重新 gzip 来重建“原始响应”", 176, "不能", "MUST", ["activity.http_artifact_download"], [160, 178]],
        ["required-trailer-before-trusted-artifact-publication", 176, "必需 trailer 未到达时不发布可信完整工件", 176, "不发布", "MUST", ["activity.http_artifact_download", "http.required_trailer"], [160, 178]],
        ["unknown-digest-method-rejects-security-decision", 178, "未知算法/方法拒绝用于安全决定", 178, "未知算法/方法拒绝用于安全决定", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.artifact_digest"}, {"op": "fact", "key": "activity.new_json_semantic_digest"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
        ["crosslanguage-known-answer-byte-digest-fixtures", 178, "跨语言 known-answer fixtures 比较字节和摘要", 178, "跨语言 known-answer fixtures 比较字节和摘要", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.artifact_digest"}, {"op": "fact", "key": "activity.new_json_semantic_digest"}, {"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [160, 178]],
    )),
)



# Reviewed edition semantics; these mappings preserve the normative author and
# its complete exceptions. The independent 1.4 baseline remains unchanged.
EDITION_COMPLETION_GROUPS += (
    dict(owner=EDITION_OWNERS[9], section=9, scope=[183, 191],
         sha256="63ba546ec728c4bc28ee245cc48f04da4f4fe19902b8e2940675db1185c2471b", rows=(
        ["agent-and-generated-output-untrusted", 183, "Agent 与其生成产物均为不可信输入", 183, "Agent 与其生成产物均为不可信输入", "MUST", ["activity.agent_execution"], [183, 191]],
        ["tcb-assets-owner-update-identity-stop", 183, "可信计算基必须明确资产、owner、更新权限、版本/摘要、运行身份和失陷后的停止条件", 183, "必须", "MUST", ["activity.agent_execution"], [183, 191]],
        ["prompt-role-worktree-lease-review-not-isolation-authority", 183, "均不能独立证明隔离或授权", 183, "不能", "MUST", ["activity.agent_execution"], [183, 191]],
        ["worker-no-current-control-roots-baselines-signers-publish-protection-write", 185, "Agent 不得写入当前控制面政策、信任根、受保护验收基线、证据签发器和发布保护", 185, "不得", "MUST", ["activity.agent_execution"], [183, 191]],
        ["control-proposals-independent-approval-new-policy", 185, "须独立批准并形成新政策身份", 185, "须", "MUST", ["activity.agent_execution"], [183, 191]],
        ["roots-independent-pre-worker-installation", 187, "初始信任根由有权维护者在 Agent 可控执行之前，通过独立安装/管理通道建立", 187, "初始信任根由有权维护者在 Agent 可控执行之前，通过独立安装/管理通道建立", "MUST", ["activity.agent_execution"], [183, 191]],
        ["repo-root-key-approved-bit-only-input", 187, "仓库附带的 key、根证书或 `approved: true` 都只是输入", 187, "仓库附带的 key、根证书或 `approved: true` 都只是输入", "MUST", ["activity.agent_execution"], [183, 191]],
        ["control-update-current-authorization-protected-check-new-identity-atomic-activate", 187, "须由当前有效控制面授权、用当前受保护验收检查，形成新身份后原子激活", 187, "须", "MUST", ["activity.agent_execution", "activity.control_update"], [183, 191]],
        ["candidate-rules-no-self-authorized-replacement", 187, "不得以候选自带的新规则证明其有权替换旧规则", 187, "不得", "MUST", ["activity.agent_execution"], [183, 191]],
        ["control-switch-inflight-generations-revocation-recovery", 187, "切换时处理在途请求、旧代次、凭据撤销及恢复边界", 187, "处理", "MUST", ["activity.agent_execution", "activity.control_update"], [183, 191]],
        ["real-principal-control-independence", 187, "换账号、换模型或换进程不自动构成独立", 187, "换账号、换模型或换进程不自动构成独立", "MUST", ["activity.agent_execution"], [183, 191]],
        ["all-protected-targets-and-bypass-credentials-inventory", 189, "所有受保护写路径纳入部署清单", 189, "所有受保护写路径纳入部署清单", "MUST", ["activity.agent_execution"], [183, 191]],
        ["legacy-cli-protected-change-or-accepted-false-proof-denied", 189, "旧 CLI 能改变这些目标或伪造目标接受的证明即构成失败", 189, "旧 CLI 能改变这些目标或伪造目标接受的证明即构成失败", "MUST", ["activity.agent_execution"], [183, 191]],
        ["deployment-capability-and-roots-before-governed-execution", 191, "受治理执行前验证部署能力与信任根", 191, "受治理执行前验证部署能力与信任根", "MUST", ["activity.agent_execution"], [183, 191]],
        ["missing-capabilities-only-approved-readonly-diagnostics", 191, "不允许默认为具备零信任执行能力", 191, "不允许", "MUST", ["activity.agent_execution"], [183, 191]],
        ["required-minimum-control-runtime-tests", 191, "A02–A08、A17、A32 必须实测", 191, "必须", "MUST", ["activity.agent_execution"], [183, 191]],
    )),
    dict(owner=EDITION_OWNERS[10], section=10, scope=[196, 226],
         sha256="a29f411506b5b31031263c972bb25f56454b12df8cc0da2097a61363ca0773d1", rows=(
        ["layered-authority-intersection", 196, "组织/项目政策、任务边界、委派范围、工具政策、资源政策、所需批准及当前运行能力的交集", 196, "组织/项目政策、任务边界、委派范围、工具政策、资源政策、所需批准及当前运行能力的交集", "MUST", ["activity.protected_action"], [196, 226]],
        ["subject-resource-action-parameters-expiry-generation-budget-key-bound", 196, "绑定主体、目标、具体动作和参数、期限、授权代次、预算与幂等键", 196, "绑定主体、目标、具体动作和参数、期限、授权代次、预算与幂等键", "MUST", ["activity.protected_action"], [196, 226]],
        ["default-deny-delegation-only-attenuates-resource-every-time", 196, "未授权默认拒绝；委派只能衰减；实际副作用入口逐次校验", 196, "未授权默认拒绝；委派只能衰减；实际副作用入口逐次校验", "MUST", ["activity.protected_action"], [196, 226]],
        ["submit-protected-branch-complete-config-release-separately-authorized", 198, "提交候选、修改保护分支、关闭任务、修改关键配置和生产发布分别授权", 198, "提交候选、修改保护分支、关闭任务、修改关键配置和生产发布分别授权", "MUST", ["activity.protected_action"], [196, 226]],
        ["long-task-periodic-and-every-write-revocation-check", 198, "长任务定期检查撤销，并在每个受保护写入点重新检查", 198, "长任务定期检查撤销，并在每个受保护写入点重新检查", "MUST", ["activity.protected_action"], [196, 226]],
        ["external-no-idempotency-known-failure-unknown-recovery-no-exactly-once", 198, "不能宣称通用 exactly-once", 198, "不能", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
        ["delegation-protected-parent-child-provenance", 200, "控制面保存有效授权依据的父子关系", 200, "保存", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["delegation-current-actor-represented-subject-all-ancestors", 200, "执行点核对当前行为主体、获准代表的主体、祖先授权有效性", 200, "核对", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["delegation-resource-purpose-parameters-expiry-quota-attenuation", 200, "子授权不得超出任一有效祖先的限制", 200, "不得", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["delegation-invalid-parent-no-renewal-or-revocation-bypass", 200, "父授权撤销确认生效后，其派生授权不得继续支持新动作", 200, "不得", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["delegation-depth-size-cost-bounded", 200, "委派层数、大小与求值成本有界", 200, "有界", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["delegation-shared-ancestor-business-budget-atomic", 200, "不能为每个子令牌复制完整预算", 200, "不能", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["client-role-or-audit-actor-chain-not-authority", 200, "不能把客户端附带的角色历史或 token 中仅供审计的 actor 链当作权威", 200, "不能", "MUST", ["activity.protected_action", "activity.delegation"], [196, 226]],
        ["actual-normalized-domain-tenant-object-action-parameter-authority", 202, "受控解析器最终确定的资源域、租户、对象、动作及参数约束", 202, "受控解析器最终确定的资源域、租户、对象、动作及参数约束", "MUST", ["activity.protected_action"], [196, 226]],
        ["original-normalized-request-bound-and-changes-rechecked", 202, "入口保留原始请求与规范化结果的绑定", 202, "入口保留原始请求与规范化结果的绑定", "MUST", ["activity.protected_action"], [196, 226]],
        ["alias-redirect-conversion-resource-change-recheck", 202, "须重新检查批准范围", 202, "须", "MUST", ["activity.protected_action"], [196, 226]],
        ["no-domain-prefix-or-gateway-confused-deputy", 202, "不利用网关自身较高权限代替调用者的授权", 202, "不利用网关自身较高权限代替调用者的授权", "MUST", ["activity.protected_action"], [196, 226]],
        ["resource-object-lifetime-distinct-same-name-recreation", 204, "资源身份须区分对象的持续存在与删除后的同名重建", 204, "须", "MUST", ["activity.protected_action"], [196, 226]],
        ["resource-id-never-reassigned", 204, "内部 resourceId 在其权威域内不重新分配", 204, "内部 resourceId 在其权威域内不重新分配", "MUST", ["activity.protected_action"], [196, 226]],
        ["external-reusable-name-protected-provider-tenant-creation-instance", 204, "外部服务仅提供可复用名称/编号时", 204, "通过受保护映射", "MUST", ["activity.protected_action", "resource.external_reusable_name"], [196, 226]],
        ["name-path-digest-resettable-version-not-instance-continuity", 204, "名称、路径、内容摘要及可重置版本号均不能单独证明实例连续性", 204, "不能", "MUST", ["activity.protected_action"], [196, 226]],
        ["creation-instance-content-version-authorization-generation-distinct", 204, "创建实例与同一对象的内容版本、授权代次分别保存", 204, "创建实例与同一对象的内容版本、授权代次分别保存", "MUST", ["activity.protected_action"], [196, 226]],
        ["retired-remapped-instance-invalidates-current-dependencies-history-retained", 204, "依赖旧实例的当前授权、Decision、待发送请求和缓存关联失效", 204, "依赖旧实例的当前授权、Decision、待发送请求和缓存关联失效", "MUST", ["activity.protected_action"], [196, 226]],
        ["unknown-instance-continuity-deny-or-unsupported", 204, "无法区分实例时，停止依赖旧实例绑定的动作", 204, "无法区分实例时，停止依赖旧实例绑定的动作", "MUST", ["activity.protected_action"], [196, 226]],
        ["new-instance-no-budget-execution-unknown-reset", 204, "新实例登记不得重置同一业务义务的预算、已执行事实或未知结果", 204, "不得", "MUST", ["activity.protected_action"], [196, 226]],
        ["receipt-fact-not-future-action-authority", 206, "Action Receipt 证明某动作的执行事实，不能直接作为后续动作的授权", 206, "不能", "MUST", ["activity.protected_action"], [196, 226]],
        ["authority-authorization-lease-target-generations-distinct", 206, "这些值承担不同职责，不能共用一个笼统的 epoch", 206, "不能", "MUST", ["activity.protected_action"], [196, 226]],
        ["effect-linearization-point-revocation-fence", 206, "在该点之前撤销或代次变化的请求必须拒绝", 206, "必须", "MUST", ["activity.protected_action"], [196, 226]],
        ["legal-committed-fact-preserved-compensation-separately-authorized", 206, "合法已提交动作不因稍后撤销自动回滚", 206, "合法已提交动作不因稍后撤销自动回滚", "MUST", ["activity.protected_action"], [196, 226]],
        ["external-gateway-fence-equivalence-tested-or-unsupported", 206, "是否满足目标提交的 fencing 仍须按该资源合同实测", 206, "须", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
        ["business-key-domain-resource-class-action-id", 208, "受保护业务唯一键为 `(authorityDomain, resourceId, actionClass, businessActionId)`", 208, "受保护业务唯一键为 `(authorityDomain, resourceId, actionClass, businessActionId)`", "MUST", ["activity.protected_action"], [196, 226]],
        ["business-id-approved-plan-or-protected-state-client-key-only-alias", 208, "`businessActionId` 由批准计划或受保护状态分配", 208, "`businessActionId` 由批准计划或受保护状态分配", "MUST", ["activity.protected_action"], [196, 226]],
        ["immutable-request-fingerprint-not-business-key-components", 208, "不能放进唯一键来容许“同键改参数”创建新动作", 208, "不能", "MUST", ["activity.protected_action"], [196, 226]],
        ["handoff-current-actor-not-original-actor-rewrite", 208, "当前执行/恢复主体独立记录并逐次认证", 208, "当前执行/恢复主体独立记录并逐次认证", "MUST", ["activity.protected_action"], [196, 226]],
        ["epoch-policy-attempt-token-no-business-key-reset", 208, "均不得重置该业务唯一键", 208, "不得", "MUST", ["activity.protected_action"], [196, 226]],
        ["same-business-request-original-result-inflight-unknown", 210, "同一业务动作、相同请求返回原结果或执行中/未知状态", 210, "同一业务动作、相同请求返回原结果或执行中/未知状态", "MUST", ["activity.protected_action"], [196, 226]],
        ["different-request-fingerprint-reject", 210, "不同请求指纹拒绝", 210, "不同请求指纹拒绝", "MUST", ["activity.protected_action"], [196, 226]],
        ["historical-result-current-read-authority", 210, "返回历史结果仍须具有当前读取权限", 210, "须", "MUST", ["activity.protected_action"], [196, 226]],
        ["proven-not-executed-retry-current-authority-original-key-budget", 210, "能够证明尚未执行的动作可以经新的有效授权继续", 210, "能够证明尚未执行的动作可以经新的有效授权继续", "MUST", ["activity.protected_action"], [196, 226]],
        ["executed-or-unknown-no-new-authorization-resend", 210, "已执行或结果未知时，更新授权不能使之重新执行", 210, "不能", "MUST", ["activity.protected_action"], [196, 226]],
        ["handoff-reference-no-token-approval-lease-transfer", 210, "既有令牌、批准和租约不会随引用自动转移", 210, "既有令牌、批准和租约不会随引用自动转移", "MUST", ["activity.protected_action"], [196, 226]],
        ["new-business-obligation-approval-shared-budget", 210, "真正的新业务动作须独立满足任务义务、批准及共享预算约束", 210, "须", "MUST", ["activity.protected_action"], [196, 226]],
        ["atomic-budget-before-effect-no-timeout-refund", 210, "超时不自动退还可能已使用的额度", 210, "超时不自动退还可能已使用的额度", "MUST", ["activity.protected_action"], [196, 226]],
        ["dedup-retention-all-retries-expired-not-new-action", 210, "期满请求明确失效，不得自动当成从未执行", 210, "不得", "MUST", ["activity.protected_action"], [196, 226]],
        ["admission-irrevocable-send-remote-commit-distinct", 212, "资源合同必须区分网关准入、不可撤回发送和远端实际提交", 212, "必须", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
        ["outbox-intent-not-effect-current-authority-before-send", 212, "实际发送前再次核对当前授权", 212, "核对", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
        ["remote-required-commit-fence-tested-or-unsupported", 212, "必须有目标侧条件提交/fencing 或经实测的等效协议", 212, "必须", "MUST", ["activity.protected_action", "resource.requires_remote_commit_fence"], [196, 226]],
        ["late-receipt-history-not-new-effect-or-completion-authority", 212, "不能自动授权新的副作用、集成或完成", 212, "不能", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
        ["http-condition-checked-at-actual-effect-point", 214, "适配器须证明条件在实际产生副作用的目标执行点检查", 214, "须", "MUST", ["activity.protected_action", "resource.http_baseline_mutation"], [196, 226]],
        ["ifmatch-strong-native-weak-and-wildcard-not-version", 214, "`W/` 弱标签不能作为匹配强条件", 214, "不能", "MUST", ["activity.protected_action", "resource.http_baseline_mutation"], [196, 226]],
        ["etag-aba-instance-generation-separate", 214, "不能把普通 ETag 声称为唯一事务代次", 214, "不能", "MUST", ["activity.protected_action", "resource.http_baseline_mutation"], [196, 226]],
        ["no-atomic-condition-required-cas-stays-closed", 214, "需要 CAS 的集成/发布路径保持关闭或使用经证明的等效资源入口", 214, "保持关闭", "MUST", ["activity.protected_action", "resource.requires_cas"], [196, 226]],
        ["http-202-queue-sdk-not-completion", 216, "实际完成凭绑定业务动作的终态结果、目标状态或可验证回执确认", 216, "确认", "MUST", ["activity.protected_action", "transport.http_action"], [196, 226]],
        ["status-poll-cancel-current-authority-destination-budget", 216, "状态查询/轮询与取消请求各有当前授权、目的地和有界额度", 216, "有", "MUST", ["activity.protected_action", "transport.http_action"], [196, 226]],
        ["failure-timeout-no-absence-or-new-baseline-key", 216, "不能自动换基线、换动作键继续执行", 216, "不能", "MUST", ["activity.protected_action", "transport.http_action"], [196, 226]],
        ["all-retry-layers-one-approved-plan", 218, "SDK、HTTP 客户端、代理、任务重投和业务层的重试共同进入同一批准执行计划", 218, "进入", "MUST", ["activity.protected_action", "activity.action_retry"], [196, 226]],
        ["attempt-time-backoff-error-retention-unknown-policy-fixed", 218, "计划固定实际尝试上限、累计时限、退避/抖动、可重试错误、幂等保留期及结果未知核对方式", 218, "固定", "MUST", ["activity.protected_action", "activity.action_retry"], [196, 226]],
        ["hidden-retry-off-or-every-send-current-fenced", 218, "内层默认自动重试必须关闭", 218, "必须", "MUST", ["activity.protected_action", "activity.action_retry"], [196, 226]],
        ["business-reservation-distinct-metered-transport-cost", 218, "业务副作用额度与传输尝试/资源消耗按已批准口径分别记账", 218, "分别记账", "MUST", ["activity.protected_action", "activity.action_retry"], [196, 226]],
        ["retry-preserves-key-fingerprint-instance-and-retention", 218, "幂等键、请求指纹及资源实例不因重试变化", 218, "不因", "MUST", ["activity.protected_action", "activity.action_retry"], [196, 226]],
        ["fixed-program-api-subcommand-argument-syntax", 220, "受保护执行器把获批操作映射到固定程序/API、子命令及参数语法", 220, "映射", "MUST", ["activity.protected_action", "activity.protected_program_launch"], [196, 226]],
        ["no-option-response-file-config-plugin-injection", 220, "未批准行为", 220, "防止", "MUST", ["activity.protected_action", "activity.protected_program_launch"], [196, 226]],
        ["approved-options-operands-input-cwd-environment", 220, "选项、操作数、标准输入、工作目录和环境均绑定到本次获批调用", 220, "绑定", "MUST", ["activity.protected_action", "activity.protected_program_launch"], [196, 226]],
        ["native-parser-normalization-rechecks-authority", 220, "真实 parser 的归一化若改变动作或资源，须重新核对权限", 220, "须", "MUST", ["activity.protected_action", "activity.protected_program_launch"], [196, 226]],
        ["native-delimiter-only-if-supported-no-extra-args-fallback", 220, "无法无歧义表达的组合拒绝，不开放任意 extra-args 兜底", 220, "拒绝", "MUST", ["activity.protected_action", "activity.protected_program_launch"], [196, 226]],
        ["cancel-wait-domain-remote-outcome-distinct", 222, "调用方停止等待、发出取消请求、本地运行域终止和远端业务终态是独立事实", 222, "是", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["cancel-timeout-not-nonexecution-proof", 222, "它们不能单独证明底层线程、子进程或已经发出的远端动作未执行", 222, "不能", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["async-durable-identity-reservation-before-handoff", 222, "持久动作身份和必要预留按 S13 生效", 222, "生效", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["independent-supervisor-real-execution-and-late-results", 222, "监督服务独立于调用会话跟踪实际执行及迟到结果", 222, "独立", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["unknown-keeps-original-budget-dedup-no-new-action-refund", 222, "禁止重建动作或自动退款", 222, "禁止", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["cancel-new-send-denied-current-authority-cleanup-poll-compensation", 224, "取消后不得再产生未获当前授权的新业务发送", 224, "不得", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["whole-domain-termination-no-hidden-writer-or-cleanup-success", 224, "未终止的写入者和未知清理结果不得被隐藏为已完成或环境可复用", 224, "不得", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["bounded-background-supervision-no-unmanaged-shield", 224, "不能用无限屏蔽取消或脱离管理的后台任务绕过停止", 224, "不能", "MUST", ["activity.protected_action", "activity.async_action"], [196, 226]],
        ["nonbypassable-resource-entry-current-subject-dependencies-budget", 226, "权限校验位于不可由 Worker 绕过的实际资源入口", 226, "权限校验位于不可由 Worker 绕过的实际资源入口", "MUST", ["activity.protected_action"], [196, 226]],
        ["unavailable-authority-or-relationship-denies", 226, "权威不可达或授权关系不明时拒绝相应动作", 226, "权威不可达或授权关系不明时拒绝相应动作", "MUST", ["activity.protected_action"], [196, 226]],
        ["tokens-not-git-logs-task-docs", 226, "令牌不进入 Git、日志和任务文档", 226, "令牌不进入 Git、日志和任务文档", "MUST", ["activity.protected_action"], [196, 226]],
        ["atomic-approval-replay-state-reservation-recoverable", 226, "批准、防重放与状态提交采用原子校验/预留及可恢复记录", 226, "批准、防重放与状态提交采用原子校验/预留及可恢复记录", "MUST", ["activity.protected_action"], [196, 226]],
        ["adapter-native-state-count-actual-sends-and-terminal", 226, "不得仅按 HTTP 2xx 或客户端调用次数计作完成和预算", 226, "不得", "MUST", ["activity.protected_action", "activity.external_side_effect"], [196, 226]],
    )),
    dict(owner=EDITION_OWNERS[11], section=11, scope=[231, 269],
         sha256="1ed1ec5a45974198138535f4d3fd0e4334cbe89b06d757674d455b0b5b5901ab", rows=(
        ["immutable-candidate-approved-protected-tool-checks", 231, "独立 verifier 针对不可变候选执行已批准检查", 231, "独立 verifier 针对不可变候选执行已批准检查", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["candidate-gate-skip-deletion-no-acceptance-selection-authority", 231, "可信验收选择不受候选自改 gate、skip 标记或测试删除控制", 231, "可信验收选择不受候选自改 gate、skip 标记或测试删除控制", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["critical-acceptance-protected-or-independently-approved-checks", 231, "关键验收需已有受保护测试、独立审查或明确批准的补充测试支持", 231, "关键验收需已有受保护测试、独立审查或明确批准的补充测试支持", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["runner-adjudicator-signer-separated-no-release-key", 233, "runner 不持有发布和签发凭据", 233, "runner 不持有发布和签发凭据", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["network-filesystem-process-device-environment-resource-real-boundary", 233, "网络、文件系统、进程、设备、环境与资源限制必须实际生效", 233, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["execution-requirement-coverage-human-judgment-distinct", 233, "报告中区分检查执行事实、业务要求覆盖与人工判断", 233, "报告中区分检查执行事实、业务要求覆盖与人工判断", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["approved-test-resources-accounts-data-egress-budget-setup-cleanup", 235, "批准计划同时限定实际服务/租户、测试账户、数据域、允许读写、出口、额度，以及初始化和清理动作", 235, "批准计划同时限定实际服务/租户、测试账户、数据域、允许读写、出口、额度，以及初始化和清理动作", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["real-resource-tests-separate-current-authorization", 235, "验证用途的 Decision、本地 runner 权限或测试计划通过，均不自行授予这些业务权限", 235, "验证用途的 Decision、本地 runner 权限或测试计划通过，均不自行授予这些业务权限", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["negative-probes-only-approved-controlled-targets", 235, "负向探针只能使用获准的受控目标", 235, "只能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["remote-cleanup-same-resource-idempotency-budget-unknown-boundary", 237, "不能借清理脚本扩大账户权限或重试未确认副作用", 237, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["cleanup-result-independent-qualification-if-boundary-affected", 237, "清理自身的结果与测试断言分别记录", 237, "清理自身的结果与测试断言分别记录", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["candidate-domain-distinct-protected-test-observer", 239, "进一步区分不可信候选执行域与受信测试驱动/观察域", 239, "进一步区分不可信候选执行域与受信测试驱动/观察域", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["critical-observer-candidate-no-modify-debug-inject-impersonate", 239, "关键断言须由候选无法修改、调试、注入或冒充的检查器产生", 239, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["readonly-test-same-uid-process-not-isolation-proof", 239, "只读测试文件、不同进程名及同 UID 的独立进程均不足以证明隔离", 239, "只读测试文件、不同进程名及同 UID 的独立进程均不足以证明隔离", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["shared-interpreter-result-dir-tests-only-auxiliary-security-evidence", 239, "不能单独满足安全关键断言", 239, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["unavailable-external-security-observation-unsupported", 239, "无法建立该边界则相应能力不受支持", 239, "无法建立该边界则相应能力不受支持", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["static-review-not-real-isolation-authorization-proof", 239, "不能代替 Z01–Z12 所需的运行隔离、授权拒绝或不可篡改实测", 239, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["external-launcher-actual-image-identity-fd-mount-network-process", 241, "启动器在候选域外验证实际镜像、身份、文件描述符、挂载、网络与进程边界", 241, "启动器在候选域外验证实际镜像、身份、文件描述符、挂载、网络与进程边界", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["every-run-config-drift-invalidates-prior-environment-evidence", 241, "每次运行绑定配置，关键变化使旧环境证据失效", 241, "每次运行绑定配置，关键变化使旧环境证据失效", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["negative-probe-real-execution-and-reachable-positive-control", 241, "真实负向测试须有可达性/正向对照", 241, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["build-output-separate-input-builder-config-output-byte-proof", 243, "独立输出清单绑定实际输入候选、构建器/配置与精确输出字节", 243, "须", "MUST", ["activity.candidate_build"], [231, 269]],
        ["actual-output-artifact-acceptance-no-rebuild-evidence-reuse", 243, "发布时重新构建所得的新字节不得沿用旧输出证明", 243, "不得", "MUST", ["activity.candidate_build"], [231, 269]],
        ["input-no-future-output-self-digest", 243, "输入候选不包含未来输出的摘要", 243, "不包含", "MUST", ["activity.candidate_build"], [231, 269]],
        ["whole-controlled-domain-termination-not-main-exit", 245, "主进程退出或超时不证明其后代、后台线程/任务、继承句柄及待发送请求已停止", 245, "主进程退出或超时不证明其后代、后台线程/任务、继承句柄及待发送请求已停止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["candidate-all-processes-controlled-domain-aggregate-limits", 245, "所有候选进程须留在可管理的运行域", 245, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["supervisor-confirms-writers-stopped-before-output-freeze-reclaim", 245, "域外 supervisor 确认写入者已退出或被不可绕过地隔离", 245, "域外 supervisor 确认写入者已退出或被不可绕过地隔离", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["unknown-termination-cleanup-no-success-or-budget-release", 245, "不签发相应完整运行成功或释放可能已消耗的预算", 245, "不签发相应完整运行成功或释放可能已消耗的预算", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["candidate-ci-yaml-scripts-dependency-hooks-untrusted", 247, "候选中的 CI YAML、复用 workflow、测试脚本和依赖安装步骤属于候选输入", 247, "属于", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "activity.ci_verification"}]}, [231, 269]],
        ["protected-ci-job-approved-control-no-untrusted-pr-execution-with-secrets", 247, "不能在持有写权限或签发材料的上下文检出并执行待验证 PR", 247, "不能", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "activity.ci_verification"}]}, [231, 269]],
        ["cross-workflow-artifact-original-run-provenance", 247, "跨 workflow 传来的 artifact 仍按来源和原始运行身份核验", 247, "核验", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "activity.ci_verification"}]}, [231, 269]],
        ["ci-action-workflow-image-immutable-material-and-least-privilege-cache", 247, "经审查的不可变身份", 247, "固定", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "activity.ci_verification"}]}, [231, 269]],
        ["source-object-execution-view-archive-output-distinct", 249, "不能只凭同一 commit 标签认定它们逐字节相同", 249, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["archive-ignore-substitution-not-source-completeness", 249, "归档成功或归档摘要固定不足以证明源候选完整", 249, "归档成功或归档摘要固定不足以证明源候选完整", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["independent-source-material-config-test-mode-inventory", 251, "从受控导入的原始对象树/已冻结内容生成独立清单", 251, "从受控导入的原始对象树/已冻结内容生成独立清单", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["materialization-build-rule-tool-input-output-digests", 251, "物化与构建变换登记批准规则、工具/配置和输入输出摘要", 251, "物化与构建变换登记批准规则、工具/配置和输入输出摘要", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["archive-or-package-pruning-no-acceptance-denominator-shrink", 251, "完整验收候选及义务分母不随 `export-ignore`、稀疏工作区或安装包精简自动缩小", 251, "完整验收候选及义务分母不随 `export-ignore`、稀疏工作区或安装包精简自动缩小", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["dirty-untracked-explicit-freeze-or-gap-deny", 251, "需纳管的 dirty/untracked 内容必须先显式冻结或拒绝缺口", 251, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["no-auto-secret-cache-local-state-upload", 251, "秘密、非纳管缓存和本机状态不得因追求“全目录”被自动上传", 251, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["untrusted-git-metadata-hooks-replacements-no-privileged-git", 253, "受治理执行器不在此类 `.git` 中以高权限运行 Git", 253, "受治理执行器不在此类 `.git` 中以高权限运行 Git", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["no-safe-directory-or-ownership-as-execution-trust", 253, "不通过更改所有权或 `safe.directory=*` 授予执行信任", 253, "不通过更改所有权或 `safe.directory=*` 授予执行信任", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["low-privilege-import-valid-objects-only-submodule-lfs-pins", 253, "递归子模块和 LFS 获取继续逐项校验目的地、提交及实际字节", 253, "递归子模块和 LFS 获取继续逐项校验目的地、提交及实际字节", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["oci-index-selected-child-platform-config-layers-runtime-config-bound", 255, "实际选中的子 manifest、平台条件、config、按顺序应用的层以及实际启动/挂载配置", 255, "覆盖", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["oci-native-object-compressed-layer-and-diffid-distinct", 255, "压缩层摘要与 config 中未压缩层的 diff_id 分别验证", 255, "分别验证", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["oci-no-platform-child-fallback-without-evidence", 255, "不让调度、缓存、仿真或回退静默更换平台/子工件", 255, "不让", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["oci-only-selected-required-closure-legal-unused-descriptors", 257, "未选中的可选描述符按原生协议处理", 257, "处理", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["oci-required-unknown-unsupported-ordered-whiteout", 257, "层间覆盖及 whiteout 是 OCI 的原生变换，按受控层顺序解释", 257, "解释", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["oci-mounts-injections-actual-execution-identity", 257, "最终 rootfs 上的挂载和注入配置同样进入执行身份", 257, "进入", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.oci_image"}]}, [231, 269]],
        ["seccomp-notify-candidate-memory-continue-not-sole-authority", 259, "不能以“读取候选内存中的路径并返回 CONTINUE”作为资源授权的唯一执行点", 259, "不能", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.seccomp_notification"}]}, [231, 269]],
        ["seccomp-proxy-controlled-handles-separate-authority-direct-path-restricted", 259, "代理对自己持有的受控参数和资源句柄重新鉴权、独立执行并返回有界结果", 259, "重新鉴权", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, {"op": "fact", "key": "runtime.seccomp_notification"}]}, [231, 269]],
        ["dynamic-prepare-build-collection-plugin-code-isolation", 261, "需要动态钩子时进入已批准隔离域", 261, "进入", "MUST", ["activity.dynamic_candidate_preparation"], [231, 269]],
        ["dryrun-collectonly-venv-build-env-not-security-isolation", 261, "都不单独证明安全隔离", 261, "不单独证明", "MUST", ["activity.dynamic_candidate_preparation"], [231, 269]],
        ["dynamic-metadata-no-reimport-candidate-in-control", 263, "不得在可信控制进程中再次导入候选以确认它们", 263, "不得", "MUST", ["activity.dynamic_candidate_preparation"], [231, 269]],
        ["build-runtime-backend-transitive-dependencies-material-closure", 263, "构建依赖和运行依赖分别固定", 263, "固定", "MUST", ["activity.candidate_build"], [231, 269]],
        ["actual-mount-child-propagation-host-writers-shared-scratch", 265, "所选隔离组合须核对实际挂载视图", 265, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["top-readonly-image-hash-not-all-mounts-or-host-writers", 265, "顶层只读标记不证明所有子挂载只读", 265, "顶层只读标记不证明所有子挂载只读", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["trusted-input-immutable-through-run-not-posthoc-digest", 265, "不能等运行后发现摘要变化再追认此前结果", 265, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["unsupported-recursive-readonly-mount-combination-denies", 267, "不静默退化为部分可写", 267, "不静默退化为部分可写", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["approved-input-update-new-binding-and-run", 267, "已批准输入更新须形成新的绑定及相应运行", 267, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["trusted-runner-no-host-fallback-environment-cwd-plugin-clean", 269, "可信 runner 配置禁止宿主回退", 269, "禁止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["independent-signer-original-metadata-not-worker-pass", 269, "不签署 Agent 提交的任意 PASS 文本", 269, "不签署 Agent 提交的任意 PASS 文本", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["source-view-runner-unexplained-difference-or-privileged-git-metadata-denies", 269, "未解释差异及不可信仓库元数据进入特权域均阻断", 269, "未解释差异及不可信仓库元数据进入特权域均阻断", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
        ["mount-change-trusted-input-writable-alias-drift-invalidates-proof", 269, "受信输入的任何未批准可写别名或漂移阻断该运行的有效证明", 269, "受信输入的任何未批准可写别名或漂移阻断该运行的有效证明", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.verification"}, {"op": "fact", "key": "activity.candidate_build"}, {"op": "fact", "key": "activity.dynamic_candidate_preparation"}]}, [231, 269]],
    )),
    dict(owner=EDITION_OWNERS[12], section=12, scope=[274, 312],
         sha256="f7dcd97b5e1ec443f19338c8151bd2554a2a47abde08d59dec4f75fa4bd38a76", rows=(
        ["binding-contract-schema-issuer-audience-verifier-rules", 278, "契约身份、schema 版本、签发者、受众、验证器/适配器及规则制品身份", 276, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["binding-scope-task-revision-cycle-candidate-target", 279, "authorityDomain/scope、完整 taskKey、定义修订、completion cycle、候选摘要、必要目标基线", 276, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["binding-standard-policy-plan-slots-bundle-facts", 280, "标准制品摘要、政策摘要、批准验收计划及 required-for-action 槽位/聚合集合摘要、Bundle 及事实摘要", 276, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["binding-report-artifacts-run-slot-source-env-human-review", 281, "原始报告与制品摘要、执行身份、计划槽位与原始运行/来源结果关联、运行环境及适用人工审查引用", 276, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["binding-time-authority-authorization-issue-run-attempt-purpose", 282, "签发/有效期、独立 authority epoch 与授权代次、签发 ID、运行/attempt 关联及按消息用途定义的重放约束", 276, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["old-closed-report-not-new-binding-field-carrier", 284, "不得强行塞入闭合的旧 report 对象", 284, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["trusted-source-digest-context-not-math-only-signature", 284, "不能只验证签名数学正确性", 284, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["protected-roots-and-audience-no-candidate-roots", 284, "禁止接受候选自带信任根", 284, "禁止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["all-blocking-truth-artifacts-coverage-required", 286, "完整资格必须满足所有适用 blocking 要求、必要 source-of-truth 制品和声明覆盖", 286, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["report-expected-not-action-denominator", 286, "不独立决定某动作的必需分母", 286, "不独立决定某动作的必需分母", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["required-slot-missing-invalid-result-artifact-denies", 286, "均阻断该动作资格", 286, "均阻断该动作资格", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["report-only-expected-false-no-results-not-remove-required-duty", 286, "不能解除该义务", 286, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["original-failed-notrun-error-no-rewrite-or-delete", 286, "禁止将失败改写为通过，或删除未执行观察项", 286, "禁止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["approved-nonrequired-observation-failure-retained-not-control-pass", 288, "原始异常必须可追溯，也不能被算作控制通过", 288, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["shared-collection-trust-or-impact-unknown-denies-affected", 288, "共同采集失效、信任状态不明或是否影响必需项尚不明确时，阻断受影响资格", 288, "共同采集失效、信任状态不明或是否影响必需项尚不明确时，阻断受影响资格", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["waiver-independent-no-report-outcome-rewrite", 288, "Waiver 保留独立事实，不能改写原始 outcome", 288, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["project-reportonly-no-must-conformance-denominator-removal", 288, "不得仅凭项目把某项 MUST 的 gate 标成 report_only，就将该义务移出符合性分母", 288, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["required-whole-verify-precondition-still-blocks", 288, "限定 Decision 不替代该前置条件", 288, "限定 Decision 不替代该前置条件", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["action-decision-not-project-full-conformance", 288, "具体动作的允许结果不等于项目整体符合声明", 288, "具体动作的允许结果不等于项目整体符合声明", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["stage-submit-not-integrate-release-complete", 290, "允许“提交候选”不能被解释为允许“合并、发布或完成”", 290, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["protected-plan-not-report-expectation-enumerates-required-slots", 290, "不能从候选报告的 expected 字段反推分母", 290, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["plan-slot-stable-unique-gate-config-target-env-shard", 290, "计划槽位使用 `(planId, checkSlotId)` 或等价的受保护唯一身份", 290, "计划槽位使用 `(planId, checkSlotId)` 或等价的受保护唯一身份", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["run-attempt-not-required-denominator-author", 290, "不能由新 run ID 改写必验分母", 290, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["slot-duplicate-conflict-omission-artifact-incomplete-denies", 290, "均阻断受影响决定", 290, "均阻断受影响决定", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["observation-notrun-explicit-not-hidden", 290, "计划中的观察槽位未执行也须有显式状态", 290, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["legal-retries-retained-predetermined-aggregation", 290, "合法重试的不同结果保留并按预定策略聚合", 290, "合法重试的不同结果保留并按预定策略聚合", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["manytomany-assertions-all-conditions-alternatives-fixed-before-result", 292, "须在结果产生前固定", 292, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["report-retransmit-resign-cache-not-new-independent-run", 292, "也不增加独立样本数", 292, "也不增加独立样本数", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["original-run-result-identity-actual-rerun-only-new-execution", 292, "只有实际重跑才产生新的执行事实", 292, "只有", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["no-unapproved-all-green-shard-retry-subset", 292, "分片和重试不得拼出未经批准的全绿子集", 292, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["reuse-current-valid-approved-original-mapping-no-new-run", 292, "本次未执行状态如实保留，不登记新运行", 292, "本次未执行状态如实保留，不登记新运行", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["required-independent-rerun-or-invalidated-premise-no-reuse", 292, "要求独立重跑或关键前提失效时不得复用", 292, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["repeated-evidence-read-current-policy-time-revocation-target", 294, "每次仍重新检查政策、时效、撤销与目标", 294, "每次仍重新检查政策、时效、撤销与目标", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["one-use-authorization-reservation-completion-unique", 294, "单次授权、预算预留和 Completion 消费使用受保护唯一性约束", 294, "单次授权、预算预留和 Completion 消费使用受保护唯一性约束", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["rerun-new-id-retained-failures-no-cherry-pick", 294, "不能靠挑选一次通过抹去不稳定结果", 294, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["evidence-resolvable-original-bytes-access-retention-expiry", 296, "必需证据的引用还须能在获准消费域内解析到其绑定字节", 296, "须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["digest-deleted-path-unreadable-uri-not-new-decision-proof", 296, "不足以支持新的受保护决定", 296, "不足以支持新的受保护决定", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["cleanup-expiry-no-historical-completion-erasure", 296, "不能把曾经完成改写成从未发生", 296, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["restricted-evidence-limited-authorized-verifier-not-publication-required", 296, "不要求向 Worker 公开全部原始证据", 296, "不要求向 Worker 公开全部原始证据", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["revocation-rotation-compromise-reason-order-impact-distinct", 298, "授权撤销、签发密钥正常轮换与签发身份失陷分别记录原因、生效顺序和影响范围", 298, "授权撤销、签发密钥正常轮换与签发身份失陷分别记录原因、生效顺序和影响范围", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["compromise-self-issuedat-not-prior-signature-proof", 298, "禁止仅凭“日期早于撤销”恢复信任", 298, "禁止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["compromise-independent-checkpoint-byte-history-or-revalidation", 298, "缺少足够独立依据时，相关证据隔离待查，不用于新的资格", 298, "缺少足够独立依据时，相关证据隔离待查，不用于新的资格", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["normal-key-rotation-no-current-purpose-time-authority-bypass", 298, "不绕过当前用途、有效期和授权检查", 298, "不绕过当前用途、有效期和授权检查", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["hosted-ci-success-neutral-skipped-not-required-slot-pass", 300, "仅将 check 名称设为 required 不能证明必需检查执行", 300, "不能", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, {"op": "fact", "key": "activity.ci_evidence"}]}, [274, 312]],
        ["final-ci-gate-enumerates-real-required-run-source-target", 300, "缺失、取消、过滤跳过或依赖未运行不能被空集合通过掩盖", 300, "不能", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, {"op": "fact", "key": "activity.ci_evidence"}]}, [274, 312]],
        ["supported-events-merge-mechanisms-final-deny-on-dependency-failure", 302, "最终 gate 的调度须覆盖被声明支持的事件与合并机制", 302, "须", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, {"op": "fact", "key": "activity.ci_evidence"}]}, [274, 312]],
        ["merge-queue-actual-mergegroup-candidate-binding", 302, "PR HEAD、平台测试合并提交与最终目标内容的关系按 S14 记录，不能互换", 302, "不能", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, {"op": "fact", "key": "ci.merge_queue"}]}, [274, 312]],
        ["time-absolute-relative-error-staleness-contract-distinct", 304, "时间合同分别定义跨进程/跨系统的有效区间", 304, "时间合同分别定义跨进程/跨系统的有效区间", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["half-open-interval-fixed-tolerance-no-caller-expansion", 304, "参考授权窗口使用半开区间 `[notBefore, expiresAt)`", 304, "参考授权窗口使用半开区间 `[notBefore, expiresAt)`", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["uncertain-time-boundary-source-or-rollback-denies-new-action", 304, "停止依赖该判断的新动作", 304, "停止依赖该判断的新动作", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["relative-clock-not-wall-clock-and-suspend-aware", 306, "进程内相对倒计时不能只依赖可回拨的 wall clock", 306, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["relative-clock-boot-instance-epoch-bound-not-cross-host-restore", 306, "每次相对期限绑定当前启动/实例及控制代次", 306, "每次相对期限绑定当前启动/实例及控制代次", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["recovery-current-authority-absolute-expiry-history-no-ttl-reset", 306, "不能从完整 TTL 重新开始", 306, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["relative-absolute-ancestor-limits-all-current", 308, "相对剩余时长、可信绝对截止及祖先授权限制同时满足才可继续", 308, "相对剩余时长、可信绝对截止及祖先授权限制同时满足才可继续", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["clock-calibration-no-expiry-extension-budget-reset", 308, "新的时钟校准不能自行延长已批准的最晚截止或重置预算", 308, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["renewal-new-current-basis-original-action-dedup", 308, "保持原动作身份和去重历史", 308, "保持原动作身份和去重历史", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["historic-verification-no-current-authority", 308, "不能借历史时间材料产生现时权限", 308, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["reference-clock-source-error-calibration-restart-suspend-anomaly-record", 308, "参考部署记录时钟来源、误差预算、校准/重启/挂起检测及异常处置", 308, "参考部署记录时钟来源、误差预算、校准/重启/挂起检测及异常处置", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["native-collected-selected-config-run-to-approved-slots", 310, "适配器将实际收集节点、配置/插件身份、运行/选择记录映射到获批槽位", 310, "适配器将实际收集节点、配置/插件身份、运行/选择记录映射到获批槽位", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["framework-success-xfail-skip-deselection-not-required-proof", 310, "测试失败或未运行不能因标记为XFAIL而充当通过", 310, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["negative-security-trusted-driver-rejection-positive-reachability", 310, "负向安全测试则由受信驱动确认预期拒绝和正向可达", 310, "负向安全测试则由受信驱动确认预期拒绝和正向可达", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["original-report-enums-versioned-native-state-mapping", 310, "原报告枚举不扩写", 310, "原报告枚举不扩写", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["independent-signature-complete-plan-original-run-and-aggregation", 312, "可信签发服务或独立签发进程形成 envelope", 312, "可信签发服务或独立签发进程形成 envelope", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["resource-linearization-current-authority-revocation-generation", 312, "受保护写入在其线性化点检查该资源当前权威状态中的授权、撤销及代次", 312, "受保护写入在其线性化点检查该资源当前权威状态中的授权、撤销及代次", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["offline-snapshot-evidence-not-new-action-authority", 312, "不能据此授予新的受保护动作", 312, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["current-authority-unreachable-or-stale-unknown-time-denies", 312, "禁止以过期快照或未知时间继续判断有效", 312, "禁止", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
        ["confirmed-revocation-all-related-entries-reject-old-grants", 312, "对外确认撤销已生效后，所有相关入口必须拒绝旧授权", 312, "必须", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.evidence_consumption"}, {"op": "fact", "key": "activity.evidence_issuance"}]}, [274, 312]],
    )),
)



# Reviewed edition semantics; these mappings preserve the normative author and
# its complete exceptions. The independent 1.4 baseline remains unchanged.
EDITION_COMPLETION_GROUPS += (
    dict(owner=EDITION_OWNERS[15], section=15, scope=[423, 443],
         sha256="adaae6aa266ed95df0f15affb35aea0472f83a80d69a7c548d6bfe5b763c5cee", rows=(
        ["surface-scope-source-precedence-deterministic-coverage", 423, "每个纳管 surface 记录范围、事实来源、来源优先级及确定性覆盖", 423, "每个纳管 surface 记录范围、事实来源、来源优先级及确定性覆盖", "MUST", ["surface.http"], [423, 443]],
        ["one-effective-author-for-each-fact", 423, "同一事实只能有一个有效作者源", 423, "只能", "MUST", ["surface.http"], [423, 443]],
        ["exact-declaration-and-normalized-inventory", 423, "新增 declaration 和 normalized inventory 的精确合同", 423, "新增 declaration 和 normalized inventory 的精确合同", "MUST", ["surface.http"], [423, 443]],
        ["operation-location-distinct-stable-unreused-identity", 423, "operation 定位与长期身份分开", 423, "operation 定位与长期身份分开", "MUST", ["surface.http"], [423, 443]],
        ["selector-materialized-in-source-snapshot", 425, "selector 在指定来源快照上物化操作集合", 425, "selector 在指定来源快照上物化操作集合", "MUST", ["surface.http"], [423, 443]],
        ["external-reference-approved-scope-digest", 425, "解析外部引用受批准范围与摘要约束", 425, "解析外部引用受批准范围与摘要约束", "MUST", ["surface.http"], [423, 443]],
        ["overlay-owner-one-way-generation", 425, "Overlay 必须有所有权和单向生成链", 425, "必须", "MUST", ["surface.http", "http.overlay"], [423, 443]],
        ["semantic-compatibility-undecidable-independent-review", 425, "未能判断的业务含义进入独立评审", 425, "未能判断的业务含义进入独立评审", "MUST", ["surface.http"], [423, 443]],
        ["native-openapi-schema-exact-version-dialect-supported-only", 427, "声明所用 OpenAPI/JSON Schema 的精确版本与 dialect", 427, "声明", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["unsupported-semantic-no-silent-dropped-constraints", 427, "未支持的语义须明确拒绝或经批准的无损映射", 427, "须", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["root-operation-inheritance-original-document-base-uri", 429, "root 与 operation 的覆盖关系、每份文档的基 URI", 429, "保留", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["security-requirement-inner-and-array-or", 429, "同一 Security Requirement Object 内的方案为同时满足", 429, "为", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["operation-security-empty-and-anonymous-object-native", 429, "操作级 `security: []` 可移除继承要求，空对象 `{}` 表达允许匿名", 429, "须", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["legal-anonymous-only-approved-protected-fact-conflict-rejects", 429, "不能把所有空声明一律当漏洞", 429, "不能", "MUST", ["surface.http", "http.openapi_description"], [423, 443]],
        ["declared-authentication-distinct-real-boundary-evidence", 431, "规范化 Inventory 分别记录声明与真实边界证据", 431, "规范化 Inventory 分别记录声明与真实边界证据", "MUST", ["surface.http"], [423, 443]],
        ["filtered-empty-paths-not-no-http-surface-proof", 431, "经过访问过滤的空 Paths 也不证明项目没有 HTTP surface", 431, "经过访问过滤的空 Paths 也不证明项目没有 HTTP surface", "MUST", ["surface.http"], [423, 443]],
        ["actual-route-gateway-deployment-callback-webhook-coverage", 431, "受保护候选中的实际路由、网关/部署事实、适用 webhook/callback 及范围声明进行覆盖对照", 431, "受保护候选中的实际路由、网关/部署事实、适用 webhook/callback 及范围声明进行覆盖对照", "MUST", ["surface.http"], [423, 443]],
        ["fixed-original-byte-source-base-before-offline-reference-resolution", 431, "后续解析离线进行", 431, "后续解析离线进行", "MUST", ["surface.http"], [423, 443]],
        ["legal-schema-recursion-native-bounded-not-dependency-cycle", 431, "有界遍历不能简单将所有循环都当作模块依赖环", 431, "不能", "MUST", ["surface.http"], [423, 443]],
        ["actual-protocol-gateway-proxy-application-request-equivalence", 433, "网关、代理、协议降级和应用处理器须对同一次受保护请求得到一致的目标、权限相关字段和消息体", 433, "须", "MUST", ["surface.http"], [423, 443]],
        ["ambiguity-before-effect-connection-desync-closed", 433, "存在解析分歧的请求在资源动作前拒绝并结束可能失步的连接", 433, "存在解析分歧的请求在资源动作前拒绝并结束可能失步的连接", "MUST", ["surface.http"], [423, 443]],
        ["front-rejection-not-backend-no-effect-proof", 433, "不把前端拒绝记录当作后端未执行的证明", 433, "不把前端拒绝记录当作后端未执行的证明", "MUST", ["surface.http"], [423, 443]],
        ["http11-reference-transfer-length-reject-close", 435, "采取拒绝并关闭连接的严格策略", 435, "采取", "MUST", ["surface.http", "http.http11_reference"], [423, 443]],
        ["approved-alternative-native-framing-end-to-end-proof", 435, "替代实现须证明其原生处理不造成下游边界分歧", 435, "须", "MUST", ["surface.http", "http.alternative_framing"], [423, 443]],
        ["conflicting-length-host-newline-chunk-truncation-native-errors", 435, "不同Content-Length、非法Host、多义换行、无效分块及截断按原生错误规则处理", 435, "不同Content-Length、非法Host、多义换行、无效分块及截断按原生错误规则处理", "MUST", ["surface.http"], [423, 443]],
        ["same-length-repeat-approved-normalize-or-reject", 435, "同值重复Content-Length或合法列表头按获批协议规则拒绝/归一化", 435, "同值重复Content-Length或合法列表头按获批协议规则拒绝/归一化", "MUST", ["surface.http"], [423, 443]],
        ["raw-framing-independent-final-effect-observation", 437, "验证网关和最终处理器的实际请求数、对象、正文及副作用", 437, "验证网关和最终处理器的实际请求数、对象、正文及副作用", "MUST", ["surface.http"], [423, 443]],
        ["unsupported-proxy-protocol-closed-legal-chunk-and-reuse-control", 437, "未支持的代理/协议组合保持关闭", 437, "未支持的代理/协议组合保持关闭", "MUST", ["surface.http"], [423, 443]],
        ["early-data-applicability-real-replay-boundary", 439, "按 RFC 8470/TLS 1.3 的实际重放边界审查", 439, "审查", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
        ["reference-no-early-protected-write-budget-or-sealed-feedback", 439, "参考部署默认不以 early data 执行受保护写入、消耗不可重复额度或释放密封反馈", 439, "参考部署默认不以 early data 执行受保护写入、消耗不可重复额度或释放密封反馈", "MUST", ["surface.http"], [423, 443]],
        ["get-method-no-sideeffect-or-disclosure-waiver", 439, "GET 等方法名不免除其真实副作用与披露约束", 439, "GET 等方法名不免除其真实副作用与披露约束", "MUST", ["surface.http"], [423, 443]],
        ["trusted-earlydata-connection-metadata-proxy-propagation", 441, "入口核对可信连接元数据与原生 `Early-Data` 传播", 441, "核对", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
        ["later-hop-handshake-not-earlier-hop-replay-elimination", 441, "不能消除先前链路接受早期数据所带来的重放可能", 441, "不能", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
        ["earlydata-425-before-effect-retry-not-early-same-key-budget", 441, "随后重试不再使用早期数据", 441, "不再", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
        ["earlydata-rejection-no-idempotency-current-authority-waiver", 441, "拒绝早期数据不解除应用层幂等、防重放或当前授权要求", 441, "不解除", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
        ["source-duplicate-coverage-closure-id-history-generation-gate", 443, "Cadence 检查来源完整性、重复定义、覆盖差异、引用闭包、ID 历史及生成漂移", 443, "Cadence 检查来源完整性、重复定义、覆盖差异、引用闭包、ID 历史及生成漂移", "MUST", ["surface.http"], [423, 443]],
        ["declaration-deletion-no-approved-surface-escape", 443, "删除声明不能让已批准 surface 无声退出范围", 443, "不能", "MUST", ["surface.http"], [423, 443]],
        ["unproved-replay-boundary-disables-optimization-or-action", 443, "未能证明所需重放边界时关闭对应优化或受影响动作", 443, "关闭", "MUST", ["surface.http", "http.tls_early_data"], [423, 443]],
    )),
    dict(owner=EDITION_OWNERS[16], section=16, scope=[448, 479],
         sha256="8a3dfd7c20a25a4bc39a2b0267b7971754887478a3cb0156409b88d7b8063c97", rows=(
        ["existing-uispec-workflow-screen-profile-references", 448, "复用 UI Spec、W#/UI 标识、interaction profile 和既有页面/工作流条目", 448, "复用 UI Spec、W#/UI 标识、interaction profile 和既有页面/工作流条目", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["affected-tasks-users-surfaces-design-states-denominator-frozen", 448, "冻结受影响任务、用户/角色、支持面、设计来源或批准替代基线、状态与验收分母", 448, "冻结受影响任务、用户/角色、支持面、设计来源或批准替代基线、状态与验收分母", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["scope-implementation-verification-exclusion-waiver-distinct", 448, "scope、实现、验证、excluded、waived 分开记录", 448, "scope、实现、验证、excluded、waived 分开记录", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["missing-design-use-approved-uispec-no-fake-design-id", 448, "不填写虚构设计 ID", 448, "不填写虚构设计 ID", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-task-audience-content-regions", 454, "任务、指定受众、主内容、按需入口及多个协作区域的职责", 450, "补足", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-content-audience-required-risk-authority-result-help-provenance", 455, "自有业务文案、必要风险/权限/结果提示、帮助与内部调试说明的来源及呈现位置", 450, "补足", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-complete-reading-location-scroll-links-return", 456, "任务所需完整内容的获取、载体、定位、滚动、深链接及适用返回行为", 450, "补足", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-async-object-switch-cancel-return-refresh-save-input", 457, "操作/对象归属，切换、取消、返回、刷新、保存及未保存输入的处理", 450, "补足", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-visual-behavior-token-version-a11y-regression-evidence", 458, "视觉/行为基线、token 来源版本、适用无障碍断言及回归链接", 450, "补足", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["page-equivalent-existing-structure-no-extra-contract-manifest", 450, "项目可以用等价结构表达，不必增建页面合同文件或 UI manifest", 450, "项目可以用等价结构表达，不必增建页面合同文件或 UI manifest", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["behavior-single-author-hfvi-only-applicable-base", 460, "对应稳定 requirement 的唯一语义来源", 460, "对应稳定 requirement 的唯一语义来源", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["approved-user-task-and-required-information", 464, "界面 MUST 支持获批任务及必要信息", 464, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["no-internal-orchestration-debug-instruction-user-body-projection", 464, "内部调试的指令 MUST NOT 被误投影为普通用户业务正文", 464, "MUST NOT", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["navigation-purpose-consistent", 465, "重复导航 SHOULD 按区域、目标和交互目的评估，保持命名与行为一致", 465, "SHOULD", "SHOULD", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["complete-authorized-reading", 466, "MUST 提供获授权且属于该任务范围的完整内容与适用定位/返回能力", 466, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["async-results-current-operation-object-generation-only", 467, "MUST 仅更新仍然有效的操作/对象/状态范围", 467, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["save-bound-actual-submitted-content-version", 468, "保存结果 MUST 绑定实际提交的内容/版本", 468, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["late-save-no-new-edit-loss-or-false-saved-state", 468, "提交之后新增的编辑不能因旧保存成功而丢失或被误标已保存", 468, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["unique-object-selection-needs-complete-set-and-identity", 469, "MUST 具有足够的集合完整性与身份依据", 469, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["unknown-corrupt-history-no-uniqueness-inference", 469, "未知、损坏或读取失败 MUST NOT 支持唯一性推断", 469, "MUST NOT", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["affected-token-consumption-source-version-exception-evidence", 470, "受影响组件须有足以支持实际消费关系的证据", 470, "须", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, {"op": "fact", "key": "activity.ui_token_consumption"}]}, [448, 479]],
        ["modal-focus-keyboard-approved-behavior", 471, "实际模态行为、焦点/键盘及适用无障碍要求 MUST 与获批交互约定一致", 471, "MUST", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["async-cancel-no-remote-effect-erasure-or-state-authority-proof", 473, "取消可作为资源优化，但不能单独证明旧结果已失去更新权", 473, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["a11y-static-browser-human-claims-separate", 475, "分别映射静态/自动扫描、真实浏览器键盘焦点行为及人工语义/辅助技术判断", 475, "分别映射静态/自动扫描、真实浏览器键盘焦点行为及人工语义/辅助技术判断", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["a11y-applicable-version-level-scope-approved", 475, "无障碍外部标准的版次、级别与范围来自适用条款及项目批准", 475, "无障碍外部标准的版次、级别与范围来自适用条款及项目批准", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["wcag-whole-page-process-not-representative-sample-inference", 475, "不以代表页面的样本通过推定整个站点通过", 475, "不以", "MUST", {"op": "all", "args": [{"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, {"op": "fact", "key": "ui.wcag_conformance_claim"}]}, [448, 479]],
        ["first-baseline-independent-approval-current-regression-old-approved-base", 477, "首次行为/视觉基线由独立有权主体批准", 477, "首次行为/视觉基线由独立有权主体批准", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["no-auto-created-baseline-no-regression-claim", 477, "不能自动创建基线后宣称“没有回归”", 477, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["baseline-scope-exclusion-changes-approved-before-failure-result", 477, "基线更新、范围缩减和排除项事前独立批准", 477, "基线更新、范围缩减和排除项事前独立批准", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["ui-notrun-evidence-reuse-original-s12-rules", 477, "`not_run` 保持真实含义", 477, "`not_run` 保持真实含义", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["real-origin-route-object-state-and-collection-precondition", 479, "UI 断言先证明目标 origin/route、对象、当前业务状态和采集完整", 479, "UI 断言先证明目标 origin/route、对象、当前业务状态和采集完整", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["normal-state-no-login-error-empty-shell-vacuous-pass", 479, "需要正常态的检查不能在登录页、错误壳或空页面上判通过", 479, "不能", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["error-disappearance-first-trigger-and-negative-case-reachability", 479, "检查旧错误已消失前应证明对应错误确实被触发", 479, "应", "SHOULD", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["candidate-no-driver-approved-baseline-denominator-change", 479, "候选不得修改驱动、批准基线或验收分母", 479, "不得", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["actual-build-environment-test-account-state-design-token-run-binding", 479, "行为证据绑定实际构建、环境、测试账户范围、状态数据、设计/token 基线及来源运行", 479, "行为证据绑定实际构建、环境、测试账户范围、状态数据、设计/token 基线及来源运行", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
        ["selector-screenshot-score-success-text-not-behavior-proof", 479, "仅有 selector、截图数量、自评得分或页面中的成功文本均不足以满足上述行为义务", 479, "仅有 selector、截图数量、自评得分或页面中的成功文本均不足以满足上述行为义务", "MUST", {"op": "any", "args": [{"op": "fact", "key": "surface.ui"}, {"op": "fact", "key": "surface.hfvi"}]}, [448, 479]],
    )),
    dict(owner=EDITION_OWNERS[17], section=17, scope=[484, 500],
         sha256="010bcac0646a0403f82ba9fae5271d41ce4a3d4b463a427dc627f67e9882b85f", rows=(
        ["ordinary-data-purpose-exposure-protocol-candidate", 484, "普通评测记录数据用途、已知暴露、协议与候选身份", 484, "普通评测记录数据用途、已知暴露、协议与候选身份", "MUST", ["activity.eval_suite"], [484, 500]],
        ["sealed-developer-no-private-input-secret-scoring-access", 484, "新密封声明须证明开发主体不能访问私有评测输入及秘密评分材料", 484, "须", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["sealed-runner-only-approved-inference-input", 484, "候选执行域只可接收协议批准的推理输入", 484, "只", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["sealed-runner-no-label-answer-unapproved-heldout-secret-scoring", 484, "不可访问标签、答案、未授权保留集或秘密评分材料", 484, "不可", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["sealed-candidate-and-scoring-domain-separated", 484, "候选执行域与评分域分离", 484, "分离", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["scorer-no-candidate-code-or-object-deserialization", 484, "评分域不执行候选代码或任意对象反序列化", 484, "不执行", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["secret-scope-protocol-no-blanket-public-formula-secrecy", 484, "公开评分公式无需一概保密", 484, "公开评分公式无需一概保密", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["bounded-input-no-whole-heldout-access", 486, "候选域只接收协议允许的有界评测输入", 486, "只", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["bounded-data-only-output-fixed-scoring-destination", 486, "候选结果经大小受限、无代码语义的输出合同送入评分域", 486, "经", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["private-input-predictions-logs-cache-report-no-developer-return", 486, "私有输入、原始预测、日志、缓存和受限报告不得回流开发身份", 486, "不得", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["split-before-stateful-fit-predeclare-transductive-exception", 488, "数据划分先于有状态拟合；例外 transductive 设置预先声明", 488, "数据划分先于有状态拟合；例外 transductive 设置预先声明", "MUST", ["activity.eval_suite"], [484, 500]],
        ["freeze-candidate-materials-protocol-scorer-feedback-before-private-release", 488, "首次私有输入发放前冻结代码/模型/Prompt/依赖/预处理、协议、评分器和反馈规则", 488, "冻结", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["persistent-budget-across-session-alias-account-runner", 488, "预算跨会话、别名、账户和 Runner 持久归属", 488, "持久", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["unknown-run-no-budget-neutral-retry", 488, "未知执行结果不得轻率作预算中性重试", 488, "不得", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["real-control-relationship-budget-owner-not-client-new-account", 490, "不能接受客户端自报的新账户来重置", 490, "不能", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["atomic-budget-before-first-private-input-or-related-feedback", 490, "首次泄露任何私有输入或数据相关反馈前，原子预留适用额度", 490, "预留", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["retry-failure-exit-time-size-gate-status-in-feedback-contract", 490, "均纳入预先批准的反馈合同", 490, "纳入", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["no-arbitrary-candidate-string-or-per-sample-debug-feedback", 490, "禁止输出任意候选字符串或逐样本调试材料", 490, "禁止", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["feedback-precision-errors-count-channel-bounded", 490, "释放的指标精度、错误类别、次数和通道应有界", 490, "应", "SHOULD", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["approved-feedback-only-no-zero-leakage-claim", 490, "只允许协议内反馈", 490, "只", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["developer-control-private-cache-logs-identity-data-separated", 490, "开发控制面与私有运行缓存/日志按身份及数据域分离", 490, "分离", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["incomplete-cleanup-no-runtime-reuse", 490, "清理不完整时不得复用运行环境", 490, "不得", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["eval-report-bounded-summary-ref-protocol-scorer-data-full-report-identity", 492, "补充协议/评分器/数据与完整报告的稳定身份及摘要", 492, "补充协议/评分器/数据与完整报告的稳定身份及摘要", "MUST", ["activity.eval_suite"], [484, 500]],
        ["reuse-existing-dataset-and-full-report-ref-no-synonymous-extra-fields", 492, "不机械新增同义 datasetRef/reportRef", 492, "不机械新增同义 datasetRef/reportRef", "MUST", ["activity.eval_suite"], [484, 500]],
        ["metrics-release-report-validity-unseen-qualification-distinct", 492, "指标达标、发布决定、报告有效性与未见声明资格分开", 492, "指标达标、发布决定、报告有效性与未见声明资格分开", "MUST", ["activity.eval_suite"], [484, 500]],
        ["pollution-append-disposition-original-evaluation-facts-retained", 492, "污染后追加处置，保留评测时点事实", 492, "污染后追加处置，保留评测时点事实", "MUST", ["activity.eval_suite"], [484, 500]],
        ["unknown-control-account-no-new-sealed-budget", 494, "新账号或不明控制关系先进入待核准状态，不能自动取得新的密封预算", 494, "不能", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["identity-migration-retains-budget-lineage", 494, "迁移身份保留原预算 lineage", 494, "保留", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["authorized-evidence-domain-only-approved-developer-feedback", 494, "开发域只能取得批准反馈", 494, "只能", "MUST", ["activity.eval_suite", "evaluation.sealed_claim"], [484, 500]],
        ["digest-existence-diagnostics-download-read-disclosure-boundary", 494, "数据摘要、对象存在性、诊断错误和下载接口均遵从 S13 的读取与披露边界", 494, "数据摘要、对象存在性、诊断错误和下载接口均遵从 S13 的读取与披露边界", "MUST", ["activity.eval_suite"], [484, 500]],
        ["isolation-budget-repeatable-score-not-statistical-dp-generalization", 496, "不能单独证明统计有效、差分隐私、样本未被间接用于选择或模型可泛化", 496, "不能", "MUST", ["activity.eval_suite"], [484, 500]],
        ["ordinary-test-data-no-fit-feature-preprocessing-tuning", 496, "普通测试集不得参与拟合、特征选择、预处理统计量估计及依结果调参", 496, "不得", "MUST", ["activity.eval_suite", "dataset.test_or_validation_use"], [484, 500]],
        ["crossvalidation-stateful-preprocessing-train-fold", 496, "交叉验证中的有状态预处理按获批划分在训练折内拟合", 496, "拟合", "MUST", ["activity.eval_suite", "evaluation.cross_validation"], [484, 500]],
        ["actual-time-subject-group-constraints", 496, "时间/主体分组约束由实际数据和声明决定", 496, "时间/主体分组约束由实际数据和声明决定", "MUST", ["activity.eval_suite"], [484, 500]],
        ["protocol-denominator-failure-timeout-missing-aggregation-repeat-claims-before-result", 498, "协议在结果产生前确定分母、失败/超时/缺样本处理、聚合、重复运行与允许声明", 498, "协议在结果产生前确定分母、失败/超时/缺样本处理、聚合、重复运行与允许声明", "MUST", ["activity.eval_suite"], [484, 500]],
        ["failed-samples-not-silently-removed", 498, "失败样本不能从指标分母中静默消失", 498, "不能", "MUST", ["activity.eval_suite"], [484, 500]],
        ["uncomputable-metric-explicit-status-no-fake-zero-or-pass", 498, "不用伪造零值或通过值占位", 498, "不用伪造零值或通过值占位", "MUST", ["activity.eval_suite"], [484, 500]],
        ["heldout-feedback-selected-candidate-not-independently-unseen", 498, "后续结果不能继续沿用“独立未见”标签", 498, "不能", "MUST", ["activity.eval_suite"], [484, 500]],
        ["ordinary-bounded-scoring-no-unimplemented-adaptive-guarantee", 498, "有限次数的普通评分不自动获得同等保证", 498, "有限次数的普通评分不自动获得同等保证", "MUST", ["activity.eval_suite"], [484, 500]],
        ["all-feedback-history-retained-claims-actual-exposure-protocol", 498, "已有反馈历史仍完整保留", 498, "已有反馈历史仍完整保留", "MUST", ["activity.eval_suite"], [484, 500]],
        ["real-iam-file-network-feedback-budget-enforced", 500, "实际 IAM/文件/网络/反馈/预算由评测部署执行", 500, "实际 IAM/文件/网络/反馈/预算由评测部署执行", "MUST", ["activity.eval_suite"], [484, 500]],
        ["static-tool-success-not-real-isolation", 500, "工具静态通过不替代真实隔离测试", 500, "工具静态通过不替代真实隔离测试", "MUST", ["activity.eval_suite"], [484, 500]],
        ["old-report-readable-no-new-sealed-evidence-no-qualification", 500, "缺失新证据不得取得密封资格", 500, "不得", "MUST", ["activity.eval_suite"], [484, 500]],
    )),
    dict(owner=EDITION_OWNERS[18], section=18, scope=[505, 521],
         sha256="a31c59a8f3778b6621102ea0f2b6a8a7fecbbbe1648ee30266e9aa7891b57b31", rows=(
        ["doc-status-enum-separate-change-task-execution", 505, "文档状态继续使用 `draft | active | frozen | deprecated`", 505, "文档状态继续使用 `draft | active | frozen | deprecated`", "MUST", None, [505, 521]],
        ["version-single-author-manifest-index-report-consistency", 505, "标准版次以 VERSION 为单一作者源", 505, "标准版次以 VERSION 为单一作者源", "MUST", None, [505, 521]],
        ["historic-version-fixtures-no-global-replacement", 505, "历史快照和 fixtures 中的旧版本保留，不全仓替换", 505, "历史快照和 fixtures 中的旧版本保留，不全仓替换", "MUST", None, [505, 521]],
        ["consumer-input-output-target-qualification-capabilities-separate", 507, "消费者能力、输入契约、输出契约、采用目标和合规资格分别声明", 507, "消费者能力、输入契约、输出契约、采用目标和合规资格分别声明", "MUST", None, [505, 521]],
        ["reader-before-writer-optional-not-reader-compatibility-proof", 507, "新 reader 先上线，新 writer 后启用", 507, "新 reader 先上线，新 writer 后启用", "MUST", None, [505, 521]],
        ["migration-retains-original-value-digest-source-gap-no-fabricated-evidence", 507, "不补造原本不存在的证据", 507, "不补造原本不存在的证据", "MUST", None, [505, 521]],
        ["protected-control-minimum-policy-tool-versions-no-worker-downgrade", 507, "不能由 Agent 编辑仓库降级", 507, "不能", "MUST", None, [505, 521]],
        ["format-read-compatibility-distinct-current-authority", 509, "格式兼容和当前安全授权分别判断", 509, "格式兼容和当前安全授权分别判断", "MUST", None, [505, 521]],
        ["supported-old-legal-format-original-semantics", 509, "支持窗口内的旧合法数据继续按其原义解析", 509, "支持窗口内的旧合法数据继续按其原义解析", "MUST", None, [505, 521]],
        ["revoked-vulnerable-old-executable-no-compatibility-authority", 509, "不得因兼容承诺重新获得受保护执行权限", 509, "不得", "MUST", None, [505, 521]],
        ["historic-diagnostic-input-no-weakened-new-control", 509, "不能迫使新目标放宽身份、解析资源限制或最低控制", 509, "不能", "MUST", None, [505, 521]],
        ["expected-content-check-and-replace-same-nonbypassable-boundary", 511, "预期内容检查与实际替换必须处于同一不可绕过的修改边界", 511, "必须", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["lock-journal-rename-not-external-writer-exclusion", 511, "工具内部锁、journal 和单次原子 rename 不足以排除仍可直接编辑目标的主体", 511, "不足以", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["inplace-proves-files-directory-open-writer-prepostimage-through-commit", 511, "须证明相关文件、目录项及已有写入能力均已纳入控制", 511, "须", "MUST", ["activity.inplace_migration"], [505, 521]],
        ["no-protected-write-boundary-only-new-candidate-diff-preserve-user", 511, "无法建立该边界时只输出新候选或差异，保留当前用户内容", 511, "只", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["readonly-business-analysis-bounded-separate-output-authority", 513, "明示的计划/诊断工件输出须另有有界写入权限", 513, "须", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["output-no-source-task-lock-policy-git-cache-user-overwrite", 513, "不得借输出路径覆盖源码、任务、锁/政策、Git 元数据、缓存或已有用户文件", 513, "不得", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["output-real-directory-object-identity-exclusive-safe-publication", 513, "输出目标先按真实目录与对象身份核对", 513, "先", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["invalid-output-no-executor-privilege-fallback", 513, "不能转用执行器权限兜底写入", 513, "不能", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["output-failure-no-apply-rollback-or-scan-denominator-change", 513, "工件生成失败不进入 apply/rollback", 513, "不进入", "MUST", ["activity.adoption_or_migration_tool"], [505, 521]],
        ["beta-target-separate-build-metadata-tag-prefix", 515, "Git tag的`v`前缀也不属于`standardVersion`值", 515, "Git tag的`v`前缀也不属于`standardVersion`值", "MUST", None, [505, 521]],
        ["beta-parsing-script-dispatch-image-lock-index-installer-test", 515, "脚本、schema dispatcher、镜像/锁、索引及安装器分别验证", 515, "脚本、schema dispatcher、镜像/锁、索引及安装器分别验证", "MUST", None, [505, 521]],
        ["gate-cadence-not-release-or-adoption-authority", 515, "既有gate cadence `pre_release`保留检查频率原义", 515, "既有gate cadence `pre_release`保留检查频率原义", "MUST", None, [505, 521]],
        ["standard-tool-protocol-channel-deployment-coordinates-independent", 517, "工具维持独立版本序列", 517, "工具维持独立版本序列", "MUST", None, [505, 521]],
        ["exact-target-artifact-support-matrix", 517, "支持矩阵绑定确切目标及制品摘要", 517, "支持矩阵绑定确切目标及制品摘要", "MUST", None, [505, 521]],
        ["each-new-duty-old-id-cli-schema-window-compatibility-decision", 517, "每项新义务、旧 ID/锚点、CLI/schema 改动和支持窗口均有兼容裁定", 517, "每项新义务、旧 ID/锚点、CLI/schema 改动和支持窗口均有兼容裁定", "MUST", None, [505, 521]],
        ["semver-public-breaking-contract-compatible-versioned-or-major", 517, "必须保留兼容接口/版本化新接口，或按该合同规则升级其主版本", 517, "必须", "MUST", ["change.public_semver_breaking"], [505, 521]],
        ["prerelease-name-no-existing-compatibility-promise-waiver", 517, "预发布标签和“新版版次”称谓不能免除已作出的兼容承诺", 517, "不能", "MUST", None, [505, 521]],
        ["public-version-policy-matches-compatibility-decision", 517, "DAS 正式版本策略及公开治理声明应与该裁定一致", 517, "应", "SHOULD", None, [505, 521]],
        ["controlled-update-origin-channel-matrix-closure-trust-update-generation", 519, "受控更新同时核对来源、获准渠道、标准/工具/协议支持矩阵、完整摘要闭包、信任状态及受保护更新代次", 519, "核对", "MUST", ["activity.release_activation"], [505, 521]],
        ["no-mixed-generation-replay-expired-release-activation", 519, "不能拼出新的有效激活", 519, "不能", "MUST", ["activity.release_activation"], [505, 521]],
        ["historic-offline-byte-proof-not-new-activation-authority", 519, "新激活需要当前授权", 519, "需要", "MUST", ["activity.release_activation"], [505, 521]],
        ["business-code-rollback-new-approved-activation-retains-security-history", 519, "不能回滚控制面历史", 519, "不能", "MUST", ["activity.release_activation"], [505, 521]],
        ["metadata-dispatch-reader-writer-downgrade-regressions", 521, "元数据生成检查、schema dispatcher、旧新读写测试和受治理防降级测试", 521, "元数据生成检查、schema dispatcher、旧新读写测试和受治理防降级测试", "MUST", None, [505, 521]],
        ["invalid-unknown-version-unsupported-explicit-failure", 521, "不静默规范化安全关键输入", 521, "不静默规范化安全关键输入", "MUST", None, [505, 521]],
    )),
)



# Reviewed edition semantics; these mappings preserve the normative author and
# its complete exceptions. The independent 1.4 baseline remains unchanged.
EDITION_COMPLETION_GROUPS += (
    dict(owner=EDITION_OWNERS[19], section=19, scope=[526, 546],
         sha256="38badb8570fbb9cbc26379d97e5fb08789f25b650a041e683b45f2a676e34624", rows=(
        ["offline-full-body-modules-schemas-fixtures-migration-coverage-view-package", 526, "标准包包含离线完整正文、模块目录、schema、fixtures、迁移映射、条款/规则/工具覆盖及可重复生成的完整视图", 526, "标准包包含离线完整正文、模块目录、schema、fixtures、迁移映射、条款/规则/工具覆盖及可重复生成的完整视图", "MUST", ["activity.standard_release"], [526, 546]],
        ["actual-executed-set-no-artificial-default-full-distinction", 526, "输出必须真实列出执行集合", 526, "必须", "MUST", ["activity.standard_release"], [526, 546]],
        ["formal-companion-standard-tool-full-matrix-reference-applicable-integration", 528, "标准自检、dasops/Cadence 自身完整测试、精确支持矩阵、最小参考部署及 A01–A32 适用联验", 528, "要求", "MUST", ["activity.standard_release", "release.official_companion"], [526, 546]],
        ["formal-standard-and-tool-support-joint-frozen-gates", 528, "必须共同满足冻结门槛", 528, "必须", "MUST", ["activity.standard_release", "release.formal_companion"], [526, 546]],
        ["specific-product-adoption-still-separate", 528, "任何具体产品仍须完成采用层验证", 528, "须", "MUST", ["activity.product_adoption"], [526, 546]],
        ["general-a30-incident-revocation-recovery-not-no-eval-na", 528, "不得按“没有评测”判为不适用", 528, "不得", "MUST", ["activity.standard_release", "release.official_companion"], [526, 546]],
        ["release-f-s-o-c-a-content-tool-deployment-adoption-denominators", 530, "区分规范内容、工具实现、参考部署和具体项目采用的分母", 530, "区分规范内容、工具实现、参考部署和具体项目采用的分母", "MUST", ["activity.standard_release"], [526, 546]],
        ["official-http-ui-sealed-support-samples-not-self-no-feature-waiver", 530, "不能让官方配套以自身无 HTTP/UI/密封业务为由跳过已冻结的契约消费与控制实现", 530, "不能", "MUST", ["activity.standard_release", "release.official_companion"], [526, 546]],
        ["minimal-domain-samples-no-full-business-platform-requirement", 530, "用最小受控 HTTP、UI 和密封评测样本证明各自承诺的支持", 530, "证明", "MUST", ["activity.standard_release", "release.official_companion"], [526, 546]],
        ["unsupported-combination-not-whole-frozen-capability-undelivered", 530, "不能替代整个冻结能力的交付", 530, "不能", "MUST", ["activity.standard_release", "release.official_companion"], [526, 546]],
        ["adoption-actor-artifact-deployment-target-facts-policy-scope-time-binding", 532, "正式采用结论须绑定采用主体、标准/工具精确制品、部署配置、受保护目标、事实/政策、适用范围和证据有效区间", 532, "须", "MUST", ["activity.product_adoption"], [526, 546]],
        ["adoption-qualified-scope-time-not-permanent-trust", 532, "不能形成永久可信标记", 532, "不能", "MUST", ["activity.product_adoption"], [526, 546]],
        ["control-affecting-drift-stops-related-actions-reanalysis-reverification", 532, "停止受影响动作", 532, "停止受影响动作", "MUST", {"op": "any", "args": [{"op": "fact", "key": "activity.product_adoption"}, {"op": "fact", "key": "activity.package_activation"}, {"op": "fact", "key": "activity.continued_operation"}]}, [526, 546]],
        ["every-new-action-current-authority", 532, "新的受保护动作仍逐次检查当前权威", 532, "新的受保护动作仍逐次检查当前权威", "MUST", ["activity.protected_action"], [526, 546]],
        ["production-gate-explicit-checks-supported-runtime-failure-propagation", 534, "安全与发布判定必须使用在支持运行模式下仍然生效的显式检查和失败传播", 534, "必须", "MUST", ["activity.standard_release"], [526, 546]],
        ["runtime-assert-debug-optimization-not-sole-security-gate", 534, "不能作为唯一授权/摘要/闭包门禁", 534, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["replace-runtime-asserts-explicit-failures", 534, "应改成明确条件与异常/非零退出", 534, "应", "SHOULD", ["activity.standard_release"], [526, 546]],
        ["governed-environment-optimization-injection-unsupported-args-negative-tests", 534, "覆盖优化模式、环境注入及未支持运行参数的反例", 534, "覆盖优化模式、环境注入及未支持运行参数的反例", "MUST", ["activity.standard_release"], [526, 546]],
        ["all-required-steps-report-artifacts-before-final-success", 536, "只有在全部所需子步骤结束、完整报告和必须工件写入成功后才产生最终成功", 536, "只有", "MUST", ["activity.standard_release"], [526, 546]],
        ["stage-log-no-premature-whole-chain-pass", 536, "不能提前输出易被消费为全链完成的 PASS", 536, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["wrapper-child-pipeline-report-write-failures-propagated", 536, "包装器正确传播子进程、管道和报告写入失败", 536, "包装器正确传播子进程、管道和报告写入失败", "MUST", ["activity.standard_release"], [526, 546]],
        ["report-consumer-actual-chain-not-console-pass-string", 536, "不能搜索控制台中的 PASS 字样决定发布", 536, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["candidate-content-read-distribute-independently-lifecycle-separate", 538, "标准内容可独立阅读、分发和验证", 538, "标准内容可独立阅读、分发和验证", "MUST", ["activity.standard_release"], [526, 546]],
        ["technical-neutrality-no-designated-product-dependency", 538, "不要求采用项目部署指定工具或业务产品才能理解/实现标准", 538, "不要求采用项目部署指定工具或业务产品才能理解/实现标准", "MUST", ["activity.standard_release"], [526, 546]],
        ["public-readme-matrix-release-governance-normative-consistency", 538, "保持与规范一致", 538, "保持与规范一致", "MUST", ["activity.standard_release"], [526, 546]],
        ["source-content-distributed-compressed-bytes-distinct", 540, "精确源码 revision、可重建内容及实际分发压缩包作为不同身份", 540, "精确源码 revision、可重建内容及实际分发压缩包作为不同身份", "MUST", ["activity.standard_release"], [526, 546]],
        ["immutable-release-asset-self-sealed-or-equivalent-byte-storage", 540, "不可变正式/预发布包应自行封存并作为固定资产分发", 540, "应", "SHOULD", ["activity.standard_release"], [526, 546]],
        ["auto-source-archive-url-not-permanent-compressed-byte-hash", 540, "不能仅凭其 commit URL 承诺同一压缩包 hash 永久可重取", 540, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["external-signature-proof-no-self-reference", 540, "附加签名和证明留在包外或按既有无自引用结构绑定", 540, "附加签名和证明留在包外或按既有无自引用结构绑定", "MUST", ["activity.standard_release"], [526, 546]],
        ["nonactive-stage-all-assets-download-byte-check-before-public", 542, "核对全部必需资产及其实际下载字节，再在受权入口完成可见发布", 542, "核对全部必需资产及其实际下载字节，再在受权入口完成可见发布", "MUST", ["activity.standard_release"], [526, 546]],
        ["immutable-release-attach-all-assets-before-publish", 542, "先附齐全部必需资产再发布", 542, "先附齐全部必需资产再发布", "MUST", ["activity.standard_release"], [526, 546]],
        ["postpublication-receipt-full-assets-no-missing-mixed-race", 542, "发布后读取平台回执和完整资产集合", 542, "发布后读取平台回执和完整资产集合", "MUST", ["activity.standard_release"], [526, 546]],
        ["unknown-release-same-action-reconcile-not-partial-success", 542, "不能把半包发布记为完整成功", 542, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["actual-digest-source-support-coverage-hard-stop-gate", 544, "发布入口核对实际工件摘要、来源、支持矩阵、测试覆盖和所有硬停止条件", 544, "发布入口核对实际工件摘要、来源、支持矩阵、测试覆盖和所有硬停止条件", "MUST", ["activity.standard_release"], [526, 546]],
        ["missing-gate-known-bypass-other-candidate-evidence-no-formal-ready", 544, "拒绝配套正式就绪", 544, "拒绝配套正式就绪", "MUST", ["activity.standard_release"], [526, 546]],
        ["formal-exact-verified-candidate-artifact-not-old-top-level-proof", 546, "不能直接把预发布包的顶层证明附到不同字节的正式包", 546, "不能", "MUST", ["activity.standard_release"], [526, 546]],
        ["version-packaging-new-top-digest-lock-manifest-signing-validation", 546, "纯版本/打包身份变化也需重新核对顶层摘要、锁、manifest 与签发", 546, "需", "MUST", ["activity.standard_release"], [526, 546]],
        ["no-package-own-final-compressed-digest-signature-selfcycle", 546, "发布签名不得要求包内嵌入其自身最终压缩包摘要", 546, "不得", "MUST", ["activity.standard_release"], [526, 546]],
    )),
    dict(owner=EDITION_OWNERS[21], section=21, scope=[597, 649],
         sha256="581854e0e131a10a2f144d6ecf5f643d40b8520740a695194e2cefb127938792", rows=(
        ["beta-positive-unpadded-increment-direct-ga-no-alpha-rc-required", 597, "N 为本项目从 1 开始递增的正整数", 597, "N 为本项目从 1 开始递增的正整数", "MUST", ["activity.standard_release"], [597, 649]],
        ["new-beta-only-needed-public-new-artifact", 597, "不为每次讨论、文档编辑或源码提交发版", 597, "不为每次讨论、文档编辑或源码提交发版", "MUST", ["activity.standard_release"], [597, 649]],
        ["planning-development-actual-release-identities-separated", 597, "方案、开发提交和实际发行分别识别", 597, "方案、开发提交和实际发行分别识别", "MUST", ["activity.standard_release"], [597, 649]],
        ["development-exact-source-build-contract-config-inputs-gap-record", 603, "每次受测源码、构建、合同及配置固定提交和摘要", 603, "每次受测源码、构建、合同及配置固定提交和摘要", "MUST", ["activity.standard_release"], [597, 649]],
        ["development-missing-minimum-controls-only-safe-isolated-or-readonly", 603, "缺少适用 Z01–Z12 的能力保持关闭", 603, "缺少适用 Z01–Z12 的能力保持关闭", "MUST", ["activity.standard_release"], [597, 649]],
        ["first-beta-frozen-semantics-contracts-implementations-all-present", 604, "F01–F11 的拟交付语义、试用交换合同与对应实现齐备", 604, "F01–F11 的拟交付语义、试用交换合同与对应实现齐备", "MUST", ["activity.standard_release"], [597, 649]],
        ["first-beta-three-component-reference-domains-runnable-no-hard-stop", 604, "三仓试用组合、开源参考执行链及最小领域样本可运行", 604, "三仓试用组合、开源参考执行链及最小领域样本可运行", "MUST", ["activity.standard_release"], [597, 649]],
        ["first-beta-enabled-path-control-admission-no-formal-exit-claim", 604, "尚未完成正式试用退出不能声明正式配套就绪", 604, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["necessary-beta-fix-compatibility-migration-rollback-reuse-decisions", 605, "修复范围、兼容影响、迁移/回退及证据复用已经判定", 605, "判定", "MUST", ["activity.standard_release", "activity.beta_package_update"], [597, 649]],
        ["necessary-beta-new-package-full-affected-tests-admission", 605, "新包完整自检、受影响测试和准入批准完成", 605, "完成", "MUST", ["activity.standard_release", "activity.beta_package_update"], [597, 649]],
        ["necessary-beta-install-activation-separate-no-history-reset", 605, "新编号不能自动清除事故、预算、待核对动作或证据缺口", 605, "不能", "MUST", ["activity.standard_release", "activity.beta_package_update"], [597, 649]],
        ["formal-all-gates-applicable-acceptance-trial-final-compatibility-artifact-approval", 606, "本版全部正式门槛、适用 A01–A32、三仓及参考部署、试用退出、最终兼容裁定、最终包核验和独立发布批准完成", 606, "完成", "MUST", ["activity.standard_release", "activity.formal_release"], [597, 649]],
        ["formal-version-no-permanent-action-trust", 606, "正式号不授予永久信任", 606, "不授予", "MUST", ["activity.standard_release", "activity.formal_release"], [597, 649]],
        ["unimplemented-beta-not-supported-no-prerelease-acceptance-substitution", 608, "不得通过 beta 名称把未实现能力标为已支持", 608, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["explicit-channel-choice-no-auto-14-migration", 610, "预发布渠道由有权主体显式选择", 610, "预发布渠道由有权主体显式选择", "MUST", ["activity.standard_release"], [597, 649]],
        ["semver-beta-numeric-prerelease-order-no-string-or-strip", 610, "不得按普通字符串排序或删除后缀", 610, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["build-metadata-not-prerelease-precedence", 610, "`+beta.1` 是构建元数据，不能表达相同的预发布优先级", 610, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["version-precedence-package-range-resource-authority-distinct", 610, "版本优先级、包管理器匹配范围和资源授权分别判断", 610, "版本优先级、包管理器匹配范围和资源授权分别判断", "MUST", ["activity.standard_release"], [597, 649]],
        ["protected-exact-target-source-package-matrix-protocol-current-trust", 610, "受保护入口核对获批目标、源码、实际包摘要、支持矩阵、协议及当前信任", 610, "受保护入口核对获批目标、源码、实际包摘要、支持矩阵、协议及当前信任", "MUST", ["activity.standard_release"], [597, 649]],
        ["future-beta-not-supported-by-same-core-prefix", 610, "不能仅凭共同 `1.5.0` 前缀接受", 610, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["published-coordinate-package-manifest-tag-immutable", 612, "同一精确坐标不得换字节", 612, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["same-byte-mirror-retransmit-idempotent", 612, "相同字节的重传/镜像可以按幂等规则核对", 612, "相同字节的重传/镜像可以按幂等规则核对", "MUST", ["activity.standard_release", "activity.release_retransmission"], [597, 649]],
        ["public-fix-next-unused-beta-number-original-package-event-retained", 612, "保留原包与原始事件", 612, "保留原包与原始事件", "MUST", ["activity.standard_release"], [597, 649]],
        ["failed-revoked-published-beta-number-not-reused", 612, "失败或撤销的已发布编号不重复使用", 612, "失败或撤销的已发布编号不重复使用", "MUST", ["activity.standard_release"], [597, 649]],
        ["unpublished-development-revision-not-published-object-overwrite", 612, "不能借相同版本字符串覆盖任何已发布对象", 612, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["beta-reader-writer-contract-deployment-storage-support-declared", 614, "逐次明确 reader、writer、schema/协议、部署及存储支持关系", 614, "逐次明确 reader、writer、schema/协议、部署及存储支持关系", "MUST", ["activity.standard_release"], [597, 649]],
        ["beta-name-no-compatibility-promise-waiver-same-schema-meaning-stable", 614, "禁止同 schema identity 改义", 614, "禁止", "MUST", ["activity.standard_release"], [597, 649]],
        ["upgrade-new-artifact-migration-before-protected-switch", 614, "升级先核验新制品及迁移计划，再在受保护边界切换", 614, "升级先核验新制品及迁移计划，再在受保护边界切换", "MUST", ["activity.standard_release"], [597, 649]],
        ["state-upgrade-transaction-backup-recovery", 614, "状态库采用 S13 的事务、备份及恢复要求", 614, "状态库采用 S13 的事务、备份及恢复要求", "MUST", ["activity.standard_release"], [597, 649]],
        ["code-rollback-no-revocation-budget-dedup-completion-audit-rollback", 614, "代码回退不能回滚授权撤销、预算、业务动作去重、Completion 或审计历史", 614, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["unreadable-new-state-approved-forward-recovery-not-old-writer", 614, "不强开旧 writer", 614, "不强开旧 writer", "MUST", ["activity.standard_release"], [597, 649]],
        ["standard-tool-protocol-deployment-versions-independent", 616, "两者允许不同编号，不要求三个仓库同时递增", 616, "两者允许不同编号，不要求三个仓库同时递增", "MUST", ["activity.standard_release"], [597, 649]],
        ["ecosystem-normal-package-version-vs-das-approved-semver-target", 616, "工具包使用其生态的规范化合法版本", 616, "工具包使用其生态的规范化合法版本", "MUST", ["activity.standard_release"], [597, 649]],
        ["exact-version-digest-matrix-not-parser-success-authority", 616, "不能把包解析成功等同于标准支持或受保护授权", 616, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["semver-build-metadata-not-pep440-local-comparison", 616, "不得直接套用到 PEP 440 的 local version 比较", 616, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["trial-existing-task-plan-deployment-no-parallel-approval-system", 620, "不新增平行审批系统", 620, "不新增", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-denominator-preapproved-changes-retain-original-failures-impact", 620, "在结果产生前批准验收分母", 620, "批准", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-exact-beta-source-components-protocol-runtime-config-policy-subject-resource", 624, "本次 beta 号或明确未发布修订、源码/内容摘要、三仓制品及协议、运行库/适配器、系统配置、政策、试用主体和资源/数据范围", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-general-chain-minimal-domains-adoption-applicability-counting", 625, "通用受保护执行链及配套最小 HTTP/UI/密封样本", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-prior-window-load-concurrency-fault-recovery-defect-performance", 626, "事先确定观察窗口、有效负载、并发、故障及恢复场景、可接受非安全缺陷和性能范围", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-upgrade-activation-consumers-state-rollback-revoke-conflict-crash-backup-owners", 627, "必要 beta 间安装/激活、旧新消费者、状态迁移、代码回退、撤销、目标竞争、进程/系统故障和备份核对", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-original-runs-failures-incidents-na-fixes-retest-reuse-disclosure", 628, "原始运行、候选/计划身份、失败/重试/事故、N/A批准、修复、受影响重验及旧证据复用映射", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-hard-stop-unknown-impact-denial-independent-continue-release-approval", 629, "影响未明阻断相关资格", 622, "必须", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["trial-exit-real-coverage-not-idle-days", 631, "无反馈、长期未修改或一次绿色 CI 均不能单独满足条件", 631, "不能", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["formal-observation-coverage-all-must-compatibility-migration-recovery-no-hard-stop", 631, "转正式同时要求观察条件和实际覆盖完成、全部适用强制验收通过、兼容/迁移/恢复证据有效、硬停止问题关闭", 631, "要求", "MUST", ["activity.standard_release", "activity.formal_release"], [597, 649]],
        ["trial-fix-config-impact-analysis-reuse-unknown-no-reuse", 633, "关系不明时不复用", 633, "不复用", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["changed-security-failure-runtime-version-adapter-negative-positive-recovery-observation", 633, "重新覆盖有关拒绝测试、正向对照、恢复及观察", 633, "覆盖", "MUST", ["activity.standard_release", "activity.beta_trial"], [597, 649]],
        ["different-implementation-green-subsets-not-one-qualified-deployment", 633, "不得把多个不同实现各自通过的子集拼成从未共同验收过的最终部署", 633, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["formal-new-immutable-identity-final-input-output-tool-deployment-check", 637, "正式 `1.5.0` 形成新的不可变发布身份", 637, "形成", "MUST", ["activity.standard_release", "activity.formal_release"], [597, 649]],
        ["reuse-only-unchanged-valid-approved-original-subartifact", 637, "只有未变且仍符合批准计划、来源和有效期的子工件证据可复用", 637, "只有", "MUST", ["activity.standard_release"], [597, 649]],
        ["final-version-manifest-index-lock-signature-install-meta-recheck-top-proof", 637, "重新核对最终包闭包和顶层证据", 637, "重新核对最终包闭包和顶层证据", "MUST", ["activity.standard_release"], [597, 649]],
        ["different-byte-beta-top-signature-not-formal-proof", 637, "不能将某个 beta 包的顶层签名附给不同字节", 637, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-metadata-standard-channel-revision-digest-status-signing-basis", 639, "发布元数据记录标准目标、渠道、源码 revision、工具/内容摘要、状态和签发依据", 639, "发布元数据记录标准目标、渠道、源码 revision、工具/内容摘要、状态和签发依据", "MUST", ["activity.standard_release"], [597, 649]],
        ["external-append-actual-publication-receipt-sealed-package-target-platform", 639, "实际发布事件由包外追加的受保护回执记录", 639, "实际发布事件由包外追加的受保护回执记录", "MUST", ["activity.standard_release"], [597, 649]],
        ["no-posthoc-package-time-rewrite", 639, "不得事后回写包内时间改变已验证字节", 639, "不得", "MUST", ["activity.standard_release"], [597, 649]],
        ["releasedat-old-contract-date-vs-external-event", 639, "新映射区分包内日期声明和包外实际事件", 639, "新映射区分包内日期声明和包外实际事件", "MUST", ["activity.standard_release"], [597, 649]],
        ["planned-commit-source-date-epoch-not-actual-receipt-time", 639, "不能填作实际发布回执时间", 639, "不能", "MUST", ["activity.standard_release"], [597, 649]],
        ["display-prerelease-latest-title-not-formal-identity", 641, "取消预发布勾选不产生正式 `1.5.0`", 641, "取消预发布勾选不产生正式 `1.5.0`", "MUST", ["activity.standard_release"], [597, 649]],
        ["incident-announcement-not-package-tag-original-receipt-change", 641, "受权事故公告不改变已发布包、tag绑定或原始回执", 641, "受权事故公告不改变已发布包、tag绑定或原始回执", "MUST", ["activity.standard_release"], [597, 649]],
        ["download-install-activation-separate-history-not-new-adoption", 641, "下载、安装和激活分别验收", 641, "下载、安装和激活分别验收", "MUST", ["activity.standard_release"], [597, 649]],
        ["incident-business-rollback-retains-security-floor-and-ledger", 641, "事故处置和业务回退保留当前安全下界及历史账本", 641, "事故处置和业务回退保留当前安全下界及历史账本", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-first-approved-exact-target-channel-matrix-allocation-compatibility-admission", 645, "拒绝 Agent 擅自改目标", 645, "拒绝 Agent 擅自改目标", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-second-final-artifact-source-deps-components-current-trust-no-mixed-beta", 646, "禁止跨 beta 混装", 646, "禁止", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-third-plan-real-slots-runs-valid-reuse-trial-hard-stop", 647, "未运行保持 `not_run`", 647, "未运行保持 `not_run`", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-fourth-current-identity-authority-budget-generation-durable-intent", 648, "重新校验发布身份、授权、预算、目标代次和持久化意图", 648, "重新校验发布身份、授权、预算、目标代次和持久化意图", "MUST", ["activity.standard_release"], [597, 649]],
        ["release-stage-assets-public-stable-business-keys-readback-receipt", 648, "发布后回读完整工件并追加实际回执", 648, "发布后回读完整工件并追加实际回执", "MUST", ["activity.standard_release"], [597, 649]],
        ["unknown-release-original-action-no-new-key-resend", 648, "不换键重发", 648, "不换键重发", "MUST", ["activity.standard_release"], [597, 649]],
        ["project-final-package-real-deployment-limited-adoption-continued-current-controls", 649, "具体项目核对最终包与自身真实部署后取得限定采用结论", 649, "具体项目核对最终包与自身真实部署后取得限定采用结论", "MUST", ["activity.product_adoption"], [597, 649]],
    )),
)


def reviewed_completion_requirements(root):
    """Preserve the complete task/shared-contract contexts and actual event scope."""
    source = 'modules/edition-1.5.md'
    lines = local_file(root, source).read_text(encoding='utf-8').splitlines()

    def reference(first, last, phrase=None):
        if not 1 <= first <= last <= len(lines):
            raise ValueError('reviewed fragment range is outside its source')
        text = '\n'.join(lines[first - 1:last])
        start = 0 if phrase is None else text.index(phrase)
        selected = text if phrase is None else phrase
        return dict(path=source, startLine=first, endLine=last,
                    startColumn=start, endColumn=start + len(selected),
                    textSha256=hashlib.sha256(selected.encode('utf-8')).hexdigest())

    preapproval = [i for i, line in enumerate(lines, 1) if line == EDITION_PREAPPROVAL]
    if len(preapproval) != 1:
        raise ValueError('completion controls lost the original preapproval qualifier')
    result = []
    for group in EDITION_COMPLETION_GROUPS:
        first, last = group['scope']
        body = '\n'.join(lines[first - 1:last]) + '\n'
        if hashlib.sha256(body.encode('utf-8')).hexdigest() != group['sha256']:
            raise ValueError('task/shared-contract normative body or legal exception changed')
        for criterion, number, phrase, force_line, force, strength, keys, scope in group['rows']:
            section, owner = group['section'], group['owner']
            activation = edition_activation(keys if keys is None or isinstance(keys, dict)
                                            else keys[0] if len(keys) == 1 else keys)
            if criterion == 'audit-unknown-storage-not-file-visibility-as-success-or-absence':
                activation = dict(op='any', args=[dict(op='fact', key=key) for key in keys])
            result.append(dict(id=f'{owner}.s{section}.{criterion}', ownerModule=owner,
                               parentClause=f'cl-13.{section}', controlId=f'S{section:02}',
                               strength=strength, criterion=criterion,
                               activation=activation,
                               contextRefs=[reference(*scope), reference(preapproval[0], preapproval[0])],
                               strengthRef=reference(force_line, force_line, force),
                               bodyRefs=[reference(number, number, phrase)]))
    return result



def edition_activation(keys):
    if isinstance(keys, dict):
        return deepcopy(keys)
    if keys is None:
        return {'op': 'const', 'value': True}
    if isinstance(keys, str):
        return {'op': 'fact', 'key': keys}
    return {'op': 'all', 'args': [{'op': 'fact', 'key': key} for key in keys]}


def legacy_activation(applicability):
    """Translate the preserved textual conditions, without defaulting facts."""
    if applicability == 'each-ai-task-or-pr':
        return {'op': 'fact', 'key': 'activity.ai_task_or_pr'}
    if applicability == 'when-contract-changes-are-needed':
        return {'op': 'fact', 'key': 'change.contract_needed'}
    if applicability == 'breaking-contract-change-in-ai-task-or-pr':
        return {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'activity.ai_task_or_pr'},
            {'op': 'fact', 'key': 'change.contract_breaking'},
        ]}
    raise ValueError('unsupported preserved applicability')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate decoded catalog key")
        result[key] = value
    return result


def load(path):
    return standard_io.loads(path.read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def local_file(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("unsafe artifact reference")
    target = root / relative
    for parent in (target, *target.parents):
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise ValueError("symlink artifact reference")
    if not target.is_file():
        raise ValueError(f"missing module artifact: {relative}")
    return target


def catalog_schema(root, relative):
    schema = load(local_file(root, relative))
    if schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema':
        raise ValueError('unsupported catalog schema dialect')
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            for keyword in ('$ref', '$dynamicRef'):
                reference = value.get(keyword)
                if reference is not None and (not isinstance(reference, str) or not reference.startswith('#/')):
                    raise ValueError('catalog schema references must stay in the locked local schema')
            if '$vocabulary' in value:
                raise ValueError('catalog profile does not accept undeclared vocabulary changes')
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=4)
def requirement_structure_check(schema_bytes):
    """Cache successful leaf checks under the exact parsed schema content.

    Source/provenance/denominator validation still runs on every call. Each
    record is checked with the original item schema and its original $defs;
    the root keeps all array and cross-field constraints. Changed schema or
    record content creates a new key. Failed checks are never cached.
    """
    schema = standard_io.loads(schema_bytes)
    groups = ('requirements', 'editionRequirements')
    # Retain the original validator for schema features whose evaluation scope
    # cannot be split into the root and independent array elements.
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if (any(key in value for key in ('$dynamicRef', '$anchor', '$dynamicAnchor', 'prefixItems'))
                    or ('$id' in value and value is not schema)
                    or ('$ref' in value and not value['$ref'].startswith('#/$defs/'))):
                return Draft202012Validator(schema).validate
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    if any('items' not in schema['properties'][group] for group in groups):
        return Draft202012Validator(schema).validate
    root_schema = deepcopy(schema)
    for group in groups:
        root_schema['properties'][group]['items'] = {}
    root_validator = Draft202012Validator(root_schema)
    item_validator = Draft202012Validator(schema)
    item_validators = {group: item_validator.evolve(schema=schema['properties'][group]['items']) for group in groups}

    @lru_cache(maxsize=8192)
    def check_item(group, raw):
        for error in item_validators[group].iter_errors(standard_io.loads(raw)):
            raise error

    def check(value):
        root_validator.validate(value)
        for group in groups:
            for item in value[group]:
                check_item(group, json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    return check


def source_fragment(root, reference):
    lines = local_file(root, reference['path']).read_text(encoding='utf-8').splitlines()
    first, last, start, end = (reference[name] for name in ('startLine', 'endLine', 'startColumn', 'endColumn'))
    if any(type(value) is not int for value in (first, last, start, end)) or not 1 <= first <= last <= len(lines):
        raise ValueError('invalid requirement source line range')
    text = '\n'.join(lines[first - 1:last])
    if not 0 <= start < end <= len(text):
        raise ValueError('invalid requirement source column range')
    text = text[start:end]
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != reference['textSha256']:
        raise ValueError('requirement source fragment differs from its normative author')
    return text


def repeated_initial_task_context(root, identity):
    """Repeat Appendix E provenance without duplicating the original task IDs."""
    if identity not in (
            'das.security-agent.ai-task.repo-scope',
            'das.security-agent.ai-task.verification-commands'):
        return []
    path = 'appendices/appendix-e-multi-repo-contract-driven-standard.md'
    text = '\n'.join(local_file(root, path).read_text().splitlines()[639:672])
    return [dict(path=path, startLine=640, endLine=672, startColumn=0,
                 endColumn=len(text), textSha256=hashlib.sha256(text.encode()).hexdigest())]


def validate_requirements(catalog, baseline, root):
    leaves = load(local_file(root, 'standard_requirements.json'))
    schema = catalog_schema(root, 'standard_requirements.schema.json')
    requirement_structure_check(json.dumps(schema, sort_keys=True, separators=(',', ':')))(leaves)
    if (leaves['standardVersion'] != catalog['standardVersion']
            or leaves['baselineSha256'] != catalog['baselineSha256']):
        raise ValueError('requirement catalog version or independent baseline differs')
    profiles = {leaf['id']: leaf for leaf in reviewed_legacy_requirements(root, baseline)}
    expected_units = {'legacy-text-de7276bb-0144', 'legacy-text-de7276bb-0145'} | {
        leaf['legacyUnitId'] for leaf in profiles.values()}
    expected_units |= {'legacy-minimum-de7276bb-10-2-' + name for name in MINIMUM_ALIASES}
    expected_units |= {unit_id for unit_id, _ in PLAYBOOK_ALIASES}
    if (set(leaves['mappedLegacyUnitIds']) != expected_units or leaves['qualificationEligible'] is not False
            or leaves['migrationStage'] != 'complete-leaf-mapping'):
        raise ValueError('complete leaf mapping must preserve its independent denominator and remain unqualified')
    units = legacy_units(root, baseline)
    modules = {item['id']: item for item in catalog['modules']}
    for leaf in leaves['requirements'] + leaves['editionRequirements']:
        references = [leaf['strengthRef'], *leaf['bodyRefs'],
                      *leaf.get('conditionRefs', []), *leaf.get('contextRefs', [])]
        if any(reference['path'] not in modules[leaf['ownerModule']]['normativeSources']
               for reference in references):
            raise ValueError('requirement body has no declared normative author: ' + leaf['id'])
    expected = {}
    for criterion, line, phrase in LEGACY_LEAVES:
        task = line != 1875
        identity = 'das.security-agent.' + ('ai-task.' if task else 'cross-repo.') + criterion
        expected[identity] = (criterion, line, phrase, task)
    seen, seen_profiles = set(), set()
    for leaf in leaves['requirements']:
        identity = leaf['id']
        if identity in profiles:
            if identity in seen_profiles or leaf != profiles[identity]:
                raise ValueError('reviewed leaf strength, scope, condition or source mapping changed')
            owner = modules[leaf['ownerModule']]
            if leaf['legacyUnitId'] not in owner['legacyUnitIds'] or leaf['parentClause'] not in owner['clauseIds']:
                raise ValueError('reviewed leaf has a different normative owner or missing registered parent')
            seen_profiles.add(identity)
            continue
        if identity not in expected or identity in seen:
            raise ValueError('unknown or duplicate stable requirement ID')
        seen.add(identity)
        criterion, line, phrase, task = expected[identity]
        applicability = ('breaking-contract-change-in-ai-task-or-pr' if criterion == 'breaking-compatibility-plan'
                         else 'each-ai-task-or-pr' if task else 'when-contract-changes-are-needed')
        unit_id = 'legacy-text-de7276bb-' + ('0144' if task else '0145')
        unit = units[unit_id]
        module = modules['das.security-agent']
        if (leaf['ownerModule'] != module['id'] or leaf['legacyUnitId'] != unit_id
                or unit_id not in module['legacyUnitIds'] or leaf['parentClause'] != unit['parentClause']
                or leaf['strength'] != 'MUST' or leaf['criterion'] != criterion
                or leaf['applicability'] != applicability
                or leaf['activation'] != legacy_activation(applicability)):
            raise ValueError('legacy requirement ownership, strength, condition or parent changed')
        references = [*leaf['conditionRefs'], *leaf['contextRefs'], leaf['strengthRef'], *leaf['bodyRefs']]
        texts = [source_fragment(root, reference) for reference in references]
        condition, force, statement = texts[0], texts[-2], texts[-1]
        lines = local_file(root, unit['source']).read_text().splitlines()
        # Fix the source ranges as well as text. An equal phrase in a different
        # scope is not proof of this requirement's applicability.
        def span(reference, first, last=None, selected=None, prefix=False):
            last = first if last is None else last
            original = '\n'.join(lines[first - 1:last])
            start = 0 if selected is None else original.index(selected)
            end = len(original) if selected is None else start + len(selected)
            if prefix:
                end = original.index('documented')
            if (reference['path'], reference['startLine'], reference['endLine'], reference['startColumn'], reference['endColumn']) != (
                    unit['source'], first, last, start, end):
                raise ValueError('requirement fragment moved outside its original semantic scope')
        span(leaf['conditionRefs'][0], 1857 if task else 1867)
        span(leaf['strengthRef'], 1857 if task else 1875, prefix=not task)
        span(leaf['bodyRefs'][0], line, selected=phrase)
        repeated = repeated_initial_task_context(root, identity)
        if leaf['contextRefs'][1:] != repeated:
            raise ValueError('initial task repeated provenance changed')
        if task:
            if len(leaf['contextRefs']) != 1 + len(repeated):
                raise ValueError('AI task leaf lost its field context')
            span(leaf['contextRefs'][0], line)
            if criterion == 'breaking-compatibility-plan':
                if len(leaf['conditionRefs']) != 2:
                    raise ValueError('compatibility plan lost its breaking-change condition')
                span(leaf['conditionRefs'][1], 1860, selected='if breaking')
            elif len(leaf['conditionRefs']) != 1:
                raise ValueError('unconditional AI task requirement acquired an extra condition')
            if (condition != unit['text'] or force != unit['text']
                    or statement != (lines[line - 1] if phrase is None else phrase)):
                raise ValueError('AI task leaf lost its required field or normative carrier')
        else:
            if len(leaf['conditionRefs']) != 1 or len(leaf['contextRefs']) != 1:
                raise ValueError('sequencing requirement acquired or lost a condition/context')
            span(leaf['contextRefs'][0], 1869, 1873)
            if (condition != lines[1866] or texts[1] != '\n'.join(lines[1868:1873])
                    or force != unit['text'][:unit['text'].index('documented')] or statement != phrase):
                raise ValueError('sequencing leaf lost its condition, sequence or mandatory effect')
    if seen != set(expected):
        raise ValueError('independent legacy requirement denominator is incomplete')
    if seen_profiles != set(profiles):
        raise ValueError('independent profile requirement denominator is incomplete')
    edition = local_file(root, 'modules/edition-1.5.md').read_text().splitlines()
    expected_edition = {f'das.security-agent.{control.lower()}.{criterion}': (criterion, control, phrase, key)
                        for criterion, control, phrase, key in EDITION_LEAVES}
    seen = set()
    force = '规范性表格中的强制结果亦为 MUST。'
    force_lines = [i for i, line in enumerate(edition, 1) if force in line]
    if len(force_lines) != 1:
        raise ValueError('edition table lost its single mandatory strength carrier')
    preapproval_lines = [i for i, line in enumerate(edition, 1) if line == EDITION_PREAPPROVAL]
    if len(preapproval_lines) != 1:
        raise ValueError('edition controls lost their preapproval qualifier')
    storage_body = '\n'.join(edition[351:376]) + '\n'
    if hashlib.sha256(storage_body.encode('utf-8')).hexdigest() != EDITION_STORAGE_SHA256:
        raise ValueError('S13 storage normative context or exception changed during extraction')
    expected_storage = {f'das.security-agent.s13.storage.{item[0]}': item for item in EDITION_STORAGE_LEAVES}
    control_body = '\n'.join(edition[337:350]) + '\n'
    if hashlib.sha256(control_body.encode('utf-8')).hexdigest() != EDITION_CONTROL_SHA256:
        raise ValueError('S13 control normative context or exception changed during extraction')
    expected_control = {f'das.security-agent.s13.control.{item[0]}': item for item in EDITION_CONTROL_LEAVES}
    storage_seen = set()
    control_seen = set()
    expected_completion = {leaf['id']: leaf for leaf in reviewed_completion_requirements(root)}
    completion_seen = set()
    for leaf in leaves['editionRequirements']:
        identity = leaf['id']
        if identity in expected_completion:
            if identity in completion_seen or leaf != expected_completion[identity]:
                raise ValueError('task/shared-contract leaf condition, force, source or identity changed')
            owner = modules[leaf['ownerModule']]
            if leaf['parentClause'] not in owner['clauseIds']:
                raise ValueError('task/shared-contract leaf lost its normative owner or parent')
            completion_seen.add(identity)
            continue
        if identity in expected_storage or identity in expected_control:
            group = 'storage' if identity in expected_storage else 'control'
            expected_prose = expected_storage if group == 'storage' else expected_control
            prose_seen = storage_seen if group == 'storage' else control_seen
            if identity in prose_seen:
                raise ValueError(f'duplicate S13 {group} requirement ID')
            prose_seen.add(identity)
            criterion, number, phrase, force_phrase, strength, keys, context = expected_prose[identity]
            if (leaf['criterion'], leaf['controlId'], leaf['parentClause'], leaf['ownerModule'], leaf['strength'], leaf['activation']) != (
                    criterion, 'S13', 'cl-13.13', 'das.security-agent', strength, edition_activation(keys)):
                raise ValueError(f'S13 {group} condition, ownership, strength or parent changed')
            if len(leaf['bodyRefs']) != 1 or len(leaf['contextRefs']) != 2:
                raise ValueError(f'S13 {group} lost its body or complete qualifier context')
            body = edition[number - 1]
            context_text = '\n'.join(edition[context[0] - 1:context[1]])
            references = (
                (leaf['bodyRefs'][0], number, number, phrase, body.index(phrase, body.index(force_phrase) if group == 'control' else 0)),
                (leaf['strengthRef'], number, number, force_phrase, body.index(force_phrase)),
                (leaf['contextRefs'][0], *context, context_text, 0),
                (leaf['contextRefs'][1], preapproval_lines[0], preapproval_lines[0], EDITION_PREAPPROVAL, 0),
            )
            for ref, first, last, text, start in references:
                if (ref['path'], ref['startLine'], ref['endLine'], ref['startColumn'], ref['endColumn']) != (
                        'modules/edition-1.5.md', first, last, start, start + len(text)):
                    raise ValueError(f'S13 {group} fragment moved outside its normative scope')
                if source_fragment(root, ref) != text:
                    raise ValueError(f'S13 {group} lost its source body, force or context')
            continue
        if identity in seen or identity not in expected_edition:
            raise ValueError('unknown or duplicate edition requirement ID')
        seen.add(identity)
        criterion, control, phrase, key = expected_edition[identity]
        activation = edition_activation(key)
        if (leaf['criterion'], leaf['controlId'], leaf['parentClause'], leaf['ownerModule'], leaf['strength'], leaf['activation']) != (
                criterion, control, 'cl-13.13', 'das.security-agent', 'MUST', activation):
            raise ValueError('edition requirement condition, ownership, strength or parent changed')
        rows = [(i, line) for i, line in enumerate(edition, 1) if line.startswith(f'| {control} |')]
        if len(rows) != 1:
            raise ValueError('edition control has no unique normative row')
        number, row = rows[0]
        statement = row.split('|')[2].strip()
        if statement != EDITION_CONTROL_RESULTS[control]:
            raise ValueError('edition control result changed during leaf extraction')
        # Search only the mandatory result cell. E.g. 动作 also occurs in the
        # Z04 introductory scope; the selected criterion is the recheck item.
        phrases = (phrase,) if isinstance(phrase, str) else phrase
        if len(leaf['bodyRefs']) != len(phrases) or len(leaf['contextRefs']) != 2:
            raise ValueError('edition requirement lost its scoped result or preapproval context')
        references = [
                (leaf['contextRefs'][0], number, row, 0),
                (leaf['contextRefs'][1], preapproval_lines[0], EDITION_PREAPPROVAL, 0),
                (leaf['strengthRef'], force_lines[0], force, edition[force_lines[0] - 1].index(force)),
        ]
        for ref, selected in zip(leaf['bodyRefs'], phrases):
            start = row.index(statement) + statement.index(selected, statement.index('重新校验') + 4
                                                           if criterion == 'action-recheck' else 0)
            references.append((ref, number, selected, start))
        for ref, line_number, text, column in references:
            if (ref['path'], ref['startLine'], ref['endLine'], ref['startColumn'], ref['endColumn']) != (
                    'modules/edition-1.5.md', line_number, line_number, column, column + len(text)):
                raise ValueError('edition requirement moved outside its normative context')
            if source_fragment(root, ref) != text:
                raise ValueError('edition requirement lost its normative result or strength')
    if seen != set(expected_edition):
        raise ValueError('reviewed edition leaf denominator is incomplete')
    if storage_seen != set(expected_storage):
        raise ValueError('reviewed S13 storage denominator is incomplete')
    if control_seen != set(expected_control):
        raise ValueError('reviewed S13 control denominator is incomplete')
    if completion_seen != set(expected_completion):
        raise ValueError('reviewed task/shared-contract denominator is incomplete')
    rows = [line for line in edition if any(line.startswith(f'| {control} |') for control in EDITION_CONTROL_RESULTS)]
    if hashlib.sha256(('\n'.join(rows) + '\n').encode('utf-8')).hexdigest() != EDITION_TABLE_SHA256:
        raise ValueError('edition control enforcement or required evidence changed during leaf extraction')
    required = {'standard_requirements.json', 'standard_requirements.schema.json', 'modules/requirements.md'}
    if not required <= set(modules['das.security-agent']['requiredArtifactRefs']):
        raise ValueError('requirement catalog or generated view omitted from its module closure')
    return leaves


def validate(catalog, baseline, root=ROOT):
    Draft202012Validator(catalog_schema(root, "standard_modules.schema.json")).validate(catalog)
    baseline_bytes = local_file(root, 'migration/legacy_normative_baseline.json').read_bytes()
    baseline_sha256 = hashlib.sha256(baseline_bytes).hexdigest()
    if baseline_sha256 != LEGACY_BASELINE_SHA256:
        raise ValueError('independent baseline differs from the reviewed pre-migration input')
    if baseline != standard_io.loads(baseline_bytes):
        raise ValueError('independent baseline object differs from its pinned file')
    if baseline.get("schemaVersion") != "1.0.0" or baseline.get("kind") != "das-legacy-normative-baseline":
        raise ValueError("wrong baseline identity")
    if catalog["baselineSha256"] != baseline_sha256:
        raise ValueError("independent baseline bytes changed")
    if catalog["standardVersion"] != (root / "VERSION").read_text().strip():
        raise ValueError("module version differs from Standard VERSION")
    modules = {module["id"]: module for module in catalog["modules"]}
    if len(modules) != len(catalog["modules"]) or set(modules) != MODULE_IDS:
        raise ValueError("duplicate or missing standard module")
    manifest = load(root / "standard_manifest.json")
    for path in [source['path'] for source in baseline['sources']] + ['templates/prompts/generate_master_doc_from_PRD.md']:
        bindings = edition_metadata(root, path)
        if bindings:
            lines = local_file(root, path).read_text().splitlines()
            if any(index >= len(lines) or lines[index] != current for index, (current, _) in bindings.items()):
                raise ValueError('current governing/template edition metadata differs: ' + path)
    if baseline["conditionalRequirements"] != manifest["conditionalRequirements"]:
        raise ValueError("legacy conditional obligation changed before migration")
    original_sources = {source['path']: legacy_source(root, source) for source in baseline['sources']}
    # Whole old Markdown sources use their immutable byte pins. The manifest's
    # version/inventory evolve; only its independently pinned original rules
    # above belong to this semantic comparison, not the new release metadata.
    original_sources['standard_manifest.json'] = local_file(root, 'standard_manifest.json').read_text()
    units = legacy_units(root, baseline)
    for unit in units.values():
        lines = original_sources[unit['source']].splitlines()
        body = "\n".join(lines[unit["startLine"] - 1:unit["endLine"]])
        if body != unit["text"] or hashlib.sha256(body.encode()).hexdigest() != unit["textSha256"]:
            raise ValueError("baseline unit differs from its independent normative body")
    owners = {}
    clauses = {item["id"] for item in load(root / "clause_index.json")["clauses"]}
    registry = load(root / 'ids/standard_ids.json')
    # A parent is navigation, not a new obligation. Existing appendix/root IDs
    # cover original text which had no numbered clause; old IDs are untouched.
    clauses |= set(registry['appendixIds']) | {'C-001'} & set(registry['clauseIds'])
    for module in catalog["modules"]:
        if module["effect"] != "normative":
            raise ValueError("legacy normative obligation moved to informative effect")
        if not set(module["clauseIds"]) <= clauses:
            raise ValueError("unknown navigation clause")
        sources = set(module["normativeSources"])
        for relative in sources | set(module["requiredArtifactRefs"]):
            local_file(root, relative)
        for unit in module["legacyUnitIds"]:
            if unit not in units or unit in owners:
                raise ValueError("unknown or multiply owned normative unit")
            if units[unit]["source"] not in sources:
                raise ValueError("unit body omitted from module sources")
            owners[unit] = module["id"]
    if set(owners) != set(units):
        raise ValueError("independent normative units missing from catalog")
    visiting, visited = set(), set()

    def visit(module):
        if module in visiting:
            raise ValueError("module dependency cycle")
        if module in visited:
            return
        if module not in modules:
            raise ValueError("unknown module dependency")
        visiting.add(module)
        for dependency in modules[module]["dependsOn"]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in modules:
        visit(module)
    if "das.interaction.standard-ui" not in modules["das.interaction.hfvi"]["dependsOn"]:
        raise ValueError("HFVI omits applicable Standard UI dependency")
    expected = {rule["ruleId"]: (index, rule) for index, rule in enumerate(baseline["conditionalRequirements"])}
    seen = set()
    for mapping in catalog["conditionalMappings"]:
        rule = mapping["ruleId"]
        if rule not in expected or rule in seen or mapping["ownerModule"] not in modules:
            raise ValueError("conditional mapping missing, duplicate, or unknown")
        index, body = expected[rule]
        if mapping["authorRef"] != f"standard_manifest.json#/conditionalRequirements/{index}" or mapping["authorSha256"] != digest(body):
            raise ValueError("conditional rule has competing author or altered semantics")
        seen.add(rule)
    if seen != set(expected):
        raise ValueError("legacy conditional mapping incomplete")
    validate_requirements(catalog, baseline, root)
    edition = local_file(root, 'modules/edition-1.5.md').read_text()
    numbers = [int(number) for number in re.findall(r'^### 13\.([0-9]+) ', edition, re.M)]
    if numbers != list(range(1, 22)) or 'Effect: **normative**' not in edition:
        raise ValueError('missing, duplicate or reordered normative edition section')
    if set(EDITION_OWNERS) != set(range(1, 22)):
        raise ValueError('edition ownership denominator must cover every section 1 through 21')
    for number, owner in EDITION_OWNERS.items():
        clause = f'cl-13.{number}'
        assigned = [module['id'] for module in catalog['modules'] if clause in module['clauseIds']]
        if assigned != [owner] or 'modules/edition-1.5.md' not in modules[owner]['normativeSources']:
            raise ValueError('edition section omitted or assigned to a second normative owner')
    required = set(manifest['requiredArtifacts'])
    for module in catalog['modules']:
        if not set(module['normativeSources'] + module['requiredArtifactRefs']) <= required:
            raise ValueError('module author or artifact omitted from Standard release closure')
    acceptance = local_file(root, 'modules/acceptance-1.5.md').read_text()
    cases = re.findall(r'^\|\s+(A[0-9]{2}\.[0-9]+)\s*\|', acceptance, re.M)
    expected_cases = [f'A{family:02d}.{case}' for family, count in enumerate(ACCEPTANCE_COUNTS, 1)
                      for case in range(1, count + 1)]
    if cases != expected_cases:
        raise ValueError('edition acceptance denominator missing or duplicated')
    candidate = manifest['extensions'].get('contentCandidate', {})
    if (manifest['extensions'].get('qualificationEligible') is not False
            or candidate.get('qualificationEligible') is not False
            or candidate.get('publicationStatus') != 'unpublished'
            or candidate.get('lifecycle') != 'draft'):
        raise ValueError('unfinished content migration cannot confer beta qualification')


def render_views(catalog, baseline, root=ROOT):
    units = legacy_units(root, baseline)
    leaves = load(root / 'standard_requirements.json')
    lines = ["# Standard Module navigation", "", "Generated by tools/validate_modules.py. The original normative body remains authoritative.", "", "[1.5 additions](edition-1.5.md) and [136 acceptance obligations](acceptance-1.5.md) are normative authors; Chapter 13 is a generated reading view. This content candidate is unpublished and does not confer qualification.", "", "Legacy text units preserve paragraphs and their context; the complete mapped leaf catalog remains unqualified.", "", f"[Requirement migration](requirements.md): {len(leaves['requirements'])} legacy obligations and {len(leaves['editionRequirements'])} edition obligations. Mapping completion does not certify implementation or deployment.", ""]
    for module in sorted(catalog["modules"], key=lambda item: item["id"]):
        lines.extend([f"## {module['id']} — {module['title']}", "", f"Effect: {module['effect']}; lifecycle: {module['status']}.", ""])
        for source in module["normativeSources"]:
            lines.append(f"- [{source}](../{source})")
        lines.extend(["", f"Legacy text units: {len(module['legacyUnitIds'])}.", ""])
    index = {"schemaVersion": "1.0.0", "standardVersion": catalog["standardVersion"], "kind": "das-module-navigation", "qualificationEligible": False,
             "units": [{"id": unit, "ownerModule": module["id"], "source": units[unit]["source"], "parentClause": units[unit]["parentClause"], "textSha256": units[unit]["textSha256"]}
                       for module in sorted(catalog["modules"], key=lambda item: item["id"]) for unit in module["legacyUnitIds"]]}
    reading = ['# Legacy requirement leaf migration', '',
               'Generated by tools/validate_modules.py from standard_requirements.json and its original normative source fragments.', '',
               f"This is a complete mapping of {len(leaves['mappedLegacyUnitIds'])} legacy carriers into {len(leaves['requirements'])} separately scoped requirements. It does not add or weaken an obligation, certify a runtime implementation, or confer qualification.", '',
               'Fragment columns are zero-based Unicode scalar offsets in the joined source lines; end offsets are exclusive. Source remains the single normative body author.', '']
    contexts = {}

    def scope_links(references):
        links = []
        for ref in references:
            key = json.dumps(ref, sort_keys=True)
            if key not in contexts:
                contexts[key] = (f'requirement-context-{len(contexts) + 1:03}', ref)
            anchor, _ = contexts[key]
            links.append(f"[{ref['path']}:{ref['startLine']}–{ref['endLine']}](#{anchor})")
        return ', '.join(dict.fromkeys(links))

    for leaf in leaves['requirements']:
        reading.extend([f"## {leaf['id']}", '',
            f"Owner: `{leaf['ownerModule']}`; parent: `{leaf['parentClause']}`; strength: **{leaf['strength']}**; criterion: `{leaf['criterion']}`.", '',
            'Applicability: ' + scope_links(leaf['conditionRefs']), ''])
        reading.extend(['Activation: `' + json.dumps(leaf['activation'], sort_keys=True, separators=(',', ':')) + '`.', ''])
        reading.extend(['Context and exceptions: ' + scope_links(leaf['contextRefs']), ''])
        reading.extend([source_fragment(root, leaf['strengthRef']).strip() + ' ' + ' '.join(source_fragment(root, ref).strip() for ref in leaf['bodyRefs']), '',
                        '[Normative source](../' + units[leaf['legacyUnitId']]['source'] + '); legacy unit: `' + leaf['legacyUnitId'] + '`.', ''])
    reading.extend(['# Edition requirement leaves', '',
        f"The {len(leaves['editionRequirements'])} leaves below map existing Z01–Z12 results and all S01–S21 sections, without adding obligations. Full source contexts preserve scope, enforcement, evidence and exceptions. The original S13 connection constraint proof remains SHOULD; SQLite-specific mandatory behavior retains its actual SQLite condition. Legacy and edition leaf mapping is complete; full product acceptance is not complete. Mapping coverage alone does not establish consumer correctness or qualification.", '',
        'Activation expresses when an obligation applies, not whether its checks passed. Missing facts stay unknown; conflicting sources remain conflict. A false preview result is an unapproved applicability proposal, not an authorized exemption.', '',
        'Z02 approval duties and Z12 provenance/safe-stop duties always apply. Other positive predicates describe actual protected requests (including denied attempts), Agent/Worker participation, untrusted execution, verification, integration, completion and output. They do not describe permission or successful checks, and cannot be set false to avoid a configured path. A Worker activity includes editing/reading, not just executing candidate code. External bindings apply when external material is necessary; missing necessity facts remain unknown. Agent-authored tests and integration competition/rebase/changed merge results retain their specific conditions. The legacy breaking plan retains its AI-task and breaking-impact conditions.', '',
        EDITION_PREAPPROVAL, ''])
    for leaf in leaves['editionRequirements']:
        reading.extend([f"## {leaf['id']}", '',
            f"Owner: `{leaf['ownerModule']}`; parent: `{leaf['parentClause']}`; control: `{leaf['controlId']}`; strength: **{leaf['strength']}**.", '',
            'Activation: `' + json.dumps(leaf['activation'], sort_keys=True, separators=(',', ':')) + '`.', '',
            'Criterion: ' + ' / '.join(source_fragment(root, ref) for ref in leaf['bodyRefs']), '',
            'Context and exceptions: ' + scope_links(leaf['contextRefs']), '',
            '[Normative author](edition-1.5.md#' + ({'S20': 'shared-contracts', 'S21': 'release-lifecycle'}.get(leaf['controlId'], 's' + leaf['controlId'][1:].zfill(2)) if leaf['controlId'].startswith('S') else 's13') + ').', ''])
    reading.extend(['# Shared normative source scopes', '',
                    'Each leaf links to its full original conditions and exceptions below. Shared scopes are rendered once; they are not replaced by the shorter criterion or activation expression.', ''])
    for anchor, ref in contexts.values():
        scope_text = source_fragment(root, ref).replace('](#', '](../' + ref['path'] + '#')
        # Preserve Markdown's explicit hard break without introducing trailing
        # whitespace in generated files. The pinned source/reference is intact.
        scope_text = re.sub(r' {2}$', r'\\', scope_text, flags=re.M)
        reading.extend([f'<a id="{anchor}"></a>', f"## {ref['path']}:{ref['startLine']}–{ref['endLine']}", '',
                        f"Normative scope: [{ref['path']}](../{ref['path']}); Unicode offsets {ref['startColumn']}–{ref['endColumn']}.", '',
                        scope_text, ''])
    original_sources = {source['path']: legacy_source(root, source) for source in baseline['sources']}
    version = catalog['standardVersion']
    date = load(root / 'standard_manifest.json')['releasedAt']
    spec = original_sources['SPECIFICATION.md'].splitlines(keepends=True)
    spec[4] = f'[![Version: v{version}](https://img.shields.io/badge/Version-v{version}-blue.svg)](CHANGELOG.md)\n'
    spec[9] = f'**Last updated:** {date}\n'
    edition = (root / 'modules/edition-1.5.md').read_text()
    edition = edition.split('\n', 1)[1].lstrip().replace('](../', '](')
    edition = edition.replace('](acceptance-1.5.md', '](modules/acceptance-1.5.md')
    appendix = (root / 'modules/acceptance-1.5.md').read_text().split('\n', 1)[1].lstrip()
    appendix = appendix.replace('](../', '](')
    appendix = appendix.replace('](edition-1.5.md', '](modules/edition-1.5.md')
    appendix = re.sub(r'^(#{2,3}) ', r'##\1 ', appendix, flags=re.M)
    full = ''.join(spec) + EDITION_MARKER + '\n<a id="edition-1-5"></a>\n## 13. Edition 1.5 normative additions\n\n'
    full += 'Generated view. Edit modules/edition-1.5.md and modules/acceptance-1.5.md; never edit this tail independently.\n\n' + edition
    full += '\n#### Edition acceptance obligations (generated)\n\n' + appendix
    context = original_sources['DAS_STANDARD_CONTEXT_PACK.md'].splitlines(keepends=True)
    context[0] = f'# DAS Standard Context Pack (v{version})\n'
    context[7] = f'- Last updated: {date}\n'
    context[8] = f'- Scope: Read-optimized quick reference for humans and AI agents working from the DAS v{version} content candidate.\n'
    summary = '\n## 10. Edition 1.5 adoption and limitations\n\n'
    summary += 'The normative additions are authored in [modules/edition-1.5.md](modules/edition-1.5.md), with a generated Chapter 13 in [SPECIFICATION.md](SPECIFICATION.md#edition-1-5).\n\n'
    summary += 'Approved facts, three-valued applicability, bounded exact contracts, current resource authorization, isolated verification, immutable candidates, actual integration and evidence-backed completion govern the applicable paths. HTTP, UI and sealed evaluation obligations follow actual capabilities, including mixed surfaces.\n\n'
    summary += 'This is an unpublished content candidate with complete legacy and edition leaf mapping. Mapping and source checks do not qualify beta, activate protected tools or authorize publication. The 136 product cases remain not_run until protected execution evidence is available. Final compatibility decisions, complete applicable exchange and consumer evidence, and installed deployment qualification remain required.\n'
    return {"modules/README.md": "\n".join(lines), "modules/navigation.json": json.dumps(index, ensure_ascii=False, indent=2)+"\n",
            'modules/requirements.md': '\n'.join(reading), 'SPECIFICATION.md': full,
            'DAS_STANDARD_CONTEXT_PACK.md': ''.join(context) + CONTEXT_MARKER + summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = load(ROOT / "standard_modules.json")
    baseline = load(ROOT / "migration/legacy_normative_baseline.json")
    validate(catalog, baseline)
    views = render_views(catalog, baseline)
    if not args.check:
        standard_io.preflight_outputs([ROOT / relative for relative in views])
    for relative, rendered in views.items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_text() != rendered:
                raise SystemExit(f"stale generated module view: {relative}")
        else:
            standard_io.write_text(path, rendered)
    print(f"modules: {len(catalog['modules'])} logical modules; {len(baseline['units'])} legacy text units preserved")


if __name__ == "__main__":
    main()
