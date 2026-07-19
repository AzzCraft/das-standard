# Appendix M - Doc-Family Governance and Module Doc Templates

This appendix defines minimal, machine-checkable templates for the governed document families in the DAS Standard. Replace every angle-bracket placeholder before adopting a template.

## Appendix M PRD Template

### Document Control

- **Doc ID:** <stable-prd-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <product or capability scope>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>

### Goals and non-goals

- Goals: <outcomes>
- Non-goals: <explicit exclusions>

### Workflows

<primary user or operator workflows>

### Acceptance criteria

<testable completion criteria>

## Appendix M Headless Surface Note Template

### Document Control

- **Doc ID:** <stable-headless-surface-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <screenless system scope>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>
- **Interaction profile:** headless

### Why there is no screen inventory

<why the governed product has no primary end-user screen inventory>

### Operator surface

<CLI, administration, or human-operated surfaces>

### API / machine-facing surfaces

<APIs, events, packets, and machine-to-machine boundaries>

### Runtime surfaces

<jobs, workers, schedulers, exports, and operational runtime boundaries>

### Verification

<deterministic verification commands and expected evidence>

## Appendix M Module Doc Template

### Document Control

- **Doc ID:** <stable-module-doc-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <module responsibility boundary>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>
- **Doc family role:** module_doc
- **Module kind:** <package|library|worker|service|infra_module|tooling_module|generator|policy_pack|other>

### Public entrypoints

<public commands, APIs, events, or imported interfaces>

### Contracts owned / consumed

<owned and consumed contract IDs, schemas, and semantics>

### Verify

#### Commands

<canonical commands>

#### Expected outcomes

<success criteria and evidence>

#### Determinism

<tier0|tier1|tier2|not_applicable, inputs, fixtures, and permitted nondeterminism>

## Appendix M Runbook Template

### Document Control

- **Doc ID:** <stable-runbook-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <operational procedure>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>

### Trigger / when to use

<conditions that invoke this runbook>

### Preconditions

<access, safety checks, and required context>

### Steps

<ordered, reversible procedure>

### Rollback / escalation

<rollback, incident escalation, and evidence capture>

## Appendix M Deployment Doc Template

### Document Control

- **Doc ID:** <stable-deployment-doc-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <deployment or environment scope>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>

### Environments

<environment matrix and allowed data classes>

### Artifact identity

<immutable artifact, configuration, and provenance identifiers>

### Rollout

<promotion, gates, and monitoring>

### Rollback / migrations

<rollback constraints, migration strategy, and escalation>

## Appendix M Context Pack Template

### Document Control

- **Doc ID:** <stable-context-pack-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <bounded execution context>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>

### Glossary

<stable terms and identifiers>

### Invariants

<non-negotiable contracts and safety properties>

### Verify

<canonical verification commands and evidence>

### Current tasks / focus

<current scope, decisions, and escalation points>

## Appendix M Support Note Template

### Document Control

- **Doc ID:** <stable-support-note-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <support or handoff boundary>
- **Parent Master Doc:** <repo-relative canonical Master Doc path>

### Audience / handoff

<intended audience and ownership transfer>

### Evidence scope

<what evidence is available and where it is stored>

### Redaction / export behavior

<what may be exported and required redaction>

### Steps / next actions

<next actions, limits, and escalation>

## Appendix M Normative Addendum Template

### Document Control

- **Doc ID:** <stable-addendum-id>
- **Owner:** <owner>
- **Status:** draft
- **Governing standard:** Docs as Software (DAS) Standard v1.4.0
- **Last updated:** <YYYY-MM-DD>
- **Scope:** <normative extension scope>
- **Parent standard:** Docs as Software (DAS) Standard
- **Doc family role:** subordinate_doc
- **Addendum kind:** <deployment|governance|security|other>

### Normative language

<BCP 14 interpretation used by this addendum>

### Purpose and scope

<what the addendum extends and does not replace>

### Relationship to the main standard

<this addendum is subordinate to the main standard and states any precedence or compatibility impact>
