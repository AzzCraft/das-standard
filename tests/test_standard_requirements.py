"""Preserve original conditions while splitting real legacy obligations."""
from copy import deepcopy
import importlib.util
import hashlib
import json
import re
from pathlib import Path
import shutil

from jsonschema import ValidationError
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('requirement_validator', ROOT / 'tools/validate_modules.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def inputs(root=ROOT):
    return validator.load(root / 'standard_modules.json'), validator.load(root / 'migration/legacy_normative_baseline.json')


def test_download_install_activation_is_a_product_event():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    leaf = next(x for x in leaves['editionRequirements'] if x['criterion'] == 'download-install-activation-separate-history-not-new-adoption')
    assert leaf['activation'] == {'op': 'any', 'args': [
        {'op': 'fact', 'key': 'activity.product_adoption'},
        {'op': 'fact', 'key': 'activity.package_activation'}]}
    assert leaf['strength'] == 'MUST'


def test_deployment_mapping_retains_profile_subset_and_selected_strategy():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    deployment = {leaf['criterion']: leaf for leaf in leaves['requirements']
                  if leaf['id'].startswith('das.governance.verification-release.deployment.')}
    assert len(deployment) == 122
    for leaf in deployment.values():
        assert leaf['parentClause'] == 'C-001'
        assert len(leaf['conditionRefs']) == len(leaf['contextRefs']) == 2
        assert 'Pure libraries or research-only repos MAY adopt a reduced subset' in validator.source_fragment(ROOT, leaf['contextRefs'][1])
    matrix = deployment['environment-matrix-owner']['activation']
    assert matrix == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.deployment_governance'},
        {'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}]}
    assert deployment['same-artifact-promotion']['strength'] == 'SHOULD'
    assert deployment['chosen-per-env-rebuild-reproducible']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.deployment_governance'},
        {'op': 'fact', 'key': 'build.rebuild_per_environment'}]}
    assert 'Rebuild-per-env MAY be used if required by policy' in validator.source_fragment(ROOT, deployment['chosen-per-env-rebuild-reproducible']['contextRefs'][0])
    assert deployment['provider-one-lawful-fallback']['strength'] == 'SHOULD'
    assert 'or partial offline behavior' in validator.source_fragment(ROOT, deployment['provider-one-lawful-fallback']['contextRefs'][0])
    assert deployment['production-no-floating-image']['strength'] == 'MUST'
    assert validator.source_fragment(ROOT, deployment['production-no-floating-image']['strengthRef']) == 'MUST NOT'
    assert {f'legacy-text-16280e97-{n:04}' for n in range(1, 37)} <= set(leaves['mappedLegacyUnitIds'])
    old = {leaf['id']: leaf for leaf in leaves['requirements']}
    for identity in ('das.core.principles.keyword-synonym-interpretation',
                     'das.security-agent.operational.no-secrets-in-source',
                     'das.governance.verification-release.platform.dependency-and-tool-locks'):
        assert any(ref['path'] == 'DAS_DEPLOYMENT_ADDENDUM.md' for ref in old[identity]['contextRefs'])
        assert all(ref['path'] != 'DAS_DEPLOYMENT_ADDENDUM.md' for ref in old[identity]['conditionRefs'])


def test_deployment_policy_must_is_distinct_from_explicit_l2_mechanisms():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if '.deployment.' in leaf['id']}
    for name in ('time-to-fix-gating', 'severity', 'blocking-severities', 'waiver-expiry'):
        leaf = mapped['vulnerability-policy-' + name]
        assert leaf['strength'] == 'MUST'
        assert leaf['activation'] == {'op': 'fact', 'key': 'activity.deployment_governance'}
        assert validator.source_fragment(ROOT, leaf['strengthRef']) == 'MUST'
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert 'required for L2' in context
        assert 'The project MUST define a vulnerability policy' in context
    for name in ('l2-production-sbom', 'l2-ci-direct-transitive-sca', 'l2-deployment-signature-check'):
        leaf = mapped[name]
        assert {'op': 'fact', 'key': 'profile.l2'} in leaf['activation']['args']
        assert leaf['strength'] == 'MUST'


@pytest.mark.parametrize('fault', ['lose-profile', 'force-same-artifact', 'hide-until-failure',
                                 'drop-library-subset', 'weaken-prohibition', 'fake-clause'])
def test_deployment_mapping_rejects_changed_scope_or_force(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if '.deployment.' in leaf['id']}
    if fault == 'lose-profile': mapped['environment-matrix-owner']['activation']['args'].pop()
    elif fault == 'force-same-artifact': mapped['same-artifact-promotion']['strength'] = 'MUST'
    elif fault == 'hide-until-failure': mapped['secret-leak-incident-rotation-remediation']['activation'] = {'op':'fact', 'key':'permission.rotation_allowed'}
    elif fault == 'drop-library-subset': mapped['runbook-deploy']['contextRefs'].pop()
    elif fault == 'weaken-prohibition': mapped['production-no-floating-image']['strength'] = 'SHOULD'
    else: mapped['runbook-deploy']['parentClause'] = 'cl-14.1'
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(*inputs(bundle), bundle)


def test_manifest_conditions_are_executable_original_leaves_not_only_provenance():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    rules = validator.load(ROOT / 'migration/legacy_normative_baseline.json')['conditionalRequirements']
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if '.manifest-rule.' in leaf['id']}
    assert set(mapped) == {rule['ruleId'].replace('_', '-') for rule in rules}
    assert len(mapped) == 10
    for rule in rules:
        leaf = mapped[rule['ruleId'].replace('_', '-')]
        assert leaf['strength'] == 'MUST'
        assert json.loads(validator.source_fragment(ROOT, leaf['contextRefs'][0])) == rule
        assert json.loads(validator.source_fragment(ROOT, leaf['bodyRefs'][0])) == rule['requires']
        assert json.loads(validator.source_fragment(ROOT, leaf['conditionRefs'][0])) == rule['appliesTo']
        assert validator.source_fragment(ROOT, leaf['strengthRef']) == '"requires"'
    headless = mapped['headless-master-doc-requires-headless-surface-note']
    assert 'maps back to core doc type' in rule_text(ROOT, headless)
    assert 'UI_SPEC = N/A' in rule_text(ROOT, headless)


def rule_text(root, leaf):
    return ' '.join(validator.source_fragment(root, ref) for ref in leaf['bodyRefs'])


@pytest.mark.parametrize('fault', ['omit-leaf', 'grant-gated', 'project-profile',
                                 'role-value', 'owner-coedit', 'condition-coedit', 'source-gap'])
def test_manifest_rule_mapping_cannot_drop_scope_values_or_competing_author(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    row = next(row for row in leaves['requirements'] if row['criterion'] ==
               'l2-master-doc-requires-context-pack')
    if fault == 'omit-leaf': leaves['requirements'].remove(row)
    elif fault == 'grant-gated': row['activation'] = {'op': 'fact', 'key': 'permission.adoption_allowed'}
    elif fault == 'project-profile': row['activation']['args'][1]['key'] = 'profile.l2'
    elif fault in ('role-value', 'condition-coedit'):
        manifest = validator.load(bundle / 'standard_manifest.json')
        if fault == 'role-value':
            rule = next(rule for rule in manifest['conditionalRequirements'] if rule['ruleId'] ==
                        'master_doc_requires_canonical_entrypoint_role')
            rule['requires']['metadataValues']['Doc family role'] = ['subordinate_doc']
        else: manifest['conditionalRequirements'][0]['appliesTo']['conformanceProfiles'] = ['L0']
        (bundle / 'standard_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    elif fault == 'owner-coedit':
        catalog['conditionalMappings'][0]['ownerModule'] = 'das.core'
        (bundle / 'standard_modules.json').write_text(json.dumps(catalog) + '\n')
        row['ownerModule'] = 'das.core'
        row['id'] = 'das.core.manifest-rule.' + row['criterion']
    else:
        module = next(module for module in catalog['modules'] if module['id'] == row['ownerModule'])
        module['normativeSources'].remove('standard_manifest.json')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_all_edition_sections_have_owned_scoped_rules_without_qualifying_partial_migration():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    sections = {leaf['parentClause'] for leaf in leaves['editionRequirements']}
    assert sections == {'cl-13.' + str(n) for n in range(1, 22)}
    assert leaves['migrationStage'] == 'complete-leaf-mapping'
    assert leaves['qualificationEligible'] is False
    by_id = {leaf['id']: leaf for leaf in leaves['editionRequirements']}
    assert by_id['das.core.s2.independent-fact-approval-before-evaluation']['activation'] == {'op':'const','value':True}
    assert by_id['das.contracts-compatibility.s5.sse-native-framing-no-eof-event']['activation'] == {
        'op':'all','args':[{'op':'fact','key':key} for key in ('activity.text_delta_transport','transport.sse')]}
    assert by_id['das.interaction.standard-ui.s16.navigation-purpose-consistent']['strength'] == 'SHOULD'
    assert by_id['das.governance.verification-release.s19.replace-runtime-asserts-explicit-failures']['strength'] == 'SHOULD'
    assert by_id['das.interaction.standard-ui.s16.complete-authorized-reading']['activation'] == {
        'op':'any','args':[{'op':'fact','key':key} for key in ('surface.ui','surface.hfvi')]}
    for identity, terms in (
            ('das.contracts-compatibility.s15.raw-framing-independent-final-effect-observation', ('本条约束所用入口','不要求建立新HTTP服务器','正常分块','连接复用')),
            ('das.interaction.standard-ui.s16.modal-focus-keyboard-approved-behavior', ('非模态抽屉','不强制焦点陷阱','实际模态行为')),
            ('das.ai-runtime-evaluation.s17.sealed-candidate-and-scoring-domain-separated', ('公开评分公式无需一概保密','不宣称可自动识别','普通测试集')),
            ('das.governance.verification-release.s21.trial-exit-real-coverage-not-idle-days', ('不规定统一试用天数','后续 beta 不构成必经次数','不换键重发'))):
        context = validator.source_fragment(ROOT, by_id[identity]['contextRefs'][0])
        assert all(term in context for term in terms)


def test_collaboration_and_visual_companions_preserve_optional_advice_and_authority_boundaries():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    collaboration = {leaf['criterion']: leaf for leaf in leaves['requirements'] if '.collaboration.' in leaf['id']}
    assert len(collaboration) == 72
    for leaf in collaboration.values():
        assert 'multiple people' in validator.source_fragment(ROOT, leaf['contextRefs'][1])
        assert 'security/compliance wins' in validator.source_fragment(ROOT, leaf['contextRefs'][1])
    assert collaboration['high-impact-or-contentious-rfc']['strength'] == 'SHOULD'
    assert collaboration['program-approval-matrix']['strength'] == 'SHOULD'
    assert collaboration['break-glass-limited-to-sev1-sev2']['activation'] == {'op':'all', 'args':[
        {'op':'fact', 'key':'activity.multiparty_document_governance'},
        {'op':'fact', 'key':'activity.break_glass_change'}]}
    assert 'next business day' in validator.source_fragment(ROOT, collaboration['deferred-gates-24h-or-next-business-day']['bodyRefs'][0])
    assert 'Slow gates MAY be deferred' in validator.source_fragment(ROOT, collaboration['regulated-break-glass-required-compliance-no-bypass']['contextRefs'][0])
    ui = 'das.interaction.standard-ui.ui.'
    hfvi = 'das.interaction.hfvi.hfvi.'
    assert by_id[ui+'ambiguous-behavior-prototype-link']['activation']['args'][-1]['key'] == 'ui.behavior_ambiguous_in_words'
    assert by_id[ui+'boundary-workflow-contract-map']['activation']['args'][-1]['key'] == 'workflow.crosses_boundary'
    assert all(by_id[hfvi+'vis-header-'+field]['strength'] == 'SHOULD' for field in (
        'doc-id', 'owner', 'status', 'governing-standard', 'updated', 'scope', 'parent-master-doc', 'interaction-profile'))
    assert by_id[hfvi+'scene-frame-budget']['strength'] == 'SHOULD'
    assert any(ref['path'].endswith('appendix-d-ui-spec-appendix-template.md') for ref in by_id[ui+'repair-ux']['contextRefs'])
    assert by_id[ui+'repair-ux']['strength'] == 'SHOULD'
    assert not any(leaf['id'].startswith(ui+'repair-state-') or leaf['id'].startswith(ui+'confirmation-state-') for leaf in leaves['requirements'])


@pytest.mark.parametrize('fault', ['severity-as-permission', 'weaken-independent-review',
                                 'force-rfc', 'omit-compliance-precedence', 'strengthen-vis-advice'])
def test_companion_scope_and_advice_cannot_be_rewritten(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    prefix = 'das.governance.verification-release.collaboration.'
    if fault == 'severity-as-permission': by_id[prefix+'break-glass-limited-to-sev1-sev2']['activation'] = {'op':'fact', 'key':'permission.break_glass_allowed'}
    elif fault == 'weaken-independent-review': by_id[prefix+'break-glass-independent-senior-review']['strength'] = 'SHOULD'
    elif fault == 'force-rfc': by_id[prefix+'high-impact-or-contentious-rfc']['strength'] = 'MUST'
    elif fault == 'omit-compliance-precedence': by_id[prefix+'regulated-break-glass-required-compliance-no-bypass']['contextRefs'].pop()
    else: by_id['das.interaction.hfvi.hfvi.vis-header-parent-master-doc']['strength'] = 'MUST'
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['omit-section', 'hide-build-until-verification',
                                 'hide-issuance-until-consumption', 'force-sse',
                                 'force-ui-on-headless', 'strengthen-advice', 'unowned-s19'])
def test_complete_section_mapping_cannot_omit_paths_or_strengthen_choices(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['editionRequirements']}
    if fault == 'omit-section':
        leaves['editionRequirements'] = [leaf for leaf in leaves['editionRequirements']
                                         if leaf['parentClause'] != 'cl-13.19']
    elif fault == 'hide-build-until-verification':
        by_id['das.security-agent.s11.candidate-domain-distinct-protected-test-observer']['activation'] = {
            'op':'fact', 'key':'activity.verification'}
    elif fault == 'hide-issuance-until-consumption':
        by_id['das.security-agent.s12.independent-signature-complete-plan-original-run-and-aggregation']['activation'] = {
            'op':'fact', 'key':'activity.evidence_consumption'}
    elif fault == 'force-sse':
        by_id['das.contracts-compatibility.s5.sse-native-framing-no-eof-event']['activation']['args'].pop()
    elif fault == 'force-ui-on-headless':
        by_id['das.interaction.standard-ui.s16.complete-authorized-reading']['activation'] = {
            'op':'const', 'value':True}
    elif fault == 'strengthen-advice':
        by_id['das.interaction.standard-ui.s16.navigation-purpose-consistent']['strength'] = 'MUST'
    else:
        for module in catalog['modules']:
            if module['id'] == 'das.governance.verification-release':
                module['clauseIds'].remove('cl-13.19')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


@pytest.mark.parametrize('fault', ['unknown-field', 'missing-force', 'invalid-expression',
                                 'nonedition-source', 'zero-body', 'too-many-bodies',
                                 'missing-qualifier', 'cross-section-id', 'wrong-owner',
                                 'wrong-clause', 'unknown-criterion'])
def test_edition_schema_common_constraints_still_reject_invalid_native_objects(fault):
    schema = validator.load(ROOT / 'standard_requirements.schema.json')
    schema['properties'] = {'leaf': schema['properties']['editionRequirements']['items']}
    schema['required'] = ['leaf']
    leaf = deepcopy(next(leaf for leaf in validator.load(ROOT / 'standard_requirements.json')['editionRequirements']
                         if leaf['id'] == 'das.interaction.standard-ui.s16.complete-authorized-reading'))
    if fault == 'unknown-field': leaf['qualificationEligible'] = True
    elif fault == 'missing-force': del leaf['strengthRef']
    elif fault == 'invalid-expression': leaf['activation'] = {'op':'allow', 'value':True}
    elif fault == 'nonedition-source': leaf['bodyRefs'][0]['path'] = 'SPECIFICATION.md'
    elif fault == 'zero-body': leaf['bodyRefs'] = []
    elif fault == 'too-many-bodies': leaf['bodyRefs'] *= 2
    elif fault == 'missing-qualifier': leaf['contextRefs'].pop()
    elif fault == 'cross-section-id': leaf['id'] = 'das.interaction.standard-ui.s15.complete-authorized-reading'
    elif fault == 'wrong-owner': leaf['ownerModule'] = 'das.core'
    elif fault == 'wrong-clause': leaf['parentClause'] = 'cl-13.15'
    else: leaf['criterion'] = 'unreviewed-advice'
    with pytest.raises(ValidationError):
        validator.Draft202012Validator(schema).validate({'leaf':leaf})


def test_remaining_audit_storage_prose_preserves_actual_failure_and_independent_stop_paths():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    audit = {leaf['criterion']: leaf for leaf in leaves['editionRequirements']
             if leaf['id'].startswith('das.security-agent.s13.audit-')}
    assert len(audit) == 61
    assert {leaf['strength'] for leaf in audit.values()} == {'MUST'}
    assert audit['audit-service-failure-stops-normal-write']['activation'] == {
        'op': 'fact', 'key': 'activity.authoritative_write'}
    assert audit['audit-independent-preapproved-local-stop']['activation'] == {
        'op': 'fact', 'key': 'activity.protected_local_stop'}
    for criterion, terms in (
            ('audit-independent-preapproved-local-stop', ('不以先成功写入', '新的业务授权', '不包含扩大权限')),
            ('audit-protected-read-authentication', ('公开资料', '经批准完整披露', '不统一要求')),
            ('audit-actual-loaded-engine-driver-config-source-fix-proof', ('实际加载', '宿主命令行版本', '修复依据')),
            ('audit-retry-confirmed-rollback-current-full-logic', ('确认事务回滚', '重算完整事务逻辑', '不能只重放', '长时间网络请求'))):
        context = validator.source_fragment(ROOT, audit[criterion]['contextRefs'][0])
        assert all(term in context for term in terms)
    assert audit['audit-sqlite-actual-nonnull-foreign-key-conflicts']['activation']['args'][-1]['key'] == 'storage.sqlite_reference'
    assert audit['audit-unknown-storage-not-file-visibility-as-success-or-absence']['activation'] == {
        'op': 'any', 'args': [{'op': 'fact', 'key': key} for key in
                            ('activity.artifact_registration', 'activity.artifact_recovery')]}


@pytest.mark.parametrize('fault', ['drop-intent', 'failure-claim-hides-path', 'permission-hides-stop',
                                 'force-sqlite', 'registration-and-recovery', 'erase-data-boundary'])
def test_audit_path_cannot_hide_configured_failure_controls_or_force_an_unused_engine(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['editionRequirements']}
    prefix = 'das.security-agent.s13.'
    if fault == 'drop-intent': leaves['editionRequirements'].remove(by_id[prefix + 'audit-durable-intent-before-effect-and-result'])
    elif fault == 'failure-claim-hides-path':
        by_id[prefix + 'audit-service-failure-stops-normal-write']['activation'] = {'op': 'fact', 'key': 'failure.audit_unavailable'}
    elif fault == 'permission-hides-stop':
        by_id[prefix + 'audit-independent-preapproved-local-stop']['activation'] = {'op': 'fact', 'key': 'permission.business_write_allowed'}
    elif fault == 'force-sqlite': by_id[prefix + 'audit-sqlite-actual-nonnull-foreign-key-conflicts']['activation']['args'].pop()
    elif fault == 'registration-and-recovery':
        by_id[prefix + 'audit-unknown-storage-not-file-visibility-as-success-or-absence']['activation']['op'] = 'all'
    else: leaves['editionRequirements'].remove(by_id[prefix + 'audit-collected-candidate-content-still-untrusted'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_task_completion_and_shared_objects_preserve_real_identity_and_authority_boundaries():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    by_id = {leaf['id']: leaf for leaf in leaves['editionRequirements']}
    task = [leaf for leaf in leaves['editionRequirements'] if leaf['controlId'] == 'S14']
    shared = [leaf for leaf in leaves['editionRequirements'] if leaf['controlId'] == 'S20']
    assert len(task) == 62 and len(shared) == 52
    assert {leaf['ownerModule'] for leaf in task} == {'das.governance.documentation'}
    assert {leaf['ownerModule'] for leaf in shared} == {'das.security-agent'}
    assert {leaf['parentClause'] for leaf in task} == {'cl-13.14'}
    assert {leaf['strength'] for leaf in task + shared} == {'MUST'}
    for suffix, terms in (
            ('completion-unique-task-cycle', ('taskKey', 'cycle', 'revision', 'attempt', '请求 ID')),
            ('rescind-narrow-proof', ('无部署', '无迁移', '无外部依赖影响', 'closureRescinded')),
            ('revalidation-no-worker-business-authority', ('验证专用授权', '预算', '不恢复终态 Task', '重新验证失败'))):
        leaf = by_id['das.governance.documentation.s14.' + suffix]
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert all(term in context for term in terms)
    integration = by_id['das.governance.documentation.s14.completion-applicable-integration-evidence']
    assert integration['activation']['args'][-1]['key'] == 'task.integration_applicable'
    no_integration = by_id['das.security-agent.s20.no-integration-preapproved-branch']
    assert no_integration['activation']['args'][-1]['key'] == 'task.integration_not_applicable'
    failed = by_id['das.governance.documentation.s14.revalidation-failure-history-retained-current-denied']
    assert failed['activation']['args'][-1]['key'] == 'result.revalidation_failed_or_insufficient'
    for name in ('bundle', 'task', 'decision', 'candidate', 'authorization', 'verification',
                 'action-receipt', 'integration-receipt', 'completion'):
        for duty in ('minimum-binding', 'authorized-producer', 'no-role-substitution'):
            assert 'das.security-agent.s20.' + name + '-' + duty in by_id
    action = by_id['das.security-agent.s20.resource-current-decision-context-evidence-recheck']
    assert action['activation'] == {'op': 'fact', 'key': 'activity.protected_action'}
    context = validator.source_fragment(ROOT, action['contextRefs'][0])
    assert all(term in context for term in ('线性化前', '父子状态', '有效授权依赖', '有效期不足'))


@pytest.mark.parametrize('fault', ['drop-task', 'drop-shared', 'wrong-owner', 'hide-authority',
                                 'unconditional-integration', 'deny-successful-revalidation',
                                 'truncate-closure-exception', 'drop-aba'])
def test_task_completion_and_shared_objects_cannot_rewrite_obligations_or_legal_exceptions(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['editionRequirements']}
    task = 'das.governance.documentation.s14.'
    shared = 'das.security-agent.s20.'
    if fault == 'drop-task': leaves['editionRequirements'].remove(by_id[task + 'completion-unique-task-cycle'])
    elif fault == 'drop-shared': leaves['editionRequirements'].remove(by_id[shared + 'decision-no-role-substitution'])
    elif fault == 'wrong-owner': by_id[task + 'completion-unique-task-cycle']['ownerModule'] = 'das.security-agent'
    elif fault == 'hide-authority': by_id[shared + 'resource-current-decision-context-evidence-recheck']['activation'] = {
        'op': 'fact', 'key': 'permission.current_action_allowed'}
    elif fault == 'unconditional-integration':
        by_id[task + 'completion-applicable-integration-evidence']['activation']['args'].pop()
    elif fault == 'deny-successful-revalidation':
        by_id[task + 'revalidation-failure-history-retained-current-denied']['activation']['args'].pop()
    elif fault == 'truncate-closure-exception':
        by_id[task + 'rescind-narrow-proof']['contextRefs'][0] = deepcopy(
            by_id[task + 'completion-unique-task-cycle']['contextRefs'][0])
    else: leaves['editionRequirements'].remove(by_id[shared + 'target-aba-protected-generation-not-reusable-value'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


@pytest.mark.parametrize('section,old,new', [
    (14, 'attempt 变化不允许重置预算', 'attempt 变化允许重置预算'),
    (20, '不再次执行集成', '再次执行集成'),
])
def test_completion_source_and_hash_coedit_cannot_erase_history_or_reintegrate(bundle, section, old, new):
    author = bundle / 'modules/edition-1.5.md'
    assert old in author.read_text()
    author.write_text(author.read_text().replace(old, new))
    leaves = validator.load(bundle / 'standard_requirements.json')
    lines = author.read_text().splitlines()
    # Recompute the untrusted, supplied fragment hashes too. The independent
    # complete source pin, rather than those coedited hashes, must still reject.
    for leaf in leaves['editionRequirements']:
        for ref in [leaf['strengthRef'], *leaf['bodyRefs'], *leaf['contextRefs']]:
            text = '\n'.join(lines[ref['startLine'] - 1:ref['endLine']])
            ref['endColumn'] = min(ref['endColumn'], len(text))
            selected = text[ref['startColumn']:ref['endColumn']]
            ref['textSha256'] = hashlib.sha256(selected.encode()).hexdigest()
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='normative body or legal exception changed'):
        validator.reviewed_completion_requirements(bundle)


def test_tooling_appendix_reuses_main_rules_and_preserves_recommendations():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    path = 'appendices/appendix-l-tooling-standard.md'
    original = {unit['id'] for unit in baseline['units'] if unit['source'] == path}
    assert len(original) == 17
    assert original <= set(leaves['mappedLegacyUnitIds'])
    tooling = [leaf for leaf in leaves['requirements'] if leaf['id'].startswith(
        'das.governance.verification-release.tooling.')]
    assert len(tooling) == 26
    assert {leaf['strength'] for leaf in tooling} == {'SHOULD'}
    assert by_id['das.governance.verification-release.verify.reproducible-tooling-lock']['strength'] == 'MUST'
    assert by_id['das.governance.verification-release.verify.closure-structured-pins']['activation'] == {
        'op': 'fact', 'key': 'activity.release_or_adoption_closure'}
    for criterion, first, last, phrase in (
            ('reproducible-tooling-lock', 12, 37, 'The lock SHOULD record'),
            ('closure-structured-pins', 41, 61, '"floating": false'),
            ('report-no-results-fails', 99, 107, 'MUST fail closed'),
            ('mirror-originating-snapshot', 128, 133, 'immutable snapshot')):
        refs = [ref for ref in by_id['das.governance.verification-release.verify.' + criterion]['contextRefs']
                if ref['path'] == path and (ref['startLine'], ref['endLine']) == (first, last)]
        assert len(refs) == 1
        assert phrase in validator.source_fragment(ROOT, refs[0])
    optional = by_id['das.governance.verification-release.tooling.lock-generator-policy-versions']
    assert optional['activation']['args'][-1]['key'] == 'tooling.generator_or_policy_affects_outputs'
    assert by_id['das.governance.verification-release.tooling.check-verify-report']['activation']['args'][-1]['key'] == 'tooling.verify_report_emitted'
    assert not any(leaf['criterion'] == 'tooling-floating-ref' for leaf in leaves['requirements'])


@pytest.mark.parametrize('fault', ['promote-lock-fields', 'hide-output-condition',
                                 'drop-pin-context', 'weaken-existing-pin',
                                 'hide-missing-results', 'drop-release-check'])
def test_tooling_appendix_cannot_weaken_pins_or_turn_optional_mechanisms_into_mandates(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    if fault == 'promote-lock-fields':
        by_id['das.governance.verification-release.tooling.lock-core-versions']['strength'] = 'MUST'
    elif fault == 'hide-output-condition':
        by_id['das.governance.verification-release.tooling.lock-generator-policy-versions']['activation']['args'].pop()
    elif fault == 'drop-pin-context':
        by_id['das.governance.verification-release.verify.closure-structured-pins']['contextRefs'].pop()
    elif fault == 'weaken-existing-pin':
        by_id['das.governance.verification-release.verify.closure-structured-pins']['strength'] = 'SHOULD'
    elif fault == 'hide-missing-results':
        by_id['das.governance.verification-release.verify.report-no-results-fails']['activation'] = {
            'op': 'fact', 'key': 'permission.results_available'}
    else:
        leaves['requirements'].remove(by_id['das.governance.verification-release.tooling.check-pinned-refs'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_original_playbooks_keep_migration_ui_review_and_scenario_scope():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    required = {
        'das.architecture-modularity.migration.required-playbook',
        'das.architecture-modularity.migration.stable-seam',
        'das.architecture-modularity.migration.cutover-replay',
        'das.interaction.standard-ui.review.judgement-human',
        'das.interaction.standard-ui.review.p1-deferred-owner',
        'das.interaction.standard-ui.review.destructive-object-identity',
        'das.architecture-modularity.ddd.monolith-context-module',
        'das.architecture-modularity.ddd.domain-no-infrastructure',
        'das.architecture-modularity.ddd.aggregate-transition-tests',
        'das.architecture-modularity.bdd.short-term-gap-owner',
        'das.architecture-modularity.bdd.tier2-isolated',
        'das.architecture-modularity.bdd.observable-idempotency',
    }
    assert required <= set(by_id)
    assert by_id['das.architecture-modularity.migration.stable-seam']['strength'] == 'MUST'
    assert by_id['das.architecture-modularity.migration.expand-contract']['strength'] == 'SHOULD'
    assert by_id['das.architecture-modularity.migration.required-playbook']['activation']['op'] == 'any'
    assert by_id['das.architecture-modularity.migration.cutover-replay']['activation']['args'][-1]['key'] == 'pipeline.tier_0_or_1'
    assert by_id['das.interaction.standard-ui.review.p1-fix']['strength'] == 'SHOULD'
    deferred = by_id['das.interaction.standard-ui.review.p1-deferred-owner']['activation']
    assert deferred['args'][0] == {'op': 'any', 'args': [
        {'op': 'fact', 'key': 'surface.ui'}, {'op': 'fact', 'key': 'surface.hfvi'}]}
    assert deferred['args'][1]['args'][-1]['key'] == 'ui.p1_deferred'
    assert by_id['das.architecture-modularity.ddd.shallow-inheritance']['strength'] == 'SHOULD'
    live = by_id['das.architecture-modularity.bdd.tier2-isolated']
    assert live['activation']['args'][-1]['key'] == 'scenario.tier_2'
    assert 'MAY call live services' in validator.source_fragment(ROOT, live['contextRefs'][0])
    for identity, source in (
        ('das.architecture-modularity.domain.scenario-trace-contracts', 'appendix-j-'),
        ('das.architecture-modularity.domain.critical-executable-scenarios', 'appendix-j-'),
        ('das.interaction.standard-ui.ui.default-gate-boundary', 'appendix-h-'),
    ):
        assert any(source in ref['path'] for ref in by_id[identity]['contextRefs'])
    assert leaves['qualificationEligible'] is False


@pytest.mark.parametrize('fault', ['all-required-triggers', 'approval-hides-ui-duty',
                                 'tier2-only-live', 'upgrade-inheritance',
                                 'cutover-loses-tier', 'drop-original-scenario-context'])
def test_playbook_mapping_rejects_weakened_scope_or_promoted_guidance(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    if fault == 'all-required-triggers':
        by_id['das.architecture-modularity.migration.required-playbook']['activation']['op'] = 'all'
    elif fault == 'approval-hides-ui-duty':
        by_id['das.interaction.standard-ui.review.judgement-human']['activation'] = {
            'op': 'fact', 'key': 'permission.ui_review_approved'}
    elif fault == 'tier2-only-live':
        by_id['das.architecture-modularity.bdd.tier2-isolated']['activation']['args'].append({
            'op': 'fact', 'key': 'scenario.live_services_used'})
    elif fault == 'upgrade-inheritance':
        by_id['das.architecture-modularity.ddd.shallow-inheritance']['strength'] = 'MUST'
    elif fault == 'cutover-loses-tier':
        by_id['das.architecture-modularity.migration.cutover-replay']['activation']['args'].pop()
    else:
        by_id['das.architecture-modularity.domain.scenario-trace-contracts']['contextRefs'].pop()
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_operational_principles_preserve_harness_rollout_and_security_choices():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    required = {
        'das.governance.verification-release.integration.browser-smoke-or-api-rationale',
        'das.governance.verification-release.integration.merge-smoke-if-not-every-pr',
        'das.governance.verification-release.integration.shared-ci-image-digests',
        'das.governance.verification-release.platform.stable-contract-actual-producer',
        'das.governance.verification-release.platform.release-code-config-flag-rollback',
        'das.governance.verification-release.platform.exhaustion-no-crash-typed-outcome',
        'das.security-agent.operational.no-tool-secrets-unless-necessary',
        'das.security-agent.operational.encryption-exception-approval-record-expiry-controls',
        'das.security-agent.operational.primary-derived-deletion',
        'das.core.principles.must-exception-sunset',
        'das.core.principles.no-policy-law-violating-exception',
    }
    assert required <= set(by_id)
    assert all(by_id[identity]['parentClause'] == 'A-G' for identity in required)
    ui = by_id['das.governance.verification-release.integration.browser-smoke-or-api-rationale']
    assert 'or document why API-level smoke is sufficient' in validator.source_fragment(ROOT, ui['contextRefs'][0])
    assert by_id['das.governance.verification-release.integration.merge-smoke-if-not-every-pr']['activation']['args'][-1]['key'] == 'harness.smoke_not_every_pr'
    assert by_id['das.governance.verification-release.platform.production-oncall-escalation']['activation'] == {'op': 'fact', 'key': 'activity.production_system'}
    secret = by_id['das.security-agent.operational.no-app-db-secrets-without-protected-purpose']
    assert 'unless explicitly designed for that purpose and protected' in validator.source_fragment(ROOT, secret['bodyRefs'][0])
    assert by_id['das.core.principles.should-deviation-justification-controls']['strength'] == 'MUST'
    assert by_id['das.governance.verification-release.platform.hermetic-verify']['strength'] == 'SHOULD'
    assert leaves['qualificationEligible'] is False


def test_ui_smoke_choice_keeps_recommendation_and_api_alternative_in_its_body():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    leaf = next(row for row in leaves['requirements'] if row['id'] ==
                'das.governance.verification-release.integration.browser-smoke-or-api-rationale')
    body = validator.source_fragment(ROOT, leaf['bodyRefs'][0])
    assert body == ('SHOULD include at least one **browser-level** smoke scenario (`smoke-ui`) '
                    'for each canonical workflow (or document why API-level smoke is sufficient).')
    assert leaf['strength'] == 'MUST'
    assert validator.source_fragment(ROOT, leaf['strengthRef']) == 'MUST'
    assert leaf['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.integration_harness'},
        {'op': 'fact', 'key': 'surface.ui'}]}
    # The label governs the coverage choice; it does not upgrade the recommended
    # browser mechanism or remove the original documented API alternative.
    context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
    assert '**MUST:** If the system has a user-facing UI' in context
    assert body in context


def test_ci_harness_authority_does_not_apply_to_local_execution():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    leaf = next(row for row in leaves['requirements'] if row['id'] ==
                'das.governance.verification-release.integration.ci-system-authority')
    assert leaf['strength'] == 'MUST'
    assert leaf['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.integration_harness'},
        {'op': 'fact', 'key': 'activity.harness_ci'}]}
    context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
    assert 'The harness `verify` output in CI MUST be treated as authoritative' in context


@pytest.mark.parametrize('criterion,line', [
    ('dedup-window-or-prevent-late-retries',173),
    ('operator-replay-new-key-or-retain-dedup',189)])
def test_backend_retry_choices_preserve_both_legal_branches(criterion,line):
    leaves=validator.load(ROOT/'standard_requirements.json')
    leaf=next(row for row in leaves['requirements'] if row['id']==
              'das.architecture-modularity.backend.'+criterion)
    original=(ROOT/'appendices/appendix-g-ai-product-engineering-principles-addendum.md').read_text().splitlines()[line-1]
    assert validator.source_fragment(ROOT,leaf['bodyRefs'][0])==original.removeprefix('- **MUST:** ')
    assert leaf['strength']=='MUST'
    assert validator.source_fragment(ROOT,leaf['strengthRef'])=='MUST'
    assert 'or ' in validator.source_fragment(ROOT,leaf['bodyRefs'][0])


@pytest.mark.parametrize('fault', ['ui-always', 'merge-without-condition', 'stable-without-producer',
                                 'production-always', 'weaken-exception', 'hide-tool-policy',
                                 'optional-budget-controls', 'upgrade-hermetic', 'drop-canonical-context',
                                 'duplicate-consumer-pin'])
def test_operational_mapping_rejects_lost_scope_exceptions_or_duplicate_duties(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    integration = 'das.governance.verification-release.integration.'
    platform = 'das.governance.verification-release.platform.'
    if fault == 'ui-always': by_id[integration + 'browser-smoke-or-api-rationale']['activation']['args'].pop()
    elif fault == 'merge-without-condition': by_id[integration + 'merge-smoke-if-not-every-pr']['activation']['args'].pop()
    elif fault == 'stable-without-producer': by_id[platform + 'stable-contract-actual-producer']['activation'] = {'op': 'fact', 'key': 'permission.stable_publish_approved'}
    elif fault == 'production-always': by_id[platform + 'production-oncall-escalation']['activation'] = {'op': 'const', 'value': True}
    elif fault == 'weaken-exception': by_id['das.core.principles.must-exception-sunset']['strength'] = 'SHOULD'
    elif fault == 'hide-tool-policy': by_id['das.security-agent.operational.tool-allowlists-io-schemas']['activation'] = {'op': 'fact', 'key': 'permission.tools_allowed'}
    elif fault == 'optional-budget-controls': by_id[platform + 'soft-budget-explicit-lifecycle']['strength'] = 'SHOULD'
    elif fault == 'upgrade-hermetic': by_id[platform + 'hermetic-verify']['strength'] = 'MUST'
    elif fault == 'drop-canonical-context': by_id['das.governance.verification-release.verify.one-canonical-entrypoint']['contextRefs'].pop()
    else: leaves['requirements'].append(deepcopy(by_id['das.contracts-compatibility.multirepo.consumer-baseline-pin']))
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_data_evals_keep_immutable_pointer_choices_privacy_and_original_tiers():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    data = {leaf['criterion']: leaf for leaf in leaves['requirements']
            if leaf['id'].startswith('das.ai-runtime-evaluation.data.')}
    assert {'dataset-manifest-required', 'gating-snapshot-when-hash-infeasible',
            'optional-uri-immutable-same-bytes', 'sensitive-debug-redaction-or-encryption',
            'eval-determinism-tier', 'gating-eval-local-pinned', 'gating-scoring-run-version',
            'no-unstable-gating-network', 'explicit-regression-budgets',
            'label-process-dataset-version', 'eval-run-dataset-immutable-identity',
            'eval-run-seeds-when-used', 'no-raw-sensitive-report-default'} <= set(data)
    assert all(leaf['parentClause'] == 'A-G' for leaf in data.values())
    assert data['gating-snapshot-when-hash-infeasible']['activation']['args'][-1]['key'] == 'dataset.content_hash_infeasible'
    assert data['optional-uri-immutable-same-bytes']['activation']['args'][-1]['key'] == 'dataset.storage_uri_present'
    assert data['sensitive-debug-redaction-or-encryption']['activation'] == {'op': 'fact', 'key': 'activity.sensitive_debug_capture'}
    assert 'redaction or encryption' in validator.source_fragment(ROOT, data['sensitive-debug-redaction-or-encryption']['bodyRefs'][0])
    context = validator.source_fragment(ROOT, data['eval-determinism-tier']['contextRefs'][0])
    assert 'Tier 0 (replay via cassettes)' in context
    assert 'Tier 1 (stable given pinned dependencies)' in context
    assert 'Tier 2 (bitwise / fully deterministic)' in context
    assert data['eval-run-environment-fingerprint']['strength'] == 'SHOULD'
    assert data['stochastic-regression-detection']['strength'] == 'SHOULD'
    assert leaves['qualificationEligible'] is False


def test_data_evaluation_module_covers_pure_data_without_fabricating_ai_capability():
    catalog, _ = inputs()
    module = next(item for item in catalog['modules'] if item['id'] == 'das.ai-runtime-evaluation')
    assert module['activation'] == {'op': 'any', 'args': [
        {'op': 'fact', 'key': key} for key in ('capability.ai', 'capability.algorithm',
                                             'activity.dataset_in_use', 'activity.eval_suite')]}


@pytest.mark.parametrize('fault', ['optional-uri-always', 'snapshot-without-condition', 'hide-debug-controls',
                                 'label-all-datasets', 'upgrade-fingerprint', 'omit-network-duty',
                                 'drop-tier-context', 'drop-dataset-context', 'missing-appendix-parent'])
def test_data_evals_mapping_rejects_lost_choices_and_fake_privacy_exemptions(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    prefix = 'das.ai-runtime-evaluation.data.'
    if fault == 'optional-uri-always': by_id[prefix + 'optional-uri-immutable-same-bytes']['activation']['args'].pop()
    elif fault == 'snapshot-without-condition': by_id[prefix + 'gating-snapshot-when-hash-infeasible']['activation']['args'].pop()
    elif fault == 'hide-debug-controls': by_id[prefix + 'sensitive-debug-access-approval']['activation'] = {'op': 'fact', 'key': 'permission.debug_capture_allowed'}
    elif fault == 'label-all-datasets': by_id[prefix + 'label-guidelines-examples-edge-cases']['activation'] = {'op': 'fact', 'key': 'activity.dataset_in_use'}
    elif fault == 'upgrade-fingerprint': by_id[prefix + 'eval-run-environment-fingerprint']['strength'] = 'MUST'
    elif fault == 'omit-network-duty': leaves['requirements'].remove(by_id[prefix + 'no-unstable-gating-network'])
    elif fault == 'drop-tier-context': by_id[prefix + 'eval-determinism-tier']['contextRefs'].pop()
    elif fault == 'drop-dataset-context': by_id['das.contracts-compatibility.contract.dataset-hash-method']['contextRefs'].pop()
    else:
        owner = next(module for module in catalog['modules'] if module['id'] == 'das.ai-runtime-evaluation')
        owner['clauseIds'].remove('A-G')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_original_backend_jobs_keep_sor_retry_budget_and_terminal_responsibilities():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    backend = {leaf['criterion']: leaf for leaf in leaves['requirements']
               if leaf['id'].startswith('das.architecture-modularity.backend.')}
    assert {'transaction-before-external-effects', 'explicit-key-when-no-safe-implicit-idempotency',
            'external-side-effect-dedup', 'operator-replay-new-key-or-retain-dedup',
            'full-pipeline-result-every-attempt', 'no-job-time-travel', 'retry-cancel-terminal-state',
            'hard-budget-no-effects', 'hard-budget-safe-outcome', 'soft-budget-documented-lifecycle',
            'sor-authorization', 'safe-audit-payload'} <= set(backend)
    assert all(leaf['parentClause'] == 'A-G' for leaf in backend.values())
    assert backend['single-artifact-or-operational-justification']['strength'] == 'SHOULD'
    assert 'unless a runtime split is operationally justified' in validator.source_fragment(
        ROOT, backend['single-artifact-or-operational-justification']['bodyRefs'][0])
    assert backend['explicit-key-when-no-safe-implicit-idempotency']['activation']['args'][-1]['key'] == 'operation.no_safe_implicit_idempotency'
    assert backend['hard-budget-no-effects']['activation']['args'][-1]['key'] == 'job.hard_budget_exhausted'
    assert backend['soft-budget-documented-lifecycle']['activation']['args'][-1]['key'] == 'job.soft_budget_used'
    assert backend['identical-derived-job-result']['activation']['args'][-1]['key'] == 'job.derived_result_field_present'
    for criterion in ('no-job-time-travel', 'no-last-run-only-terminality', 'no-full-key-log'):
        assert validator.source_fragment(ROOT, backend[criterion]['strengthRef']) == 'MUST NOT'
    for criterion in ('dedup-window-or-prevent-late-retries', 'operator-replay-new-key-or-retain-dedup',
                      'sensitive-encryption-or-approved-exception', 'hard-budget-safe-outcome'):
        assert 'or' in validator.source_fragment(ROOT, backend[criterion]['contextRefs'][0])
    assert leaves['qualificationEligible'] is False


@pytest.mark.parametrize('fault', ['weaken-transaction', 'hide-authorization', 'drop-hard-budget-condition',
                                 'remove-terminal-prohibition', 'require-optional-result',
                                 'truncate-retry-context', 'duplicate-public-api', 'drop-alias-context'])
def test_backend_mapping_cannot_waive_or_strengthen_original_duties(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    prefix = 'das.architecture-modularity.backend.'
    if fault == 'weaken-transaction': by_id[prefix + 'transaction-before-external-effects']['strength'] = 'SHOULD'
    elif fault == 'hide-authorization': by_id[prefix + 'sor-authorization']['activation'] = {'op': 'fact', 'key': 'permission.operation_allowed'}
    elif fault == 'drop-hard-budget-condition': by_id[prefix + 'hard-budget-no-effects']['activation']['args'].pop()
    elif fault == 'remove-terminal-prohibition': by_id[prefix + 'no-job-time-travel']['strengthRef'] = deepcopy(by_id[prefix + 'idempotent-job-transitions']['strengthRef'])
    elif fault == 'require-optional-result': by_id[prefix + 'identical-derived-job-result']['activation']['args'].pop()
    elif fault == 'truncate-retry-context': by_id[prefix + 'retry-cancel-terminal-state']['contextRefs'] = deepcopy(by_id[prefix + 'no-job-time-travel']['contextRefs'])
    elif fault == 'duplicate-public-api': leaves['requirements'].append(deepcopy(by_id['das.architecture-modularity.sdmm.public-imports']))
    else: by_id['das.contracts-compatibility.contract.job-profile']['contextRefs'].pop()
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_keyword_sampling_cannot_omit_original_minimum_gates_or_duplicate_existing_duties():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    minimum = {leaf['criterion']: leaf for leaf in leaves['requirements']
               if leaf['id'].startswith('das.governance.verification-release.minimum.')}
    assert set(minimum) == {
        'contracts-schema', 'contracts-fixtures', 'contracts-changed-compatibility',
        'backend-unit', 'backend-integration', 'backend-contract', 'backend-job-idempotency',
        'backend-job-retry', 'integration-smoke', 'integration-compatibility', 'integration-system-verify',
        'docs-status', 'docs-governing-standard', 'docs-required-sections', 'docs-placeholders',
    }
    inventory = validator.legacy_units(ROOT, baseline)
    assert len(baseline['units']) == 479
    assert len(inventory) == 518
    assert len([identity for identity in inventory if identity.startswith('legacy-minimum-')]) == 6
    assert all(leaf['parentClause'] == 'cl-10.2' and leaf['strength'] == 'MUST' for leaf in minimum.values())
    assert minimum['backend-job-idempotency']['activation']['args'][-1]['key'] == 'activity.backend_job_flows'
    assert minimum['contracts-changed-compatibility']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.contract_repository'}, {'op': 'fact', 'key': 'activity.contract_change'}]}
    assert minimum['docs-status']['activation'] == {'op': 'fact', 'key': 'activity.governed_doc_set'}
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    for identity in ('das.interaction.standard-ui.ui.default-gate-boundary',
                     'das.interaction.standard-ui.ui.default-gate-unit',
                     'das.interaction.standard-ui.ui.default-gate-smoke',
                     'das.ai-runtime-evaluation.algorithm.repo-boundary-checks',
                     'das.ai-runtime-evaluation.algorithm.repo-core-unit-tests',
                     'das.ai-runtime-evaluation.algorithm.repo-deterministic-eval',
                     'das.ai-runtime-evaluation.algorithm.repo-tier-replay'):
        contexts = by_id[identity]['contextRefs']
        ui = identity.startswith('das.interaction.standard-ui.ui.')
        assert len(contexts) == (3 if ui else 2)
        minimum_contexts = [ref for ref in contexts if ref['path'] == 'SPECIFICATION.md'
                            and (ref['startLine'], ref['endLine']) == (1685, 1692)]
        assert len(minimum_contexts) == 1
        assert 'Minimum per-repo gates' in validator.source_fragment(ROOT, minimum_contexts[0])
        if ui:
            repeated_contexts = [ref for ref in contexts if ref['path'] ==
                                'appendices/appendix-h-ui-design-review-checklist.md']
            assert len(repeated_contexts) == 1
            assert (repeated_contexts[0]['startLine'], repeated_contexts[0]['endLine']) == (42, 53)
    assert not any('minimum.frontend-' in leaf['id'] or 'minimum.algo-' in leaf['id']
                   for leaf in leaves['requirements'])


@pytest.mark.parametrize('fault', ['drop-row', 'duplicate-frontend', 'hide-job-tests',
                                 'docs-as-permission', 'weaken-minimum', 'remove-alias-context', 'lose-change-condition',
                                 'rewrite-implicit-source', 'missing-implicit-owner'])
def test_original_implicit_minima_are_not_optional_or_new_duplicate_requirements(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    minimum = by_id['das.governance.verification-release.minimum.backend-job-idempotency']
    if fault == 'drop-row': leaves['requirements'].remove(minimum)
    elif fault == 'duplicate-frontend': leaves['requirements'].append(deepcopy(by_id['das.interaction.standard-ui.ui.default-gate-smoke']))
    elif fault == 'hide-job-tests': minimum['activation'] = {'op': 'fact', 'key': 'permission.job_tests_required'}
    elif fault == 'docs-as-permission': by_id['das.governance.verification-release.minimum.docs-status']['activation'] = {'op': 'fact', 'key': 'permission.docs_approved'}
    elif fault == 'weaken-minimum': minimum['strength'] = 'SHOULD'
    elif fault == 'remove-alias-context': by_id['das.ai-runtime-evaluation.algorithm.repo-tier-replay']['contextRefs'].pop()
    elif fault == 'lose-change-condition': by_id['das.governance.verification-release.minimum.contracts-changed-compatibility']['activation']['args'].pop()
    elif fault == 'rewrite-implicit-source':
        author = bundle / 'SPECIFICATION.md'
        author.write_text(author.read_text().replace('compatibility checks for changed contracts.', 'optional compatibility checks.'))
    else:
        owner = next(item for item in catalog['modules'] if item['id'] == 'das.governance.verification-release')
        owner['legacyUnitIds'].remove('legacy-minimum-de7276bb-10-2-backend')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


def test_unnumbered_legacy_source_uses_existing_stable_appendix_parent():
    _, baseline = inputs()
    registry = validator.load(ROOT / 'ids/standard_ids.json')
    units = {item['id']: item for item in baseline['units']}
    unit = units['legacy-text-165796df-0018']
    assert unit['parentClause'] == ''
    assert validator.legacy_navigation_parent(unit, registry) == 'A-E'
    assert validator.legacy_navigation_parent(units['legacy-text-de7276bb-0001'], registry) == 'C-001'
    assert validator.legacy_navigation_parent(units['legacy-text-de7276bb-0038'], registry) == 'cl-4.3'
    bad = deepcopy(registry)
    del bad['appendixIds']['A-E']
    with pytest.raises(ValueError, match='registered'):
        validator.legacy_navigation_parent(unit, bad)
    bad_unit = dict(unit, source='unapproved.md')
    with pytest.raises(ValueError, match='navigation parent'):
        validator.legacy_navigation_parent(bad_unit, registry)


def test_existing_registered_appendix_parent_is_allowed_without_changing_old_navigation(bundle):
    catalog, baseline = inputs(bundle)
    architecture = next(item for item in catalog['modules'] if item['id'] == 'das.architecture-modularity')
    # A-E is now already required by the reviewed repository playbook. Use
    # another existing shared navigation parent for this lawful-addition control.
    assert 'A-E' in architecture['clauseIds']
    assert 'A-K' not in architecture['clauseIds']
    architecture['clauseIds'].append('A-K')
    validator.validate(catalog, baseline, bundle)
    architecture['clauseIds'][-1] = 'A-UNREGISTERED'
    with pytest.raises(ValueError, match='unknown navigation clause'):
        validator.validate(catalog, baseline, bundle)


def test_multirepo_contract_rules_preserve_independent_owner_and_pure_helpers():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    rules = {leaf['criterion']: leaf for leaf in leaves['requirements']
             if leaf['id'].startswith('das.contracts-compatibility.multirepo.')}
    assert len(rules) == 52
    reading = (ROOT / 'modules/requirements.md').read_text()
    section = reading.split('## das.contracts-compatibility.multirepo.contract-one-decision-owner\n', 1)[1].split('\n## ', 1)[0]
    assert '[Normative source](../appendices/appendix-e-multi-repo-contract-driven-standard.md)' in section
    assert all(item['parentClause'] == 'A-E' for item in rules.values())
    for key in ('scoring-locally-runnable', 'scoring-version-pinned', 'no-hidden-success-definition',
                'contract-one-decision-owner', 'contract-owner-review-rule', 'helper-no-runtime-exceptions',
                'codegen-tool-pins', 'codegen-deterministic-output', 'codegen-ci-reproducibility',
                'codegen-no-manual-edits', 'consumer-upgrade-compatibility'):
        assert rules[key]['strength'] == 'MUST'
    assert rules['strict-internet-version-negotiation']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.internet_facing_contract'},
        {'op': 'fact', 'key': 'contract.strict_decoding_selected'}]}
    assert rules['contract-pr-codegen']['activation']['args'][-1]['key'] == 'change.contract_codegen_applicable'
    assert rules['breaking-strategy-stored-data-migration']['activation']['args'][-1]['key'] == 'change.persisted_data_migration_applicable'
    assert validator.source_fragment(ROOT, rules['consumer-compatible-changes']['strengthRef']) == 'Consumer MUST'
    assert validator.source_fragment(ROOT, rules['consumer-no-undocumented-interpretation']['strengthRef']) == 'MUST NOT'
    assert validator.source_fragment(ROOT, rules['helper-no-runtime-exceptions']['strengthRef']) == 'MUST NOT'
    for key in ('consumer-ignore-unknown-default', 'critical-two-check-layers', 'contract-semver'):
        assert rules[key]['strength'] == 'SHOULD'
    assert 'producer‑side schema validation tests' in validator.source_fragment(ROOT, rules['boundary-one-drift-check']['contextRefs'][0])
    assert 'consumer‑side decoding tests' in validator.source_fragment(ROOT, rules['boundary-one-drift-check']['contextRefs'][0])
    assert 'end‑to‑end contract tests' in validator.source_fragment(ROOT, rules['boundary-one-drift-check']['contextRefs'][0])
    assert 'If “constructors” are provided' in validator.source_fragment(ROOT, rules['helper-data-constructors']['contextRefs'][0])


@pytest.mark.parametrize('fault', ['drop-owner', 'weaken-hidden-success-ban', 'lose-strict-condition',
                                 'require-codegen-update', 'require-helper-constructors',
                                 'runtime-exception-permission', 'strengthen-semver', 'fake-parent',
                                 'rewrite-source', 'hide-breaking-migration'])
def test_multirepo_mapping_cannot_invent_authority_or_weaken_original_contracts(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    rules = {leaf['criterion']: leaf for leaf in leaves['requirements']
             if leaf['id'].startswith('das.contracts-compatibility.multirepo.')}
    if fault == 'drop-owner': leaves['requirements'].remove(rules['contract-one-decision-owner'])
    elif fault == 'weaken-hidden-success-ban': rules['no-hidden-success-definition']['strength'] = 'SHOULD'
    elif fault == 'lose-strict-condition': rules['strict-internet-version-negotiation']['activation']['args'].pop()
    elif fault == 'require-codegen-update': rules['contract-pr-codegen']['activation']['args'].pop()
    elif fault == 'require-helper-constructors': rules['helper-data-constructors']['activation']['args'].pop()
    elif fault == 'runtime-exception-permission': rules['helper-no-runtime-exceptions']['activation'] = {'op': 'fact', 'key': 'permission.helper_exceptions_allowed'}
    elif fault == 'strengthen-semver': rules['contract-semver']['strength'] = 'MUST'
    elif fault == 'fake-parent': rules['producer-implementation']['parentClause'] = 'cl-6.3'
    elif fault == 'rewrite-source': rules['producer-implementation']['bodyRefs'][0]['path'] = 'SPECIFICATION.md'
    else: rules['breaking-strategy-stored-data-migration']['activation'] = {'op': 'fact', 'key': 'permission.migration_approved'}
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_documentation_drift_keeps_one_resolution_alternatives_and_l2_controls():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    docs = {leaf['criterion']: leaf for leaf in leaves['requirements']
            if leaf['ownerModule'] == 'das.governance.documentation'
            and leaf['parentClause'] in ('cl-9.7', 'cl-9.8')}
    assert set(docs) == {
        'drift-record-immediately', 'drift-one-outcome', 'drift-decision-record',
        'drift-external-compatibility', 'drift-old-new-fixtures', 'drift-reproducing-gate',
        'drift-waiver-owner', 'drift-waiver-scope', 'drift-waiver-expiry',
        'api-inventory-automation', 'executable-contract-truth', 'l2-automated-drift-check', 'l2-drift-ci',
        'doc-owner', 'doc-approval-rule', 'boundary-decision-owner', 'doc-pr-flow',
        'out-of-band-reconcile-or-noncanonical', 'multi-party-rfc', 'dispute-decision-record',
    }
    scope = validator.source_fragment(ROOT, docs['drift-one-outcome']['contextRefs'][0])
    for phrase in ('PR note', 'tracked issue labeled', 'exactly one', 'Doc is wrong / outdated', 'Code is wrong', 'Intent changed'):
        assert phrase in scope
    assert docs['drift-external-compatibility']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.doc_drift_observed'},
        {'op': 'fact', 'key': 'change.drift_external_or_persisted'}]}
    assert docs['drift-waiver-owner']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.doc_drift_observed'},
        {'op': 'fact', 'key': 'drift.not_fixed_in_current_pr'},
        {'op': 'fact', 'key': 'activity.doc_drift_waiver'}]}
    assert 'date or release milestone' in validator.source_fragment(ROOT, docs['drift-waiver-expiry']['contextRefs'][0])
    for key in ('l2-automated-drift-check', 'l2-drift-ci'):
        assert docs[key]['activation'] == {'op': 'fact', 'key': 'profile.l2'}
    assert 'or treated as non-canonical' in validator.source_fragment(ROOT, docs['out-of-band-reconcile-or-noncanonical']['bodyRefs'][0])
    assert {key for key, leaf in docs.items() if leaf['strength'] == 'SHOULD'} == {
        'api-inventory-automation', 'executable-contract-truth', 'multi-party-rfc'}
    assert leaves['qualificationEligible'] is False


@pytest.mark.parametrize('fault', ['delete', 'duplicate', 'lose-external-condition',
                                 'waiver-as-permission', 'weaken-owner', 'strengthen-rfc', 'drop-resolution-alternatives'])
def test_documentation_governance_cannot_lose_conditions_or_lawful_resolution(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    docs = {leaf['criterion']: leaf for leaf in leaves['requirements'] if leaf['ownerModule'] == 'das.governance.documentation'}
    if fault == 'delete': leaves['requirements'].remove(docs['drift-decision-record'])
    elif fault == 'duplicate': leaves['requirements'].append(deepcopy(docs['doc-owner']))
    elif fault == 'lose-external-condition': docs['drift-external-compatibility']['activation']['args'].pop()
    elif fault == 'waiver-as-permission': docs['drift-waiver-owner']['activation']['args'][-1]['key'] = 'permission.waiver_approved'
    elif fault == 'weaken-owner': docs['doc-owner']['strength'] = 'SHOULD'
    elif fault == 'strengthen-rfc': docs['multi-party-rfc']['strength'] = 'MUST'
    else: docs['drift-one-outcome']['contextRefs'][0] = deepcopy(docs['drift-one-outcome']['bodyRefs'][0])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_documentation_minima_keep_equivalents_optional_waivers_and_package_scope():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    docs = {leaf['criterion']: leaf for leaf in leaves['requirements']
            if leaf['ownerModule'] == 'das.governance.documentation'}
    for key in ('master-doc-readiness', 'sub-doc-canonical-owner-key', 'sub-doc-na-reason',
                'ui-spec-ai-contract-references', 'headless-pointer-not-substantive',
                'package-no-fake-profile', 'module-determinism-section', 'manual-traceability-review',
                'delegated-index-traceability', 'context-pack-l2-current', 'doc-verify-unique-ids'):
        assert key in docs
    assert docs['sub-doc-na-reason']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.governed_subordinate_doc'},
        {'op': 'fact', 'key': 'document.declared_not_applicable'}]}
    assert docs['package-no-fake-profile']['activation'] == {'op': 'fact', 'key': 'activity.pure_package_library_tooling_doc'}
    assert docs['context-pack-l2-current']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'profile.l2'}, {'op': 'fact', 'key': 'change.context_pack_material'}]}
    assert 'or include a documented waiver with owner + expiry' in validator.source_fragment(ROOT, docs['material-change-doc-or-waiver']['bodyRefs'][0])
    assert 'or a single authoritative link' in validator.source_fragment(ROOT, docs['delegated-index-traceability']['bodyRefs'][0])
    assert 'extension-declared equivalent' in validator.source_fragment(ROOT, docs['headless-note-or-mapped-equivalent']['contextRefs'][0])
    for key in ('traceability-automation', 'doc-context-budget', 'context-pack-small', 'master-doc-machine-section-model'):
        assert docs[key]['strength'] == 'SHOULD'
    assert validator.source_fragment(ROOT, docs['headless-pointer-governing-link']['strengthRef']) == 'MUST point'
    assert validator.source_fragment(ROOT, docs['headless-pointer-not-substantive']['strengthRef']) == 'MUST NOT'


def test_interaction_tracks_keep_actual_screens_prototype_bounds_and_cost_control():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    ui = {leaf['criterion']: leaf for leaf in leaves['requirements']
          if leaf['id'].startswith('das.interaction.standard-ui.ui.')
          and leaf['legacyUnitId'].startswith('legacy-text-de7276bb-')}
    hfvi = {leaf['criterion']: leaf for leaf in leaves['requirements']
            if leaf['ownerModule'] == 'das.interaction.hfvi'
            and leaf['legacyUnitId'].startswith('legacy-text-de7276bb-')}
    assert len(ui) == 62
    assert len(hfvi) == 40
    assert {key for key in ui if key.startswith('stream-')} == {
        'stream-contract', 'stream-fixtures', 'stream-scroll', 'stream-selection',
        'stream-cancel', 'stream-partial-final', 'stream-prefer-append', 'stream-replace-documented'}
    assert ui['stream-contract']['activation'] == {'op': 'fact', 'key': 'activity.ui_stream_screen'}
    assert ui['optimistic-rollback']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.low_risk_reversible_ui_action'},
        {'op': 'fact', 'key': 'ui.optimistic_update_used'}]}
    assert ui['reversible-backend-idempotency']['activation'] == {'op': 'fact', 'key': 'activity.low_risk_reversible_ui_action'}
    assert ui['kit-snapshot-pr']['strength'] == 'SHOULD'
    assert ui['ai-generic-thinking']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.ai_ui_flow'}, {'op': 'fact', 'key': 'pipeline.compute_bound'},
        {'op': 'fact', 'key': 'stream.progress_unavailable'}]}
    assert ui['ai-progress-frames']['strength'] == 'SHOULD'
    assert validator.source_fragment(ROOT, ui['no-import-environment']['strengthRef']) == 'MUST NOT'
    for key in ('prototype-motion-bounds', 'prototype-motion-owner', 'prototype-motion-expiry'):
        assert hfvi[key]['activation'] == {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'profile.hfvi'}, {'op': 'fact', 'key': 'profile.l0'},
            {'op': 'fact', 'key': 'activity.prototype_motion_values'}]}
    assert {key for key in hfvi if key.startswith('vis-')} == {
        'vis-coordinates', 'vis-layers', 'vis-input', 'vis-invariants', 'vis-technical-component-table',
        'vis-motion-tokens', 'vis-debug-overlay', 'vis-verification'}
    context = validator.source_fragment(ROOT, hfvi['no-hardcoded-motion']['contextRefs'][0])
    assert 'This section is normative when' in context
    assert 'MAY (L0 only, bounded)' in context
    assert 'owner + expiry' in context
    assert hfvi['schema-before-code']['strength'] == 'MUST'
    assert hfvi['constructor-event-replay-sequence']['strength'] == 'SHOULD'
    assert leaves['qualificationEligible'] is False


@pytest.mark.parametrize('fault', ['drop-minimum', 'require-waiver', 'headless-fake-screen',
                                 'package-fake-profile', 'lose-prototype-owner', 'unconditional-stream',
                                 'strengthen-snapshot-pr', 'weaken-schema-first', 'drop-optimistic-condition',
                                 'hide-idempotency', 'wrong-owner', 'lose-hfvi-exception'])
def test_documentation_and_interaction_conditions_cannot_be_waived_or_strengthened(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    docs = lambda name: by_id['das.governance.documentation.doc.' + name]
    ui = lambda name: by_id['das.interaction.standard-ui.ui.' + name]
    hfvi = lambda name: by_id['das.interaction.hfvi.hfvi.' + name]
    if fault == 'drop-minimum': leaves['requirements'].remove(docs('master-doc-readiness'))
    elif fault == 'require-waiver': docs('material-change-doc-or-waiver')['activation'] = {'op': 'fact', 'key': 'activity.doc_waiver'}
    elif fault == 'headless-fake-screen': docs('headless-note-or-mapped-equivalent')['bodyRefs'] = deepcopy(docs('ui-spec-appendix')['bodyRefs'])
    elif fault == 'package-fake-profile': docs('package-no-fake-profile')['activation'] = {'op': 'fact', 'key': 'profile.headless'}
    elif fault == 'lose-prototype-owner': leaves['requirements'].remove(hfvi('prototype-motion-owner'))
    elif fault == 'unconditional-stream': ui('stream-cancel')['activation'] = {'op': 'const', 'value': True}
    elif fault == 'strengthen-snapshot-pr': ui('kit-snapshot-pr')['strength'] = 'MUST'
    elif fault == 'weaken-schema-first': hfvi('schema-before-code')['strength'] = 'SHOULD'
    elif fault == 'drop-optimistic-condition': ui('optimistic-rollback')['activation']['args'].pop()
    elif fault == 'hide-idempotency': ui('reversible-backend-idempotency')['activation'] = deepcopy(ui('optimistic-rollback')['activation'])
    elif fault == 'wrong-owner': hfvi('visual-gate')['ownerModule'] = 'das.security-agent'
    else: hfvi('no-hardcoded-motion')['contextRefs'] = deepcopy(hfvi('no-hardcoded-motion')['bodyRefs'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_verify_rules_keep_not_run_no_results_and_optional_artifact_semantics():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    rules = {leaf['criterion']: leaf for leaf in leaves['requirements']
             if leaf['id'].startswith('das.governance.verification-release.verify.')}
    assert len(rules) == 114
    for key in ('report-explicit-not-run', 'report-no-disappearing-gates', 'report-no-empty-pass',
                'no-report-as-blocking-gate', 'no-collection-as-enforcement', 'closure-no-bare-string-pins'):
        assert rules[key]['strength'] == 'MUST'
    assert rules['report-no-results-fails']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.governed_verify_report'},
        {'op': 'fact', 'key': 'gate.failure_on_no_results'},
        {'op': 'fact', 'key': 'gate.blocking_or_source_of_truth'}]}
    assert rules['emit-machine-report']['strength'] == 'SHOULD'
    assert rules['provide-full-gate']['strength'] == 'SHOULD'
    assert rules['two-standard-modes']['strength'] == 'MUST'
    assert rules['registry-expected-artifacts']['activation']['args'][-1]['key'] == 'gate.governed_output_expected'
    assert rules['closure-policy-pack-version']['activation']['args'][-1]['key'] == 'suite.policy_pack_applicable'
    assert rules['closure-template-version']['activation']['args'][-1]['key'] == 'suite.generator_template_applicable'
    assert validator.source_fragment(ROOT, rules['report-explicit-not-run']['strengthRef']) == 'MUST be represented'
    assert validator.source_fragment(ROOT, rules['report-no-disappearing-gates']['strengthRef']) == 'MUST NOT'
    assert 'unless explicitly documented and stubbed' in validator.source_fragment(ROOT, rules['fast-hermetic-or-documented-stubs']['bodyRefs'][0])
    assert 'unless the divergence is governed as an explicit extension' in validator.source_fragment(ROOT, rules['mirror-no-local-edits-or-extension']['bodyRefs'][0])
    assert 'source-of-truth artifacts are missing' in validator.source_fragment(ROOT, rules['report-no-empty-pass']['contextRefs'][0])


def test_domain_rules_keep_actual_boundaries_offline_scenarios_and_owner_acceptance():
    leaves = validator.load(ROOT / 'standard_requirements.json')
    rules = {leaf['criterion']: leaf for leaf in leaves['requirements']
             if leaf['id'].startswith('das.architecture-modularity.domain.')}
    assert len(rules) == 44
    assert rules['no-silent-contract-rename']['activation'] == {'op': 'fact', 'key': 'activity.released_contract_terminology'}
    assert validator.source_fragment(ROOT, rules['no-silent-contract-rename']['strengthRef']) == 'MUST NOT'
    for key in ('context-owner', 'context-system-of-record', 'no-backdoor-context-writes'):
        assert rules[key]['activation'] == {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'domain.non_trivial'}, {'op': 'fact', 'key': 'activity.bounded_context'}]}
    assert rules['acl-deterministic']['activation']['args'][-1]['key'] == 'activity.acl_translation'
    assert rules['external-legacy-acl']['strength'] == 'SHOULD'
    assert rules['tier-bdd-offline-default']['strength'] == 'MUST'
    assert rules['nondeterministic-scenario-isolated']['activation']['args'][-1]['key'] == 'scenario.nondeterministic_external_dependencies'
    assert rules['owner-accept-release-scenario']['activation']['args'][-1]['key'] == 'scenario.release_gate'
    assert 'owner** of the bounded context MUST review and accept' in validator.source_fragment(ROOT, rules['owner-accept-release-scenario']['contextRefs'][0])
    assert rules['domain-class-invariants']['strength'] == 'SHOULD'
    assert rules['inheritance-stable-is-a']['strength'] == 'MUST'


@pytest.mark.parametrize('fault', ['drop-not-run', 'skip-is-pass', 'require-optional-report',
                                 'require-optional-version', 'drop-governed-output-condition',
                                 'weaken-no-floating', 'drop-owner-review', 'permission-hides-invariants',
                                 'require-acl', 'drop-offline', 'wrong-domain-force'])
def test_verification_and_domain_duties_cannot_misstate_evidence_or_owner_authority(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    vr = lambda name: by_id['das.governance.verification-release.verify.' + name]
    dm = lambda name: by_id['das.architecture-modularity.domain.' + name]
    if fault == 'drop-not-run': leaves['requirements'].remove(vr('report-explicit-not-run'))
    elif fault == 'skip-is-pass': vr('report-no-empty-pass')['activation'] = {'op': 'fact', 'key': 'verification.passed'}
    elif fault == 'require-optional-report': vr('emit-machine-report')['strength'] = 'MUST'
    elif fault == 'require-optional-version': vr('closure-policy-pack-version')['activation']['args'].pop()
    elif fault == 'drop-governed-output-condition': vr('registry-expected-artifacts')['activation']['args'].pop()
    elif fault == 'weaken-no-floating': vr('release-tool-no-floating-source')['strength'] = 'SHOULD'
    elif fault == 'drop-owner-review': leaves['requirements'].remove(dm('owner-accept-release-scenario'))
    elif fault == 'permission-hides-invariants': dm('core-entity-invariants-tested')['activation'] = {'op': 'fact', 'key': 'permission.domain_approved'}
    elif fault == 'require-acl': dm('external-legacy-acl')['strength'] = 'MUST'
    elif fault == 'drop-offline': dm('tier-bdd-offline-default')['activation'] = {'op': 'const', 'value': False}
    else: dm('no-backdoor-context-writes')['strengthRef'] = deepcopy(dm('domain-glossary')['strengthRef'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_algorithm_track_retains_tiers_side_effects_budgets_and_replay_gates():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
                      if leaf['id'].startswith('das.ai-runtime-evaluation.algorithm.')}
    assert set(mapped) == {
        'tier-master-doc', 'tier-run-manifest', 'replay-config', 'replay-dependency-pins',
        'replay-harness', 'replay-golden-fixtures', 'replay-ci', 'invariant-assertions',
        'stable-cassettes', 'higher-determinism', 'accept-side-effects-mode',
        'adapter-check-before-write', 'dry-run-read-only-or-fakes', 'orchestrator-pass-mode',
        'pipeline-budget-policy', 'runtime-budget-enforcement', 'hard-termination-code',
        'limit-diagnostic-code', 'run-manifest', 'pipeline-result', 'exact-manifest-pointer',
        'lossless-job-wrapping', 'multi-stage-summary', 'material-change-evaluations',
        'evaluation-dataset-pin', 'evaluation-report', 'evaluation-artifacts',
        'repo-boundary-checks', 'repo-core-unit-tests', 'repo-deterministic-eval',
        'repo-pinned-eval-split', 'repo-tier-replay', 'slow-replay-full-tier',
        'critical-default-replay-smoke', 'large-refactor-safe-migration',
    }
    for criterion in ('replay-config', 'replay-dependency-pins', 'replay-harness', 'replay-golden-fixtures', 'replay-ci'):
        assert mapped[criterion]['activation'] == {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'activity.algorithm_pipeline'}, {'op': 'fact', 'key': 'pipeline.tier_0_or_1'}]}
        context = validator.source_fragment(ROOT, mapped[criterion]['contextRefs'][0])
        assert 'How often they block merges is a cost decision governed by the project profile' in context
        assert 'Tier 2 (bitwise / fully deterministic)' in context
    assert mapped['hard-termination-code']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.algorithm_execution'}, {'op': 'fact', 'key': 'budget.limit_affects_execution'},
        {'op': 'fact', 'key': 'budget.hard_termination'}]}
    assert mapped['limit-diagnostic-code']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.algorithm_execution'}, {'op': 'fact', 'key': 'budget.limit_affects_execution'}]}
    assert 'read-only or use fakes/cassettes' in validator.source_fragment(ROOT, mapped['dry-run-read-only-or-fakes']['bodyRefs'][0])
    assert 'sandbox' in validator.source_fragment(ROOT, mapped['adapter-check-before-write']['contextRefs'][0])
    migration = validator.source_fragment(ROOT, mapped['large-refactor-safe-migration']['contextRefs'][0])
    assert 'branch-by-abstraction' in migration and 'parallel run/shadow mode' in migration
    assert validator.source_fragment(ROOT, mapped['repo-boundary-checks']['strengthRef']) == 'MUST'
    recommendations = {'invariant-assertions', 'stable-cassettes', 'higher-determinism', 'multi-stage-summary',
                       'slow-replay-full-tier', 'critical-default-replay-smoke'}
    assert {key for key, leaf in mapped.items() if leaf['strength'] == 'SHOULD'} == recommendations
    assert leaves['qualificationEligible'] is False


@pytest.mark.parametrize('fault', ['delete', 'duplicate', 'wrong-owner', 'strengthen-should',
                                 'lose-tier', 'permission-condition', 'lose-budget-condition', 'drop-context'])
def test_algorithm_scope_cannot_be_rewritten_by_consumer_or_check_outcome(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements'] if leaf['ownerModule'] == 'das.ai-runtime-evaluation'}
    if fault == 'delete': leaves['requirements'].remove(mapped['repo-boundary-checks'])
    elif fault == 'duplicate': leaves['requirements'].append(deepcopy(mapped['repo-boundary-checks']))
    elif fault == 'wrong-owner': mapped['exact-manifest-pointer']['ownerModule'] = 'das.security-agent'
    elif fault == 'strengthen-should': mapped['critical-default-replay-smoke']['strength'] = 'MUST'
    elif fault == 'lose-tier': mapped['replay-ci']['activation']['args'].pop()
    elif fault == 'permission-condition': mapped['adapter-check-before-write']['activation']['key'] = 'permission.write_allowed'
    elif fault == 'lose-budget-condition': mapped['hard-termination-code']['activation']['args'].pop()
    else: mapped['large-refactor-safe-migration']['contextRefs'][0] = deepcopy(mapped['large-refactor-safe-migration']['bodyRefs'][0])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_contract_migration_preserves_legacy_readers_semantic_minima_and_alternatives():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    contracts = {leaf['criterion']: leaf for leaf in leaves['requirements']
                 if leaf['id'].startswith('das.contracts-compatibility.contract.')}
    required = {
        'serialized-camel-case', 'protobuf-style', 'protobuf-json-camel-case',
        'compat-api', 'compat-events', 'compat-persisted', 'compat-operational-schema', 'compat-long-lived-session',
        'breaking-expand-contract', 'breaking-window', 'legacy-tolerant-reader', 'writer-dual-support',
        'explicit-defaults', 'document-defaults', 'additive-fields', 'deprecation-note', 'deprecation-date',
        'persisted-schema-version', 'breaking-major-version', 'breaking-compatibility-runners', 'non-atomic-window',
        'equivalent-envelope-mapping', 'equivalent-envelope-lossless', 'error-stable-code', 'error-machine-code',
        'error-bounded-message', 'error-safe-message', 'error-shallow-details', 'error-bounded-details',
        'diagnostic-codes-array', 'diagnostic-scalar-kv', 'diagnostic-safe', 'explicit-algorithm-budget',
        'budget-in-manifest', 'budget-in-job', 'stable-resource-names', 'stable-exhaustion-code', 'hierarchical-budget',
        'run-schema-version', 'run-id', 'run-created-at', 'run-correlation', 'run-pipeline-id', 'run-algorithm-version',
        'run-contract-pins', 'run-profile', 'run-config-identity', 'run-immutable-config', 'run-raw-input',
        'run-input-identity', 'run-side-effects-mode', 'run-budget-allocated', 'run-budget-consumed',
        'run-budget-remaining', 'run-determinism-tier', 'run-determinism-parameters', 'no-embedded-manifest-hash',
        'external-manifest-hash', 'canonical-manifest-hash', 'pipeline-lossless-job', 'pipeline-run-link',
        'pipeline-status-error', 'pipeline-stage-summaries', 'job-multiple-runs', 'job-start-time', 'job-finish-time',
        'job-side-effects-mode', 'job-profile', 'job-config-identity', 'job-manifest-pointer', 'job-identical-pointers',
        'job-legacy-tolerant-reader', 'dataset-intended-use', 'dataset-provenance', 'dataset-license',
        'dataset-content-identity', 'dataset-hash-method', 'dataset-published-identity', 'dataset-artifact-pointer',
        'dataset-content-addressing', 'dataset-record-schema', 'dataset-legacy-tolerant-reader', 'citation-mapping',
        'citation-unique-ids', 'citation-reference-exists', 'citation-sanitization', 'citation-safe-snippets',
        'citation-offset-unit', 'citation-offset-contract', 'citation-web-utf16', 'citation-graceful-consumer', 'citation-ui-spec',
        'stream-schema', 'stream-semantics', 'stream-fixtures', 'stream-checks', 'stream-monotone-sequence',
        'stream-terminal', 'stream-timeout', 'stream-recovery', 'stream-kind', 'stream-matching-payload',
        'stream-append', 'stream-sparing-replace', 'stream-replace-no-jitter', 'stream-progress', 'stream-generic-working',
        'tokens-canonical-versioned', 'tokens-schema', 'tokens-owner', 'tokens-compatible-evolution',
        'tokens-behavioral-review', 'tokens-visual-regression', 'tokens-semantic-names', 'tokens-stable-names',
        'tokens-incubator-namespace', 'tokens-incubator-owner', 'tokens-incubator-expiry', 'tokens-frontend-ci',
        'tokens-prototype-no-shared-leak', 'component-stable-id', 'component-props-events', 'component-story',
        'component-visual-snapshots', 'component-compatible-evolution',
    }
    required |= {'stable-' + suffix for suffix in ('job-type', 'job-id', 'run-id', 'profile-id', 'config-identity',
                 'stage-id', 'error-code', 'diagnostic-code', 'gating-dataset-id', 'gating-metric-id',
                 'gating-score-id', 'prompt-id', 'tool-allowlist-id')}
    assert set(contracts) == required
    assert contracts['legacy-tolerant-reader']['activation'] == {
        'op': 'fact', 'key': 'activity.legacy_compatibility_surface'}
    assert contracts['breaking-major-version']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.compatibility_surface'}, {'op': 'fact', 'key': 'change.contract_breaking'}]}
    assert contracts['dataset-hash-method']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.dataset_manifest'}, {'op': 'fact', 'key': 'dataset.content_hash_present'}]}
    assert contracts['component-story']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.shared_ui_component'}, {'op': 'fact', 'key': 'ui.kit_exists'},
        {'op': 'fact', 'key': 'ui.component_state_referenced'}]}
    for criterion, phrase in {'run-input-identity': 'at least one of', 'run-config-identity': 'OR',
                             'dataset-content-identity': 'at least one of',
                             'citation-sanitization': 'or', 'tokens-canonical-versioned': 'or'}.items():
        assert phrase in validator.source_fragment(ROOT, contracts[criterion]['contextRefs'][0])
    assert contracts['citation-web-utf16']['strength'] == 'SHOULD'
    assert contracts['stream-progress']['strength'] == 'SHOULD'
    assert contracts['stream-generic-working']['strength'] == 'MUST'
    assert validator.source_fragment(ROOT, contracts['no-embedded-manifest-hash']['strengthRef']) == 'MUST NOT'
    assert validator.source_fragment(ROOT, contracts['external-manifest-hash']['strengthRef']) == 'and MUST live'
    assert validator.source_fragment(ROOT, contracts['run-profile']['strengthRef']) == 'Minimum required fields (normative)'
    assert leaves['qualificationEligible'] is False


def test_identifier_stability_targets_declared_surfaces_not_every_possible_identifier():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    assert by_id['das.contracts-compatibility.contract.stable-job-id']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.canonical_identifier_surface'},
                              {'op': 'fact', 'key': 'identifier.job_id_surface'}]}
    assert by_id['das.contracts-compatibility.contract.stable-prompt-id']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.prompt_or_tool_allowlist_identifiers'},
                              {'op': 'fact', 'key': 'identifier.prompt_id_surface'}]}
    # Identifier-scope facts cannot hide the separate required JobEnvelope ID/config minima.
    assert by_id['das.contracts-compatibility.contract.job-profile']['activation'] == {
        'op': 'fact', 'key': 'activity.job_envelope'}
    assert by_id['das.contracts-compatibility.contract.stable-resource-names']['activation'] == {
        'op': 'fact', 'key': 'activity.algorithm_execution'}


def test_budget_and_stream_duties_preserve_original_trigger_and_surface_conditions():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if leaf['ownerModule'] == 'das.contracts-compatibility'}
    assert mapped['stable-exhaustion-code']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.algorithm_execution'},
        {'op': 'fact', 'key': 'budget.exhaustion_occurred'}]}
    assert 'if budget exhaustion occurs' in validator.source_fragment(ROOT, mapped['stable-exhaustion-code']['contextRefs'][0])
    assert mapped['stream-append']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.legacy_ui_stream'},
        {'op': 'fact', 'key': 'stream.text_surface'}]}
    assert 'for streaming text surfaces' in validator.source_fragment(ROOT, mapped['stream-append']['contextRefs'][0])
    assert mapped['stream-generic-working']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.legacy_ui_stream'},
        {'op': 'fact', 'key': 'pipeline.compute_bound'},
        {'op': 'fact', 'key': 'stream.progress_unavailable'}]}
    assert 'if progress is unavailable' in validator.source_fragment(ROOT, mapped['stream-generic-working']['contextRefs'][0])
    assert mapped['stream-terminal']['activation'] == {'op': 'fact', 'key': 'activity.legacy_ui_stream'}
    assert leaves['qualificationEligible'] is False


def test_requirement_reading_view_keeps_every_scope_without_repeating_shared_blocks():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    reading = validator.render_views(catalog, baseline)['modules/requirements.md']
    contexts = {json.dumps(ref, sort_keys=True): ref for leaf in leaves['requirements'] + leaves['editionRequirements']
                for ref in leaf.get('conditionRefs', []) + leaf['contextRefs']}
    for ref in contexts.values():
        # Local citations in a copied source scope must point back to its author.
        restored = reading.replace('](../' + ref['path'] + '#', '](#').replace('\\\n', '  \n')
        assert validator.source_fragment(ROOT, ref) in restored
    # The original RunManifest minimum and L0 prototype exception are retained
    # once as exact shared source scopes, rather than pasted into every leaf.
    assert reading.count('Minimum required fields (normative):') == 2  # the minimum scope and the hash-note scope
    assert reading.count('**MAY (L0 prototypes):**') == 1
    assert reading.count('Normative scope:') == len(contexts)
    assert set(re.findall(r'\]\(#([^)]+)\)', reading)) <= set(re.findall(r'<a id="([^"]+)"', reading))
    assert '[SQLITE-DURABILITY](../modules/edition-1.5.md#ref-sqlite-durability)' in reading


def test_topology_duties_keep_lawful_alternatives_and_complete_contract_artifacts():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if leaf['id'].startswith('das.architecture-modularity.topology.')}
    assert set(mapped) == {
        'no-size-only-runtime-split', 'prefer-sdmm', 'cross-repo-compatible-or-atomic',
        'hub-no-business-logic', 'hub-no-orchestration', 'frontend-sdmm', 'backend-modular-monolith',
        'algorithm-sdmm', 'eval-data-scrubbed-or-approved', 'ci-production-contract-pin', 'local-contract-override',
        'contract-schema', 'contract-semantics', 'contract-positive-fixtures', 'contract-negative-fixtures',
        'contract-ci-checks', 'contract-compatibility-runners', 'cross-language-types', 'cross-language-identifiers',
        'one-authoring-ssot', 'generated-other-representations', 'representation-drift-checks',
        'stable-semantics-reference', 'linkable-semantics-doc', 'minimal-system-harness', 'system-smoke-flow',
        'harness-compatibility-decode', 'harness-external-replay', 'harness-release-sequencing', 'harness-bidirectional-decode',
    }
    assert mapped['cross-repo-compatible-or-atomic']['activation'] == {'op': 'fact', 'key': 'activity.cross_repo_boundary'}
    assert 'unless you can prove and enforce atomic cutover' in validator.source_fragment(ROOT, mapped['cross-repo-compatible-or-atomic']['bodyRefs'][0])
    assert 'unless explicitly approved by compliance' in validator.source_fragment(ROOT, mapped['eval-data-scrubbed-or-approved']['bodyRefs'][0])
    assert 'business logic' in validator.source_fragment(ROOT, mapped['hub-no-business-logic']['bodyRefs'][0])
    assert validator.source_fragment(ROOT, mapped['hub-no-business-logic']['strengthRef']) == 'MUST NOT'
    assert mapped['harness-external-replay']['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.multi_repo_system'}, {'op': 'fact', 'key': 'material.external_dependencies'}]}
    assert mapped['local-contract-override']['strength'] == 'SHOULD'
    assert mapped['backend-modular-monolith']['strength'] == 'SHOULD'
    assert 'operationally justified' in validator.source_fragment(ROOT, mapped['backend-modular-monolith']['contextRefs'][0])
    assert all('complete' in validator.source_fragment(ROOT, mapped[name]['contextRefs'][0])
               for name in ('contract-schema', 'contract-semantics', 'contract-positive-fixtures', 'contract-ci-checks'))


def test_existing_profile_duties_are_not_limited_to_security_agent():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    profiles = {leaf['criterion']: leaf for leaf in leaves['requirements']
                if leaf['id'].startswith('das.core.profile.')}
    required = {
        'conformance-one', 'conformance-explicit-new-document', 'conformance-legacy-declaration',
        'external-compatibility', 'external-fixtures', 'conformance-evolution', 'conformance-enum-source',
        'l0-deferred-scope', 'l0-debt-owner', 'l0-revisit-trigger',
        'interaction-one', 'interaction-explicit-new-document', 'interaction-legacy-declaration',
        'headless-note', 'headless-pointer-link', 'headless-operator-surface', 'headless-cli-api-surfaces',
        'headless-job-runtime-surfaces', 'headless-packet-export-surfaces', 'headless-no-screen-reason',
        'ui-spec', 'hfvi-section', 'hfvi-appendix', 'interaction-enum-source', 'hfvi-contract-surfaces',
    }
    assert set(profiles) == required
    assert all(leaf['id'].startswith('das.core.profile.') for leaf in profiles.values())
    assert profiles['conformance-one']['activation'] == {'op': 'const', 'value': True}
    assert profiles['l0-debt-owner']['activation'] == {'op': 'fact', 'key': 'profile.l0'}
    assert profiles['conformance-legacy-declaration']['activation'] == {
        'op': 'fact', 'key': 'document.legacy_v1_3_conformant'}
    assert profiles['headless-pointer-link']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'profile.headless'},
                              {'op': 'fact', 'key': 'activity.headless_pointer_doc'}]}
    assert profiles['ui-spec']['activation'] == {
        'op': 'any', 'args': [{'op': 'fact', 'key': 'profile.standard_ui'},
                              {'op': 'fact', 'key': 'profile.hfvi'}]}
    recommendations = {'conformance-legacy-declaration', 'conformance-evolution',
                       'conformance-enum-source', 'interaction-legacy-declaration',
                       'interaction-enum-source', 'hfvi-contract-surfaces'}
    for criterion, leaf in profiles.items():
        assert leaf['strength'] == ('SHOULD' if criterion in recommendations else 'MUST')
        assert leaf['strength'] in validator.source_fragment(ROOT, leaf['strengthRef'])
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        if criterion.endswith('legacy-declaration'):
            assert 'During the v1 compatibility period' in context
        if criterion == 'headless-note':
            assert 'local-extension-declared equivalent' in context
        if criterion == 'l0-revisit-trigger':
            assert 'date or explicit trigger' in context


def test_two_paragraph_carriers_have_twelve_separate_preserved_obligations():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    expected = {
        'repo-scope', 'module-scope', 'contract-surface-scope', 'contract-impact',
        'breaking-compatibility-plan', 'determinism-tier', 'replay-expectation',
        'budgets', 'verification-commands', 'verification-outcomes',
        'document-sequencing', 'enforce-sequencing',
    }
    legacy_security = [item for item in leaves['requirements'] if item['id'].startswith(
        ('das.security-agent.ai-task.', 'das.security-agent.cross-repo.'))]
    assert {item['criterion'] for item in legacy_security} == expected
    assert len(legacy_security) == 12
    assert {'legacy-text-de7276bb-0144', 'legacy-text-de7276bb-0145'} <= set(leaves['mappedLegacyUnitIds'])
    assert leaves['qualificationEligible'] is False
    breaking = next(item for item in leaves['requirements'] if item['criterion'] == 'breaking-compatibility-plan')
    assert breaking['applicability'] == 'breaking-contract-change-in-ai-task-or-pr'
    assert validator.source_fragment(ROOT, breaking['conditionRefs'][1]) == 'if breaking'
    for item in legacy_security:
        assert 'MUST' in validator.source_fragment(ROOT, item['strengthRef'])
        assert item['parentClause'] == ('cl-11.2' if item['criterion'].endswith('sequencing') else 'cl-11.1')
    assert validator.render_views(catalog, baseline) == validator.render_views(catalog, baseline)


def test_standard_release_manifest_and_extension_duties_preserve_conditions():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if leaf['id'].startswith('das.core.manifest.')}
    assert 'extension-review-trigger' in mapped
    assert 'manifest-suite-lock-schema' in mapped
    assert 'published-required-paths' in mapped
    for name in ('name', 'namespace', 'kind', 'extension-point', 'owner', 'scope', 'compatibility-note'):
        assert mapped['extension-' + name]['activation'] == {'op': 'fact', 'key': 'activity.local_extension'}
    trigger = mapped['extension-review-trigger']
    assert trigger['strength'] == 'MUST'
    assert '`upstreamingTrigger` **or** `reviewDate`' in validator.source_fragment(ROOT, trigger['contextRefs'][0])
    assert mapped['extension-doc-type-mapping']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.local_extension'},
                              {'op': 'fact', 'key': 'extension.satisfies_core_doc_type'}]}
    assert mapped['manifest-suite-lock-schema']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.standard_release'},
                              {'op': 'fact', 'key': 'standard.uses_suite_lock'}]}
    assert mapped['extension-schema-validation']['strength'] == 'SHOULD'
    assert mapped['release-check-supporting-refs']['strength'] == 'SHOULD'
    assert mapped['addendum-required-entries']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.standard_release'},
                              {'op': 'fact', 'key': 'standard.ships_normative_addendum'}]}
    expected_enums = {'conformance', 'interaction', 'doc-status', 'gate-cadence', 'gate-enforcement',
                      'doc-family-role', 'module-kind', 'addendum-kind', 'determinism', 'repo-role',
                      'tool-class', 'tool-placement', 'verify-gate-kind', 'suite-module-state',
                      'release-snapshot-kind', 'verify-report-outcome'}
    assert {key.removeprefix('manifest-enum-') for key in mapped if key.startswith('manifest-enum-')} == expected_enums


def test_sdmm_boundary_duties_are_part_of_the_executable_migration():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    boundary = {leaf['criterion']: leaf for leaf in leaves['requirements']
                if leaf['id'].startswith('das.architecture-modularity.sdmm.')}
    assert set(boundary) == {
        'no-self-assembly', 'public-imports', 'no-deep-imports', 'explicit-graph', 'enforce-graph',
        'acyclic-graph', 'safe-import', 'fast-import', 'no-import-io', 'no-import-network',
        'no-import-global-mutation', 'no-import-expensive-init', 'explicit-initialization',
        'stable-public-api', 'consumed-contracts', 'produced-contracts', 'contract-tests',
        'compatible-additive', 'compatible-reader', 'breaking-migration-window',
        'refactor-boundaries', 'refactor-graph', 'ci-boundary-tools', 'canonical-verify', 'module-map',
    }
    assert boundary['breaking-migration-window']['activation'] == {
        'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.external_or_persisted_surface'},
                              {'op': 'fact', 'key': 'change.contract_breaking'}]}
    assert boundary['refactor-graph']['activation'] == {'op': 'fact', 'key': 'boundary.internal_nonpersisted'}
    assert boundary['explicit-initialization']['strength'] == 'SHOULD'
    assert boundary['module-map']['strength'] == 'SHOULD'
    assert 'or expensive initialization' in validator.source_fragment(ROOT, boundary['no-import-expensive-init']['contextRefs'][0])


@pytest.mark.parametrize('criterion', ['no-self-assembly', 'no-deep-imports', 'no-import-network',
                                      'no-import-global-mutation', 'extension-no-silent-enum-widening',
                                      'canonical-release-presentation'])
def test_negative_duties_keep_the_complete_must_not_force_fragment(criterion):
    leaves = validator.validate_requirements(*inputs(), ROOT)
    leaf = next(item for item in leaves['requirements'] if item['criterion'] == criterion)
    assert leaf['strength'] == 'MUST'
    assert validator.source_fragment(ROOT, leaf['strengthRef']) == 'MUST NOT'


def test_all_z_table_results_keep_mandatory_context_and_predicates():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    assert leaves['schemaVersion'] == '3.0.0'
    table_leaves = [leaf for leaf in leaves['editionRequirements'] if leaf['controlId'].startswith('Z')]
    assert len(table_leaves) == 68
    groups = {}
    for leaf in table_leaves:
        groups.setdefault(leaf['controlId'], []).append(leaf)
        assert leaf['parentClause'] == 'cl-13.13'
        assert validator.source_fragment(ROOT, leaf['strengthRef']) == '规范性表格中的强制结果亦为 MUST。'
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert context.startswith('| ' + leaf['controlId'] + ' |')
        assert len(context.split('|')) == 6  # Result, enforcement and evidence all retained.
        preapproval = validator.source_fragment(ROOT, leaf['contextRefs'][1])
        assert '不要求每次动作均由人类点击批准' in preapproval
        assert '高风险动作必须走相应独立批准路径' in preapproval
    assert {control: len(group) for control, group in groups.items()} == {
        'Z01': 4, 'Z02': 4, 'Z03': 5, 'Z04': 7, 'Z05': 4, 'Z06': 12,
        'Z07': 2, 'Z08': 8, 'Z09': 4, 'Z10': 4, 'Z11': 5, 'Z12': 9,
    }
    for leaf in groups['Z02']:
        assert leaf['activation'] == {'op': 'const', 'value': True}
    for leaf in groups['Z04']:
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert '每次受保护动作都重新校验' in context
        key = 'activity.delegation' if leaf['criterion'] == 'delegation-ceiling' else 'activity.protected_action'
        assert leaf['activation'] == {'op': 'fact', 'key': key}
    for leaf in groups['Z08']:
        assert '本地自签和裸 hash 不构成可信证明' in validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert leaf['activation'] == {'op': 'fact', 'key': 'activity.evidence_consumption'}
    breaking = next(leaf for leaf in leaves['requirements'] if leaf['criterion'] == 'breaking-compatibility-plan')
    assert breaking['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.ai_task_or_pr'}, {'op': 'fact', 'key': 'change.contract_breaking'}]}
    for leaf in groups['Z06']:
        role = leaf['criterion'].split('-', 1)[0]
        assert validator.source_fragment(ROOT, leaf['bodyRefs'][0]) == ('验证' if role == 'verification' else '集成')
        scoped = {'op': 'fact', 'key': 'activity.' + role}
        if leaf['criterion'].endswith('external-binding'):
            assert validator.source_fragment(ROOT, leaf['bodyRefs'][1]) == '必要外部工件'
            assert leaf['activation'] == {'op': 'all', 'args': [scoped, {'op': 'fact', 'key': 'material.external_required'}]}
        else:
            assert leaf['activation'] == scoped
    for leaf in groups['Z05']:
        assert leaf['activation'] == {'op': 'fact', 'key': 'activity.untrusted_execution'}
    for leaf in groups['Z12']:
        assert leaf['activation'] == {'op': 'const', 'value': True}


@pytest.mark.parametrize('control', [f'Z{i:02}' for i in range(1, 13)])
def test_no_minimum_control_can_disappear_from_the_partial_catalog(bundle, control):
    leaves = validator.load(bundle / 'standard_requirements.json')
    leaves['editionRequirements'] = [leaf for leaf in leaves['editionRequirements'] if leaf['controlId'] != control]
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='denominator is incomplete'):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['missing-preapproval', 'wrong-actor', 'external-unconditional',
                                  'missing-merge-condition', 'worker-permission-condition', 'stop-only-when-failed'])
def test_risk_predicates_keep_actor_necessity_and_unconditional_stop_duties(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['criterion']: leaf for leaf in leaves['editionRequirements']}
    if fault == 'missing-preapproval': by_id['policy-approval']['contextRefs'].pop()
    elif fault == 'wrong-actor': by_id['verification-candidate-binding']['bodyRefs'][0] = deepcopy(by_id['integration-candidate-binding']['bodyRefs'][0])
    elif fault == 'external-unconditional': by_id['verification-external-binding']['activation'] = {'op': 'fact', 'key': 'activity.verification'}
    elif fault == 'missing-merge-condition': by_id['merge-result-reverification']['activation'] = {'op': 'fact', 'key': 'activity.integration'}
    elif fault == 'worker-permission-condition': by_id['policy-write-denial']['activation'] = {'op': 'fact', 'key': 'permission.worker_write_allowed'}
    else: by_id['revocation-stop']['activation'] = {'op': 'fact', 'key': 'failure.revoked'}
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / 'standard'
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    return root


@pytest.mark.parametrize('fault', ['remove-minimum', 'both-config-identities', 'closed-legacy-reader',
                                 'unconditional-hash-method', 'strengthen-recommendation',
                                 'drop-ui-kit-condition', 'drop-stream-terminal', 'wrong-hash-force'])
def test_contract_mapping_rejects_changed_legacy_conditions_and_minima(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if leaf['ownerModule'] == 'das.contracts-compatibility'}
    if fault == 'remove-minimum': leaves['requirements'].remove(mapped['run-budget-remaining'])
    elif fault == 'both-config-identities':
        mapped['run-config-identity']['activation'] = {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'run.config_id_present'}, {'op': 'fact', 'key': 'run.config_hash_present'}]}
    elif fault == 'closed-legacy-reader': mapped['legacy-tolerant-reader']['activation'] = {'op': 'const', 'value': False}
    elif fault == 'unconditional-hash-method': mapped['dataset-hash-method']['activation'] = {'op': 'fact', 'key': 'activity.dataset_manifest'}
    elif fault == 'strengthen-recommendation': mapped['stream-progress']['strength'] = 'MUST'
    elif fault == 'drop-ui-kit-condition': mapped['component-story']['activation'] = {'op': 'fact', 'key': 'activity.shared_ui_component'}
    elif fault == 'drop-stream-terminal': leaves['requirements'].remove(mapped['stream-terminal'])
    else: mapped['external-manifest-hash']['strengthRef'] = deepcopy(mapped['no-embedded-manifest-hash']['strengthRef'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['missing-positive-fixture', 'missing-negative-fixture', 'weaken-hub-ban',
                                 'permission-waives-data-rule', 'permission-waives-atomicity-rule', 'drop-external-replay-condition'])
def test_topology_mapping_preserves_hub_closure_and_explicit_exception_obligations(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements']
              if leaf['id'].startswith('das.architecture-modularity.topology.')}
    if fault == 'missing-positive-fixture': leaves['requirements'].remove(mapped['contract-positive-fixtures'])
    elif fault == 'missing-negative-fixture': leaves['requirements'].remove(mapped['contract-negative-fixtures'])
    elif fault == 'weaken-hub-ban': mapped['hub-no-business-logic']['strength'] = 'SHOULD'
    elif fault == 'permission-waives-data-rule': mapped['eval-data-scrubbed-or-approved']['activation'] = {'op': 'fact', 'key': 'permission.compliance_denied'}
    elif fault == 'permission-waives-atomicity-rule': mapped['cross-repo-compatible-or-atomic']['activation'] = {'op': 'fact', 'key': 'verification.atomic_cutover_failed'}
    else: mapped['harness-external-replay']['activation'] = {'op': 'fact', 'key': 'activity.multi_repo_system'}
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['missing-field', 'require-optional-schema', 'permission-condition',
                                 'require-both-review-triggers', 'strengthen-self-check', 'wrong-force-source'])
def test_manifest_mapping_rejects_changed_old_semantics(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements'] if leaf['id'].startswith('das.core.manifest.')}
    if fault == 'missing-field': leaves['requirements'].remove(mapped['extension-owner'])
    elif fault == 'require-optional-schema': mapped['manifest-suite-lock-schema']['activation'] = {'op': 'fact', 'key': 'activity.standard_release'}
    elif fault == 'permission-condition': mapped['extension-masterdoc-reference']['activation'] = {'op': 'fact', 'key': 'permission.extensions_allowed'}
    elif fault == 'require-both-review-triggers':
        mapped['extension-review-trigger']['activation'] = {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'extension.has_upstreaming_trigger'}, {'op': 'fact', 'key': 'extension.has_review_date'}]}
    elif fault == 'strengthen-self-check': mapped['release-check-required-paths']['strength'] = 'MUST'
    else: mapped['extension-machine-manifest']['strengthRef'] = deepcopy(mapped['extension-name']['strengthRef'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['missing-boundary', 'unconditional-window', 'waive-refactor-graph',
                                 'wrong-owner', 'strengthen-module-map', 'wrong-import-condition'])
def test_sdmm_mapping_cannot_change_original_strength_scope_or_evolution(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = {leaf['criterion']: leaf for leaf in leaves['requirements'] if leaf['id'].startswith('das.architecture-modularity.sdmm.')}
    if fault == 'missing-boundary': leaves['requirements'].remove(mapped['no-deep-imports'])
    elif fault == 'unconditional-window': mapped['breaking-migration-window']['activation'] = {'op': 'const', 'value': True}
    elif fault == 'waive-refactor-graph': mapped['refactor-graph']['activation'] = {'op': 'const', 'value': False}
    elif fault == 'wrong-owner': mapped['canonical-verify']['ownerModule'] = 'das.security-agent'
    elif fault == 'strengthen-module-map': mapped['module-map']['strength'] = 'MUST'
    else: mapped['no-import-network']['activation'] = {'op': 'fact', 'key': 'permission.network_allowed'}
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['missing-profile', 'waive-headless', 'permission-condition',
                                 'remove-trigger', 'strengthen-recommendation', 'different-owner'])
def test_profile_mapping_cannot_drop_or_reinterpret_old_conditions(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    profiles = {leaf['criterion']: leaf for leaf in leaves['requirements'] if leaf['id'].startswith('das.core.profile.')}
    if fault == 'missing-profile': leaves['requirements'].remove(profiles['interaction-one'])
    elif fault == 'waive-headless': profiles['headless-note']['activation'] = {'op': 'const', 'value': False}
    elif fault == 'permission-condition': profiles['headless-note']['activation'] = {'op': 'fact', 'key': 'permission.headless_allowed'}
    elif fault == 'remove-trigger': profiles['l0-revisit-trigger']['bodyRefs'] = deepcopy(profiles['l0-debt-owner']['bodyRefs'])
    elif fault == 'strengthen-recommendation': profiles['interaction-legacy-declaration']['strength'] = 'MUST'
    else: profiles['ui-spec']['ownerModule'] = 'das.security-agent'
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_coedited_baseline_cannot_hide_deleted_legacy_unit(bundle):
    """The old denominator cannot be replaced along with its consumer hashes."""
    import hashlib
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    mapped = set(leaves['mappedLegacyUnitIds'])
    # Every independently tracked carrier is now mapped. Delete a real mapped
    # original unit; the independently pinned whole baseline must still detect it.
    removed = baseline['units'][-1]
    baseline['units'].remove(removed)
    for module in catalog['modules']:
        if removed['id'] in module['legacyUnitIds']:
            module['legacyUnitIds'].remove(removed['id'])
    # An attacker/careless migration regenerates every dependent digest too.
    raw = (json.dumps(baseline, ensure_ascii=False, indent=2) + '\n').encode()
    (bundle / 'migration/legacy_normative_baseline.json').write_bytes(raw)
    rebound = hashlib.sha256(raw).hexdigest()
    catalog['baselineSha256'] = rebound
    leaves['baselineSha256'] = rebound
    (bundle / 'standard_modules.json').write_text(json.dumps(catalog) + '\n')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='independent baseline'):
        validator.validate(catalog, baseline, bundle)


def test_in_memory_baseline_cannot_differ_from_pinned_file(bundle):
    catalog, baseline = inputs(bundle)
    # APIs as well as CLI must validate the same original input object.
    baseline['sourceCommit'] = '0' * 40
    with pytest.raises(ValueError, match='independent baseline'):
        validator.validate(catalog, baseline, bundle)


@pytest.mark.parametrize('fault', [
    'delete_leaf', 'duplicate_leaf', 'rename_id', 'weaken_strength', 'wrong_owner',
    'wrong_parent', 'remove_breaking_condition', 'condition_on_unconditional',
    'wrong_source_scope', 'wrong_source_digest', 'claim_qualification', 'omit_module_artifact',
])
def test_leaf_loss_or_semantic_change_is_rejected(bundle, fault):
    catalog, baseline = inputs(bundle)
    leaves = validator.load(bundle / 'standard_requirements.json')
    first = leaves['requirements'][0]
    breaking = next(item for item in leaves['requirements'] if item['criterion'] == 'breaking-compatibility-plan')
    if fault == 'delete_leaf': leaves['requirements'].pop()
    elif fault == 'duplicate_leaf': leaves['requirements'][-1] = deepcopy(first)
    elif fault == 'rename_id': first['id'] = 'das.security-agent.ai-task.reused'
    elif fault == 'weaken_strength': first['strength'] = 'SHOULD'
    elif fault == 'wrong_owner': first['ownerModule'] = 'das.core'
    elif fault == 'wrong_parent': first['parentClause'] = 'cl-11.2'
    elif fault == 'remove_breaking_condition': breaking['conditionRefs'].pop()
    elif fault == 'condition_on_unconditional': first['conditionRefs'].append(deepcopy(breaking['conditionRefs'][1]))
    elif fault == 'wrong_source_scope': first['bodyRefs'][0]['startLine'] += 1
    elif fault == 'wrong_source_digest': first['bodyRefs'][0]['textSha256'] = '0' * 64
    elif fault == 'claim_qualification': leaves['qualificationEligible'] = True
    else:
        module = next(item for item in catalog['modules'] if item['id'] == 'das.security-agent')
        module['requiredArtifactRefs'].remove('standard_requirements.json')
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(catalog, baseline, bundle)


@pytest.mark.parametrize('keyword', ['$ref', '$dynamicRef'])
def test_catalog_schema_cannot_fetch_unlocked_rules(bundle, keyword):
    path = bundle / 'standard_requirements.schema.json'
    schema = validator.load(path)
    schema[keyword] = 'https://unapproved.invalid/rule'
    path.write_text(json.dumps(schema))
    with pytest.raises(ValueError, match='locked local schema'):
        validator.validate(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', [
    'delete', 'duplicate', 'rename', 'new_condition', 'weaken', 'wrong_parent',
    'wrong_owner', 'wrong_control', 'wrong_phrase', 'drop_scope', 'wrong_strength',
    'legacy_false', 'legacy_breaking_condition', 'not_risk', 'stage_downgrade',
])
def test_edition_scope_and_executable_conditions_cannot_be_rewritten(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    leaf = next(item for item in leaves['editionRequirements']
                if item['id'] == 'das.security-agent.z02.policy-approval')
    assert leaf['strengthRef'] != leaf['bodyRefs'][0]
    if fault == 'delete': leaves['editionRequirements'].pop()
    elif fault == 'duplicate': leaves['editionRequirements'][-1] = deepcopy(leaf)
    elif fault == 'rename': leaf['id'] += '-new'
    elif fault == 'new_condition': leaf['activation'] = {'op': 'fact', 'key': 'profile.l2'}
    elif fault == 'weaken': leaf['strength'] = 'SHOULD'
    elif fault == 'wrong_parent': leaf['parentClause'] = 'cl-13.12'
    elif fault == 'wrong_owner': leaf['ownerModule'] = 'das.core'
    elif fault == 'wrong_control': leaf['controlId'] = 'Z04'
    elif fault == 'wrong_phrase': leaf['bodyRefs'] = deepcopy(leaves['editionRequirements'][1]['bodyRefs'])
    elif fault == 'drop_scope': leaf['contextRefs'] = deepcopy(leaf['bodyRefs'])
    elif fault == 'wrong_strength': leaf['strengthRef'] = deepcopy(leaf['bodyRefs'][0])
    elif fault == 'legacy_false': leaves['requirements'][0]['activation'] = {'op': 'const', 'value': False}
    elif fault == 'legacy_breaking_condition':
        breaking = next(leaf for leaf in leaves['requirements'] if leaf['criterion'] == 'breaking-compatibility-plan')
        breaking['activation'] = {'op': 'fact', 'key': 'activity.ai_task_or_pr'}
    elif fault == 'not_risk': leaf['activation'] = {'op': 'not', 'args': [{'op': 'fact', 'key': 'activity.protected_action'}]}
    else: leaves['migrationStage'] = 'partial-leaf-mapping'
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(*inputs(bundle), bundle)


@pytest.mark.parametrize('before,after', [
    ('每次受保护动作都重新校验', '受保护动作可以校验'),
    ('未知风险事实阻断相应资格', '未知风险事实不阻断相应资格'),
    ('本地自签和裸 hash 不构成可信证明', '本地自签和裸 hash 构成可信证明'),
    ('不可访问宿主秘密、控制 socket 或未批准网络', '可以访问宿主秘密、控制 socket 或未批准网络'),
    ('必要外部工件的完整身份', '外部工件的可选身份'),
    ('审计不可被 Worker 删除、替换或回滚', '审计可以被 Worker 删除、替换或回滚'),
    ('缺失能力、撤销、事故和降级尝试安全停止', '缺失能力、撤销、事故和降级尝试继续运行'),
])
def test_catalog_regeneration_cannot_hide_a_weakened_normative_carrier(bundle, before, after):
    path = bundle / 'modules/edition-1.5.md'
    text = path.read_text()
    assert text.count(before) == 1
    path.write_text(text.replace(before, after))
    # Deliberately regenerate every edition fragment, including valid hashes,
    # to prove that current-source consistency alone is not the denominator.
    leaves = validator.load(bundle / 'standard_requirements.json')
    lines = path.read_text().splitlines()
    import hashlib
    for leaf in leaves['editionRequirements']:
        if not leaf['controlId'].startswith('Z'):
            continue
        row = next((i, line) for i, line in enumerate(lines, 1) if line.startswith('| ' + leaf['controlId'] + ' |'))
        number, line = row
        ref = leaf['contextRefs'][0]
        ref.update(startLine=number, endLine=number, startColumn=0, endColumn=len(line),
                   textSha256=hashlib.sha256(line.encode()).hexdigest())
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='result changed during leaf extraction'):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('before,after', [
    ('副作用入口与受保护写入入口', '普通客户端入口'),
    ('Action Receipt、撤销与过期代次拒绝证据', '可选日志'),
    ('高风险动作必须走相应独立批准路径', '高风险动作可以不走独立批准路径'),
])
def test_regenerated_context_cannot_weaken_enforcement_evidence_or_preapproval(bundle, before, after):
    import hashlib
    path = bundle / 'modules/edition-1.5.md'
    text = path.read_text()
    assert text.count(before) == 1
    path.write_text(text.replace(before, after))
    lines = path.read_text().splitlines()
    leaves = validator.load(bundle / 'standard_requirements.json')
    # Rebind the altered context with correct coordinates and hashes: the
    # independent normative guard, rather than a stale hash, must reject it.
    for leaf in leaves['editionRequirements']:
        for ref in leaf['contextRefs']:
            line = '\n'.join(lines[ref['startLine'] - 1:ref['endLine']])
            ref.update(endColumn=len(line), textSha256=hashlib.sha256(line.encode()).hexdigest())
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='enforcement or required evidence changed|lost their preapproval qualifier'):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_storage_prose_preserves_original_force_and_whole_exception_context():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    storage = [leaf for leaf in leaves['editionRequirements'] if '.s13.storage.' in leaf['id']]
    assert len(storage) == 28
    by_id = {leaf['criterion']: leaf for leaf in storage}
    recommendation = by_id['connection-constraint-proof']
    assert recommendation['strength'] == 'SHOULD'
    assert validator.source_fragment(ROOT, recommendation['strengthRef']) == '应'
    assert {leaf['strength'] for leaf in storage if leaf != recommendation} == {'MUST'}
    for criterion in ('transaction-before-read', 'serializable-shared-budget', 'serializable-task-set', 'serializable-no-pending'):
        context = validator.source_fragment(ROOT, by_id[criterion]['contextRefs'][0])
        assert '不要求所有只读观察查询使用最高隔离等级' in context
        assert '副作用和长时间网络请求不放入可自动重试的数据库事务体' in context
    for criterion in ('artifact-complete-bytes', 'artifact-storage-durability', 'artifact-protected-reference'):
        assert by_id[criterion]['activation'] == {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'activity.artifact_registration'},
            {'op': 'fact', 'key': 'storage.system_crash_covered'}]}
    for criterion in ('artifact-directory-sync', 'artifact-sync-results'):
        assert by_id[criterion]['activation']['args'][-1] == {'op': 'fact', 'key': 'storage.linux_filesystem'}
    assert '不引入多区域复制或任意灾难下零丢失保证' in validator.source_fragment(ROOT, by_id['durable-confirmation']['contextRefs'][0])
    assert '快照完整不代表已包含备份完成后的事实' in validator.source_fragment(ROOT, by_id['backup-consistent-boundary']['contextRefs'][0])


@pytest.mark.parametrize('fault', ['delete', 'duplicate', 'strengthen-should', 'weaken-must',
                                 'condition-on-reported-failure', 'remove-crash-condition', 'remove-linux-condition',
                                 'permission-as-condition', 'drop-context', 'move-force'])
def test_storage_subobligations_cannot_change_scope_or_normative_force(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    storage = {leaf['criterion']: leaf for leaf in leaves['editionRequirements'] if leaf['controlId'] == 'S13'}
    if fault == 'delete': leaves['editionRequirements'].pop()
    elif fault == 'duplicate': leaves['editionRequirements'][-1] = deepcopy(storage['durable-confirmation'])
    elif fault == 'strengthen-should': storage['connection-constraint-proof']['strength'] = 'MUST'
    elif fault == 'weaken-must': storage['transaction-before-read']['strength'] = 'SHOULD'
    elif fault == 'condition-on-reported-failure': storage['failed-transaction-rollback']['activation'] = {'op': 'all', 'args': [{'op': 'fact', 'key': 'activity.authoritative_write'}, {'op': 'fact', 'key': 'failure.transaction_statement'}]}
    elif fault == 'remove-crash-condition': storage['artifact-complete-bytes']['activation'] = {'op': 'fact', 'key': 'activity.artifact_registration'}
    elif fault == 'remove-linux-condition': storage['artifact-directory-sync']['activation']['args'].pop()
    elif fault == 'permission-as-condition': storage['durable-confirmation']['activation']['key'] = 'permission.write_allowed'
    elif fault == 'drop-context': storage['serializable-no-pending']['contextRefs'][0] = deepcopy(storage['serializable-no-pending']['bodyRefs'][0])
    else: storage['connection-constraint-proof']['strengthRef'] = deepcopy(storage['failed-write-no-success']['strengthRef'])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('before,after', [
    ('不要求所有只读观察查询使用最高隔离等级', '要求所有只读观察查询使用最高隔离等级'),
    ('快照完整不代表已包含备份完成后的事实', '快照完整代表已包含备份完成后的事实'),
    ('不能声称不存在的跨存储原子性', '可以声称跨存储原子性'),
])
def test_regenerated_storage_context_cannot_hide_exception_or_recovery_changes(bundle, before, after):
    import hashlib
    path = bundle / 'modules/edition-1.5.md'
    text = path.read_text()
    assert text.count(before) == 1
    path.write_text(text.replace(before, after))
    lines = path.read_text().splitlines()
    leaves = validator.load(bundle / 'standard_requirements.json')
    for leaf in leaves['editionRequirements']:
        if leaf['controlId'] != 'S13': continue
        ref = leaf['contextRefs'][0]
        current = '\n'.join(lines[ref['startLine'] - 1:ref['endLine']])
        ref.update(endColumn=len(current), textSha256=hashlib.sha256(current.encode()).hexdigest())
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='normative context or exception changed'):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_explicit_audit_read_and_disclosure_leaves_preserve_context_and_actual_scope():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    control = {leaf['criterion']: leaf for leaf in leaves['editionRequirements'] if '.s13.control.' in leaf['id']}
    assert len(control) == 27
    assert {leaf['strength'] for leaf in control.values()} == {'MUST'}
    assert control['bounded-stop-without-record-channel']['activation'] == {'op': 'fact', 'key': 'activity.protected_action'}
    stop = validator.source_fragment(ROOT, control['bounded-stop-without-record-channel']['contextRefs'][0])
    assert '不以先成功写入故障中的主审计库或取得新的业务授权为前提' in stop
    assert '该通道也不可用时仍须执行有界停止' in stop
    assert '不包含扩大权限、解除保护、业务补偿、重新发送外部请求或宣布完成' in stop
    for criterion in ('read-resource-domain-binding', 'read-caller-binding', 'read-purpose-binding', 'read-audience-binding'):
        assert control[criterion]['activation'] == {'op': 'fact', 'key': 'activity.protected_read'}
    for criterion, leaf in control.items():
        if not criterion.startswith('disclosure-'): continue
        assert leaf['activation'] == {'op': 'all', 'args': [
            {'op': 'fact', 'key': 'activity.protected_read'}, {'op': 'fact', 'key': 'activity.continuous_disclosure'}]}
        context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
        assert '不统一要求所有普通下载经过私有数据网关' in context
        assert '不要求逐字节授权' in context
        assert '不声称撤销能收回已经合法披露的数据' in context
    audience = control['capability-audience']
    assert audience['bodyRefs'][0]['startColumn'] > audience['strengthRef']['startColumn']
    assert audience['bodyRefs'][0]['startColumn'] > control['read-audience-binding']['bodyRefs'][0]['startColumn']


@pytest.mark.parametrize('fault', ['delete-control', 'duplicate-control', 'weaken', 'permission-condition',
                                 'fault-condition', 'remove-read-scope', 'wrong-audience-occurrence', 'drop-stop-context'])
def test_control_leaves_cannot_be_waived_or_moved_into_another_scope(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    control = {leaf['criterion']: leaf for leaf in leaves['editionRequirements'] if '.s13.control.' in leaf['id']}
    if fault == 'delete-control': leaves['editionRequirements'].remove(control['audit-checkpoint'])
    elif fault == 'duplicate-control': leaves['editionRequirements'][-1] = deepcopy(control['audit-checkpoint'])
    elif fault == 'weaken': control['capability-revocation']['strength'] = 'SHOULD'
    elif fault == 'permission-condition': control['read-caller-binding']['activation']['key'] = 'permission.read_allowed'
    elif fault == 'fault-condition': control['no-automatic-replay']['activation']['key'] = 'failure.result_write'
    elif fault == 'remove-read-scope': control['disclosure-byte-record-limit']['activation']['args'].pop(0)
    elif fault == 'wrong-audience-occurrence':
        ref = control['capability-audience']['bodyRefs'][0]
        line = (bundle / ref['path']).read_text().splitlines()[ref['startLine'] - 1]
        ref['startColumn'] = line.index('受众'); ref['endColumn'] = ref['startColumn'] + len('受众')
    else: control['bounded-stop-without-record-channel']['contextRefs'][0] = deepcopy(control['bounded-stop-without-record-channel']['bodyRefs'][0])
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('before,after', [
    ('不统一要求所有普通下载经过私有数据网关', '要求所有普通下载经过私有数据网关'),
    ('不要求逐字节授权', '要求逐字节授权'),
    ('该通道也不可用时仍须执行有界停止', '该通道不可用时不执行安全停止'),
])
def test_rebound_control_sources_cannot_erase_exceptions_or_independent_stop(bundle, before, after):
    import hashlib
    path = bundle / 'modules/edition-1.5.md'
    text = path.read_text(); assert text.count(before) == 1
    path.write_text(text.replace(before, after))
    lines = path.read_text().splitlines()
    leaves = validator.load(bundle / 'standard_requirements.json')
    for leaf in leaves['editionRequirements']:
        if '.s13.control.' not in leaf['id']: continue
        ref = leaf['contextRefs'][0]
        text = '\n'.join(lines[ref['startLine'] - 1:ref['endLine']])
        ref.update(endColumn=len(text), textSha256=hashlib.sha256(text.encode()).hexdigest())
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises(ValueError, match='S13 control normative context or exception changed'):
        validator.validate_requirements(*inputs(bundle), bundle)


@pytest.mark.parametrize('fault', ['root-extension', 'root-count', 'leaf-extension', 'invalid-leaf-type',
                                 'wrong-fragment-path', 'edition-extension', 'changed-schema'])
def test_cached_structure_keeps_the_original_full_schema_rejections(fault):
    schema = validator.catalog_schema(ROOT, 'standard_requirements.schema.json')
    leaves = validator.load(ROOT / 'standard_requirements.json')
    raw = json.dumps(schema, sort_keys=True, separators=(',', ':'))
    validator.requirement_structure_check(raw)(leaves)  # Warm with legitimate records.
    if fault == 'root-extension': leaves['permissionGranted'] = True
    elif fault == 'root-count': leaves['requirements'].pop()
    elif fault == 'leaf-extension': leaves['requirements'][0]['permissionGranted'] = True
    elif fault == 'invalid-leaf-type': leaves['requirements'][0] = True
    elif fault == 'wrong-fragment-path': leaves['requirements'][0]['bodyRefs'][0]['path'] = 'unapproved.txt'
    elif fault == 'edition-extension': leaves['editionRequirements'][0]['permissionGranted'] = True
    else:
        schema['properties']['standardVersion'] = {'const': 'an-unsupported-edition'}
    # This is the unchanged complete schema validator, independent of the cache.
    with pytest.raises(ValidationError):
        validator.Draft202012Validator(schema).validate(leaves)
    with pytest.raises(ValidationError):
        validator.requirement_structure_check(json.dumps(schema, sort_keys=True, separators=(',', ':')))(leaves)


@pytest.mark.parametrize('feature', ['prefixItems', 'property-reference'])
def test_structure_cache_keeps_original_scope_for_unsplittable_schemas(feature):
    schema = {'type': 'object', 'properties': {
        'requirements': {'type': 'array', 'items': {'type': 'number'}},
        'editionRequirements': {'type': 'array', 'items': {'type': 'number'}}}}
    value = {'requirements': [2], 'editionRequirements': [3]}
    if feature == 'prefixItems':
        schema['properties']['requirements']['prefixItems'] = [{'type': 'string'}]
        value['requirements'] = ['a lawful first element', 2]
    else:
        schema['properties']['mirror'] = {'$ref': '#/properties/requirements'}
        value['mirror'] = [4]
    validator.Draft202012Validator(schema).validate(value)
    check = validator.requirement_structure_check(json.dumps(schema, sort_keys=True, separators=(',', ':')))
    check(value)
    value['editionRequirements'] = ['invalid']
    with pytest.raises(ValidationError):
        check(value)


def test_structure_cache_does_not_cache_source_or_allow_mutable_schema_results(bundle):
    catalog, baseline = inputs(bundle)
    validator.validate(catalog, baseline, bundle)
    first = validator.catalog_schema(bundle, 'standard_requirements.schema.json')
    first['properties']['qualificationEligible']['const'] = True
    assert validator.catalog_schema(bundle, 'standard_requirements.schema.json')['properties']['qualificationEligible']['const'] is False
    source = bundle / 'SPECIFICATION.md'
    text = source.read_text()
    source.write_text(text.replace('MUST', 'MAY', 1))
    with pytest.raises(ValueError, match='body changed'):
        validator.validate(catalog, baseline, bundle)


def test_implicit_template_minima_are_information_duties_with_original_alternatives():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    p = 'das.governance.documentation.template.'
    promotion = by_id[p + 'l1-l2-deployment-record-promotion-rule']
    assert 'SAME_ARTIFACT_OR_REBUILD' in validator.source_fragment(ROOT, promotion['bodyRefs'][0])
    assert promotion['activation']['args'][1] == {'op': 'any', 'args': [
        {'op': 'fact', 'key': 'activity.document_activation'},
        {'op': 'fact', 'key': 'activity.active_master_doc_update'}]}
    assert promotion['activation']['args'][3] == {'op': 'any', 'args': [
        {'op': 'fact', 'key': 'profile.l1'}, {'op': 'fact', 'key': 'profile.l2'}]}
    assert by_id[p + 'same-artifact-across-environments']['strength'] == 'SHOULD'
    assert by_id['das.architecture-modularity.domain.domain-glossary']['strength'] == 'SHOULD'
    glossary = by_id[p + 'nontrivial-domain-glossary-definition']
    assert glossary['activation']['args'][-1] == {'op': 'fact', 'key': 'domain.non_trivial'}
    assert 'required for non-trivial domains' in validator.source_fragment(ROOT, glossary['strengthRef'])
    ui = 'das.interaction.standard-ui.ui.'
    assert by_id[ui + 'accessibility-gate']['strength'] == 'SHOULD'
    assert by_id[ui + 'required-accessibility-record-keyboard']['strength'] == 'MUST'
    citations = validator.source_fragment(ROOT, by_id[ui + 'citation-screen-record-marker-or-offset-rules']['contextRefs'][0])
    assert 'if marker-based' in citations and 'if offset-based' in citations
    primary = by_id['das.governance.documentation.doc.ui-spec-standard-states']
    assert any('Permission denied' in validator.source_fragment(ROOT, ref) for ref in primary['contextRefs'])
    ai = by_id['das.governance.documentation.doc.ui-spec-ai-states']
    assert any('required if this screen includes AI interaction' in validator.source_fragment(ROOT, ref)
               for ref in ai['contextRefs'])
    assert not any(leaf['criterion'] in {'repairing-cancellable', 'confirmation-object-identity'}
                   for leaf in leaves['requirements'])  # Mixed-case example cells are not new BCP 14 duties.
    assert 'DPR handling, zoom, camera transforms' in '\n'.join(
        validator.source_fragment(ROOT, ref)
        for ref in by_id['das.interaction.hfvi.hfvi.vis-coordinates']['contextRefs'])


@pytest.mark.parametrize('fault', ['drop-minimum', 'remove-readiness', 'l1-only', 'require-rebuild',
                                 'strengthen-accessibility-gate', 'drop-primary-context', 'hide-critical-replay'])
def test_implicit_required_information_cannot_be_deleted_or_strengthened(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    p = 'das.governance.documentation.template.'
    if fault == 'drop-minimum': leaves['requirements'].remove(by_id[p + 'minimum-security-declaration-logging-policy'])
    elif fault == 'remove-readiness': by_id[p + 'required-traceability-contracts']['activation']['args'].pop(1)
    elif fault == 'l1-only': by_id[p + 'l1-l2-environment-matrix']['activation']['args'][3]['args'].pop()
    elif fault == 'require-rebuild':
        by_id[p + 'l1-l2-deployment-record-promotion-rule']['activation']['args'].append({'op': 'fact', 'key': 'deployment.rebuilt'})
    elif fault == 'strengthen-accessibility-gate': by_id['das.interaction.standard-ui.ui.accessibility-gate']['strength'] = 'MUST'
    elif fault == 'drop-primary-context': by_id['das.governance.documentation.doc.ui-spec-standard-states']['contextRefs'].pop()
    else: by_id['das.interaction.hfvi.hfvi.critical-interaction-verification-replay-command']['activation']['args'].append({'op': 'fact', 'key': 'checks.replay_passed'})
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate_requirements(*inputs(bundle), bundle)


def test_remaining_carriers_preserve_templates_examples_and_repeated_ids():
    catalog, baseline = inputs()
    leaves = validator.validate_requirements(catalog, baseline, ROOT)
    assert set(leaves['mappedLegacyUnitIds']) == set(validator.legacy_units(ROOT, baseline))
    # Full tracked-carrier coverage alone does not prove implicit-minimum review,
    # installed acceptance or authority. Keep those independent exits open.
    assert leaves['migrationStage'] == 'complete-leaf-mapping'
    assert leaves['qualificationEligible'] is False
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    template = {leaf['criterion']: leaf for leaf in leaves['requirements'] if '.template.' in leaf['id']}
    repo = {leaf['criterion']: leaf for leaf in leaves['requirements'] if '.repo.' in leaf['id']}
    assert len(template) == 117 and len(repo) == 115
    for leaf in template.values():
        assert leaf['parentClause'] == 'A-C'
        trigger = leaf['activation']['args'][0] if leaf['activation']['op'] == 'all' else leaf['activation']
        assert trigger == {'op':'fact','key':'activity.project_master_doc_template'}
        assert 'OPTIONAL_PLACEHOLDER' in validator.source_fragment(ROOT, leaf['contextRefs'][1])
        assert 'fenced code blocks is literal example text' in validator.source_fragment(ROOT, leaf['contextRefs'][1])
    ready = template['activation-blockers-resolved-or-adr-deferred']
    assert 'explicitly deferred via ADR' in validator.source_fragment(ROOT, ready['bodyRefs'][0])
    assert ready['activation']['args'][-1]['key'] == 'activity.document_activation'
    assert template['activation-l2-current-context-pack']['activation']['args'][-1]['key'] == 'profile.l2'
    assert template['actual-job-envelope-minimum-applicable-correlation']['activation']['args'][-1]['key'] == 'job.correlation_applicable'
    assert template['overall-plan-active-copies-update-or-explicit-divergence']['strength'] == 'MUST'
    assert 'explicitly document divergence' in validator.source_fragment(ROOT, template['overall-plan-active-copies-update-or-explicit-divergence']['bodyRefs'][0])
    assert template['api-table-canonical-registry-index']['strength'] == 'SHOULD'
    assert repo['recommended-role-gate-frontend-build']['strength'] == 'SHOULD'
    assert repo['recommended-role-gate-algorithm-tier0-replay']['activation']['args'][-1]['key'] == 'repository.tier_0_pipelines'
    assert repo['independent-deployment-version-matrix-supported-window']['activation'] == {'op':'fact','key':'activity.independent_deployments'}
    assert repo['cross-repo-change-verifiable-harness-or-fixtures']['activation'] == {'op':'fact','key':'activity.cross_repo_contract_change'}
    assert 'or' in validator.source_fragment(ROOT, repo['cross-repo-change-verifiable-harness-or-fixtures']['contextRefs'][0])
    assert 'enforced atomic cutover' in validator.source_fragment(ROOT, repo['evolution-assume-partial-upgrades-unless-enforced-atomic']['contextRefs'][0])
    assert 'at least one of' in validator.source_fragment(ROOT, repo['user-model-quality-at-least-one-lawful-gate']['bodyRefs'][0])
    for identity in ('das.security-agent.ai-task.repo-scope', 'das.security-agent.ai-task.verification-commands'):
        assert len(by_id[identity]['conditionRefs']) == 1
        assert len(by_id[identity]['contextRefs']) == 2
        assert by_id[identity]['contextRefs'][-1]['path'].endswith('appendix-e-multi-repo-contract-driven-standard.md')
        assert by_id[identity]['activation'] == {'op':'fact','key':'activity.ai_task_or_pr'}
    # An illustrative import-linter layer list remains context, without a new
    # architecture mandate or a replacement for the original public-boundary rule.
    graph = by_id['das.architecture-modularity.sdmm.explicit-graph']
    assert any('These examples are illustrative. Use equivalents' in validator.source_fragment(ROOT, ref)
               for ref in graph['contextRefs'])


@pytest.mark.parametrize('fault', ['template-forced-every-project', 'ready-hidden-by-approval',
                                 'drop-l2-condition', 'force-recommended-build', 'hide-required-contract-check',
                                 'matrix-only-after-window-exists', 'lost-task-repeat', 'weaken-code-literal-rule'])
def test_remaining_scope_and_repeated_provenance_cannot_be_coedited(bundle, fault):
    leaves = validator.load(bundle / 'standard_requirements.json')
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    tp = 'das.governance.documentation.template.'
    rp = 'das.architecture-modularity.repo.'
    if fault == 'template-forced-every-project': by_id[tp+'fenced-literals-not-placeholder-replacement']['activation'] = {'op':'const','value':True}
    elif fault == 'ready-hidden-by-approval': by_id[tp+'activation-blockers-resolved-or-adr-deferred']['activation']['args'][-1]['key'] = 'permission.activate_allowed'
    elif fault == 'drop-l2-condition': by_id[tp+'activation-l2-current-context-pack']['activation']['args'].pop()
    elif fault == 'force-recommended-build': by_id[rp+'recommended-role-gate-frontend-build']['strength'] = 'MUST'
    elif fault == 'hide-required-contract-check': by_id[rp+'cross-repo-change-verifiable-harness-or-fixtures']['activation'] = {'op':'fact','key':'checks.already_passed'}
    elif fault == 'matrix-only-after-window-exists': by_id[rp+'independent-deployment-version-matrix-supported-window']['activation'] = {'op':'fact','key':'contract.supported_window_exists'}
    elif fault == 'lost-task-repeat': by_id['das.security-agent.ai-task.repo-scope']['contextRefs'].pop()
    else: by_id[tp+'fenced-literals-not-placeholder-replacement']['strength'] = 'SHOULD'
    (bundle / 'standard_requirements.json').write_text(json.dumps(leaves) + '\n')
    with pytest.raises((ValueError, ValidationError)):
        validator.validate(*inputs(bundle), bundle)


def test_reviewed_source_scope_cannot_extend_past_unchanged_body(monkeypatch):
    scopes = dict(validator.REPEATED_CONTEXT_SCOPES)
    scopes['legacy-text-5046745a-0038'] = (1099, 1117)
    monkeypatch.setattr(validator, 'REPEATED_CONTEXT_SCOPES', scopes)
    with pytest.raises(ValueError, match='reviewed fragment range'):
        validator.reviewed_legacy_requirements(ROOT, inputs()[1])


def test_optional_dataset_template_preserves_conditional_dual_pointer_invariant():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    leaf = next(row for row in leaves['requirements']
                if row['id'] == 'das.ai-runtime-evaluation.data.dual-primary-pointers-same-bytes')
    assert leaf['strength'] == 'MUST' and leaf['parentClause'] == 'A-G'
    assert validator.source_fragment(ROOT, leaf['strengthRef']) == 'MUST'
    assert validator.source_fragment(ROOT, leaf['bodyRefs'][0]) == (
        'If both are present, they MUST refer to the same bytes/snapshot.')
    assert leaf['activation'] == {'op': 'all', 'args': [
        {'op': 'fact', 'key': 'activity.dataset_manifest'},
        {'op': 'fact', 'key': 'dataset.content_hash_present'},
        {'op': 'fact', 'key': 'dataset.snapshot_id_used'}]}
    context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
    assert 'optional but recommended' in context and 'illustrative fields' in context
    assert 'contentHash' in context and 'snapshotId' in context
    _, baseline = inputs()
    assert len(baseline['units']) == 479
    unit = validator.legacy_units(ROOT, baseline)[leaf['legacyUnitId']]
    assert unit['source'].startswith('appendices/appendix-g-')
    assert 'If both are present' in unit['text']


def test_dataset_template_reuses_equivalent_original_obligations():
    leaves = validator.validate_requirements(*inputs(), ROOT)
    expected = {
        'das.contracts-compatibility.contract.dataset-content-identity',
        'das.contracts-compatibility.contract.dataset-hash-method',
        'das.ai-runtime-evaluation.data.gating-hash-preferred',
        'das.ai-runtime-evaluation.data.gating-snapshot-when-hash-infeasible',
        'das.ai-runtime-evaluation.data.optional-uri-immutable-same-bytes',
    }
    by_id = {leaf['id']: leaf for leaf in leaves['requirements']}
    for identity in expected:
        leaf = by_id[identity]
        contexts = [validator.source_fragment(ROOT, ref) for ref in leaf['contextRefs']]
        assert any('### If both are present' in text and 'optional but recommended' in text
                   for text in contexts), identity
        assert all(ref['startLine'] != 780 for ref in leaf['conditionRefs'])
    assert not any(leaf['criterion'] == 'dataset-template-required'
                   for leaf in leaves['requirements'])


@pytest.mark.parametrize('criterion,line,phrase,strength', [
    ('sensitive-encryption-or-approved-exception', 287,
     'For artifacts classified as sensitive, encryption-at-rest MUST be enabled (or an explicit documented exception approved by the appropriate owner).', 'MUST'),
    ('avoid-or-review-production-locks', 281,
     'Avoid production-impacting locks; when unavoidable, require explicit review and a rollout plan.', 'SHOULD'),
    ('hard-budget-safe-outcome', 268,
     'If a partial/best-effort result is safe to return, the outcome MUST be `degraded`; otherwise it MUST be `failed`.', 'MUST'),
    ('soft-budget-justification', 269,
     'SHOULD be used only when a hard cutoff would cause worse outcomes or when spend can only be estimated until completion.', 'SHOULD'),
])
def test_backend_qualified_choices_keep_full_conditions_and_approval(criterion, line, phrase, strength):
    leaves = validator.load(ROOT / 'standard_requirements.json')
    leaf = next(row for row in leaves['requirements']
                if row['id'] == 'das.architecture-modularity.backend.' + criterion)
    assert leaf['strength'] == strength
    assert validator.source_fragment(ROOT, leaf['bodyRefs'][0]) == phrase
    assert leaf['bodyRefs'][0]['startLine'] == line
    assert validator.source_fragment(ROOT, leaf['strengthRef']) == strength
    context = validator.source_fragment(ROOT, leaf['contextRefs'][0])
    assert phrase in context
