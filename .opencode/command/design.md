---
description: Write the Software Design Document for a product or feature (sdd-writer, docs only)
agent: orchestrator
subtask: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
design ${ARGUMENTS}
```

- **Verb is fixed:** `design`. This is a separate branch: the planner pipeline is skipped.
- Output is `docs/sdd.md` only — never production code.
- If the product description is missing, the writer asks its own clarifying questions.

Examples:

```text
/design -- محصول جدید با ماژول‌های auth و key
/design -- افزودن ماژول notification به سند طراحی
```

Report every stage to the user and end with the stage table. Never invent scope.
