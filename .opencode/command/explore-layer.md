---
description: Compare one layer across all modules (patterns and exceptions)
agent: code-explorer
subtask: true
---

Scope: **one layer across all modules**.

Layer: `$ARGUMENTS`

Allowed values: `domain` | `application` | `infrastructure` | `presentation`.
If empty or invalid, ask.

Compare this layer across every module under `app/modules/`: what is common, what
differs, and which modules break the pattern. Output: the pattern summary +
the list of exceptions with `file:line`. Read-only.
