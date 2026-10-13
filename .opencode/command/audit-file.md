---
description: Audit a single file against the architecture rules and coding standards
agent: code-auditor
subtask: true
---

Scope: **a single file**.

Target: `$ARGUMENTS`

If the argument is empty, ask which file.

Audit only this file. Before judging, read it and, if needed, the interfaces it
depends on via `codegraph_explore`. Run the agent's mandatory checklist over this
file and produce the findings table (Severity | file:line | Violated rule |
Explanation | Suggestion) plus a one-line verdict. Do not edit the file.
