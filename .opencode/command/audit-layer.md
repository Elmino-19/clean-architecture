---
description: Audit one layer (domain/application/infrastructure/presentation) across all modules
agent: code-auditor
subtask: true
---

Scope: **one layer across all modules**.

Layer: `$ARGUMENTS`

Allowed values: `domain` | `application` | `infrastructure` | `presentation`.
If empty or invalid, ask.

Across every module under `app/modules/`, audit only this layer and find the
shared deviations. Output: the findings table (with a module column), the
recurring patterns, and an overall verdict. Within the step budget, if unfinished,
stop and request an extension. Do not edit anything.
