# Prompt: Reverse Engineer a Master Doc

**Role:** Software Architect & DAS Standard Auditor.

**Context:** I have an existing software repository that I need to document using the Docs as Software (DAS) Standard.

**Target Repo:** [INSERT REPO NAME AND VERSION HERE]

**Your Goal:** Create a `master_doc.md` that accurately describes the *current* architecture of this repository, while highlighting where it differs from the DAS Standard.

**Instructions:**

1.  **Analyze the Codebase:**
    * Identify the directory structure (monorepo vs. multi-repo).
    * Locate key contracts (APIs, schemas, types, database models).
    * Trace the primary user workflows, e.g., "User logs in", "User submits order".
    * Find the "verification" methods (test scripts, CI workflows).

2.  **Map to DAS Structure:**
    * Fill out the standard `master_doc.md` sections (Product Definition, Domain Model, System Overview, Contracts, etc.).
    * *Crucial:* If a section does not exist in the repo, e.g., no explicit `contracts/` folder, describe *how* it is currently handled, e.g., "Implicitly defined in `src/types`", and label it as a **Gap**.

3.  **Perform a Gap Analysis:**
    At the very top of the document, insert a "DAS Conformance Summary" table:
    * **Contracts:** Is there a dedicated hub? Are schemas explicit? (Status: Explicit / Implicit / Mixed / Missing)
    * **Boundaries:** Are module boundaries enforced? (Status: Enforced / Leaky / Monolithic)
    * **Verification:** Is there a single `verify` command? (Status: Yes / Fragmented / Missing)
    * **Traceability:** Are requirements linked to code? (Status: High / Low / None)

4.  **Output Format:**
    * Provide the full `master_doc.md` content in Markdown.
    * Ensure the "Conformance Summary" is the first section.
    * Use "Draft" status for this document.

**Input Data:**
[PASTE REPO FILE TREE OR GITHUB LINK HERE]