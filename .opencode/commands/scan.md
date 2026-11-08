---
description: Find architecture deviations and hard-coded data in the given modules/layers (analyzer, read-only)
agent: orchestrator
subagent: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
scan $ARGUMENTS
```

- **Verb is fixed:** `scan`. Everything after the verb is flags and the optional objective.
- If no objective is given, derive it from the scope (find deviations, do not fix them).
- `--kind` restricts the checklist to specific categories when the skill defines them.

Examples:

```text
/scan --modules key,example
/scan --scope layer --layers application,presentation -n 3
/scan --scope all --kind transaction,soft-delete -- یافته‌ها را دسته‌بندی کن
```

Report every stage to the user and end with the stage table. Never invent scope.
