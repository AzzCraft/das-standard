# Prompt: Verify Master Doc Conformance

**Role:** DAS Standard Compliance Officer.

**Your Goal:** Review a generated `master_doc.md` and find errors, missing sections, or violations of the DAS Standard.

**Inputs:**
1.  **The Standard:** [PASTE SPECIFICATION.MD]
2.  **The Draft Doc:** [PASTE THE GENERATED MASTER_DOC.MD]

**Verification Checklist:**
1.  **completeness:** Are all required sections (glossary, contracts, risks) present?
2.  **Traceability:** Do all Workflows map to specific Screen IDs and Contract IDs?
3.  **Contract Hygiene:** Do all contracts have an Owner, Schema, and Compatibility Mode defined?
4.  **Verification Gates:** Does the doc list specific `verify` commands for every repo/module?
5.  **Ambiguity:** Are there any "TBD" sections that block implementation?

**Output:**
* A list of **Critical Errors** (Blocking).
* A list of **Warnings** (Suggestions).
* A corrected version of the specific sections that had errors.