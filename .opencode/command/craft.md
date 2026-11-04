---
description: Implement new code strictly from the task list, then review it (planner → coder×N → reviewer)
agent: orchestrator
subtask: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
craft ${ARGUMENTS}
```

- **Verbs are fixed:** `plan,craft,review` — the full implement pipeline.
- If no objective is given, ask **one** question offering the scope-derived draft.
- Workers never run tests; the `reviewer` runs `make test` and `make lint` once.

Examples:

```text
/craft --modules example -- ماژول نمونه را کامل کن
/craft --modules key -n 3 -- افزودن کش با tombstone
/craft --files app/modules/health/presentation/router.py --
```

Report every stage to the user and end with the stage table. Never invent scope.
