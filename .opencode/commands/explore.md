---
description: Explain architecture, request flow and blast radius for the given scope (analyzer, read-only)
agent: orchestrator
subagent: true
---

Execute this command line as the project orchestrator, with the verbs fixed:

```text
explore $ARGUMENTS
```

- **Verb is fixed:** `explore` (analyzer in `--mode map`).
- Nothing is edited, not even a comment.

Examples:

```text
/explore --modules key
/explore --scope layer --layers domain -- مرزهای دامنه چیست
/explore --files app/modules/user/application/use_cases.py -- این جریان از کجا می‌آید
```

Report every stage to the user and end with the stage table. Never invent scope.
