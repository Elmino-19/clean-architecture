---
description: "Explain a single file — responsibility, dependencies and change impact"
agent: code-explorer
subtask: true
---

Scope: **a single file**.

Target: `$ARGUMENTS`

If the argument is empty, ask which file.

Using `codegraph_explore`, analyse this file: what it defines, what it depends
on, what depends on it (blast radius), and which flows it appears in. Back every
claim with `file:line`. Read-only.
