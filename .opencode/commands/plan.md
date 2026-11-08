---
description: Produce an ordered, dependency-aware task list with one file per worker (planner, writes only .me/runs)
agent: orchestrator
subagent: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
plan $ARGUMENTS
```

- **Verb is fixed:** `plan`. No code file is touched.
- If no objective is given, ask **one** question offering the scope-derived draft.
- `-n` sets how many task files the planner produces (default 3).

Examples:

```text
/plan --modules key -- هدف آزاد
/plan --modules user,knowledge -n 2 -- افزودن پیام خطای سازگار
/plan --files app/app.py --
```

Report every stage to the user and end with the stage table. Never invent scope.
