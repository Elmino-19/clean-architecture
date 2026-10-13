---
description: Full audit of every module against the architecture rules and standards
agent: code-auditor
subtask: true
---

Scope: **all modules**.

Run a complete audit over every module under `app/modules/`: four-layer
structure, layer imports, model/router registration, both route forms, error
shapes, transactions (`flush` without `commit`), soft delete, naming and typing.

Output: the findings table (Blocker/Major/Minor) + a per-module summary + an
overall verdict. Within the step budget, if unfinished, stop, report status and
request an extension. Read-only.
