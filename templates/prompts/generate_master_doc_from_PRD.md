# Prompt: Generate Master Doc from PRD

**Role:** Senior Engineering Lead & AI Architect.
**Standard:** Docs as Software (DAS) Standard v1.0.0.

**Your Goal:** Convert a raw Product Requirements Document (PRD) into a canonical `master_doc.md` that is ready for implementation.

**Inputs:**
1.  **DAS Specification:** SPECIFICATION.MD HERE
2.  **Product Requirements:** [YOUR_PRD.MD]

**Instructions:**
1.  **Ingest** the PRD and identify all User Workflows, Functional Requirements, and Data Entities.
2.  **Structure** the output exactly according to the `Master Doc Template` defined in the DAS Standard.
3.  **Formalize Contracts:**
    * For every boundary crossing (Frontend <-> Backend, Backend <-> Algo), define a specific **Contract ID** (e.g., `API-001`).
    * Define the schema fields and validation rules.
4.  **Define Verification:**
    * Write the specific `verify` commands that should be created for this project.
    * Define the acceptance criteria for each workflow.
5.  **Refine:** Ensure there is no ambiguity. Replace vague phrases like "fast response" with concrete SLOs like "P95 < 200ms".

**Output:**
A single, complete `master_doc.md` file code block that an AI agent can implement the whole project according to it with no ambiguity.