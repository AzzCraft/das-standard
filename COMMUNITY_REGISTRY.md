# DAS Community Registry | 社区名录

This registry tracks open-source repositories that have been documented using the **DAS Standard**.

These Master Docs are community contributions. They provide an architectural "X-Ray" of complex software versions, making them easier to understand and contribute to.

## Featured Projects

| Project | Version | Master Doc Link | Author | Conformance |
| :--- | :--- | :--- | :--- | :--- |
| **Example App** | v1.0.0 | [Link](https://github.com/example/repo/blob/main/docs/master_doc.md) | [@yourname](https://github.com/yourname) | ✅ Full |
| **LangChain** | v0.1.0 | [Link](...) | [@contributor](...) | ⚠️ Partial |
| **React** | v18.2.0 | [Link](...) | [@contributor](...) | ⚠️ Gap Analysis |

---

## How to Contribute

We welcome **"Reverse Engineering"** contributions!

You don't need to write code to contribute. A valuable way to learn a codebase (and help others) is to analyze a popular open-source project (like `pandas`, `next.js`, or `pytorch`) and generate a **Gap Analysis Master Doc** for it.

### Step 1: Select a Target
* Pick a popular repository.
* **Important:** Select a specific **Version Tag** (e.g., `v1.2.3`). Do not document `main`, as it changes too fast.

### Step 2: Generate the Analysis
Use our official **Reverse Engineering Prompt** with an LLM (ChatGPT, Claude, Gemini) to audit the code and generate the doc.

* **[Get the Prompt Here](templates/prompts/reverse_engineer.md)**

### Step 3: Add the Conformance Summary
Since external repos rarely follow DAS perfectly, you must add this table at the very top of your `master_doc.md` to explain the gaps:

| DAS Component | Status in this Repo | Notes |
| :--- | :--- | :--- |
| **Contracts** | ⚠️ Implicit | Defined in code classes; no independent schemas. |
| **Boundaries** | ❌ Mixed | Circular dependencies between `core` and `ui`. |
| **Verification** | ✅ Good | Uses `make test` for everything. |
| **Traceability**| ❌ None | No links between PRDs and Code. |

### Step 4: Submit
1.  Host the `master_doc.md` in your own repository or Gist.
2.  Submit a **Pull Request** to this file (`COMMUNITY_REGISTRY.md`).
3.  Add your link to the table above.

---

## Badge for Your Repo

If your repository follows the DAS Standard, you can add this badge 
[![Architecture: DAS Standard](https://img.shields.io/badge/Architecture-DAS_Standard-blue)](https://github.com/azzcraft/das-standard) to your README:

```markdown
[![Architecture: DAS Standard](https://img.shields.io/badge/Architecture-DAS_Standard-blue)](https://github.com/azzcraft/das-standard)