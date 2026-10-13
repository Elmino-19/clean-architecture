---
description: Audit a whole module (all four layers)
agent: code-auditor
subtask: true
---

Scope: **a whole module**.

Module: `$ARGUMENTS` (under `app/modules/`)

If the argument is empty, ask which module.

Audit all four layers of this module and run every mandatory check: folder
structure, layer imports, model registered in `migrations/env.py`, router
registered in `app/app.py`, both route forms, error shapes, `flush` without
`commit`, soft delete, naming. Produce the findings table and a verdict. Do not
edit anything.
