# Prompt: Verify Master Doc Against PRD

**Role:** DAS Standard Compliance Officer & Product Quality Assurance (QA).
**Goal:** rigorously audit a draft `master_doc.md` against the DAS Standard and the original Product Requirements (PRD).

**Context:**
I have generated a Master Doc using the DAS Standard. I need you to find errors, omissions, and violations before I approve it for implementation.

**Inputs:**
1. **DAS Specification:** [SPECIFICATION.MD]
2. **Original PRD:** [ORIGINAL_PRD]
3. **Draft Master Doc:** [MASTER_DOC.MD]

**Verification Instructions:**

Perform a deep analysis on these three dimensions. Be strict.

### 1. Standard Conformance Check (The "Law")
* **Structure:** Does it contain all required sections (Glossary, Contract Inventory, WBS, Open Questions)?
* **Contracts:** Do `API-###`, `SCHEMA-###`, and `JOB-###` IDs exist? Are they referenced in the "Traceability Index"?
* **Naming:** Are serialized contracts using `camelCase` (as per Spec §4.1)?
* **Verification:** Does the doc define specific `verify` commands for every repo/module?
* **Status:** Are required placeholders (like `{{REQUIRED}}`) filled in?

### 2. PRD Fidelity Check (The "Scope")
* **Completeness:** Did we miss any User Stories or Functional Requirements from the original PRD?
* **Accuracy:** Do the defined Workflows (`W1`, `W2`...) match the user intent described in the PRD?
* **Constraints:** Are the Non-Functional Requirements (Performance, Security) from the PRD explicitly documented in the Master Doc?

### 3. Logic & Traceability Check (The "Engineering")
* **Orphans:** Are there Workflows that map to *no* Screen IDs or *no* Contract IDs?
* **Dead Ends:** Are there State Machines that have no exit condition?
* **Hallucinations:** Did the draft invent features that were not in the PRD?

**Output Format:**

Provide a structured **Audit Report**:

## Critical Errors (Blockers)
*List specific violations that must be fixed before coding (e.g., missing verification commands, undefined contracts for critical flows).*

## Warnings (Suggestions)
*List areas that are vague or could be improved (e.g., weak acceptance criteria, missing edge cases).*

## Recommended Fixes
*For the Critical Errors above, provide the **exact Markdown text** to replace the broken sections.*