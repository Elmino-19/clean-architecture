---
description: Fix only the listed items, then review them (scan → planner → editor×N → reviewer)
agent: orchestrator
subagent: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
mend $ARGUMENTS
```

- **Verbs are fixed:** `scan,plan,mend,review` — never fix unnamed findings.
- If no objective is given, ask **one** question offering the scope-derived draft.
- Scope never expands: unlisted issues are reported, not fixed.

Examples:

```text
/mend --modules key -- اصل commit در لایه application
/mend --scope layer --layers infrastructure -- اصلاح نام‌گذاری
/mend --files app/app.py -- رجیستر نبودن روتر
```

Report every stage to the user and end with the stage table. Never invent scope.
