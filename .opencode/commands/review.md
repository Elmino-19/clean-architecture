---
description: Verify the existing task list and diff, run make test/lint once, report done vs open
agent: orchestrator
subagent: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
review $ARGUMENTS
```

- **Verb is fixed:** `review`.
- No code is changed: the reviewer only reports and returns open items for a `mend` run.

Examples:

```text
/review --modules key
/review --scope all -- آخرین تغییرات را بازبینی کن
```

Report every stage to the user and end with the stage table. Never invent scope.
