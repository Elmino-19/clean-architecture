---
description: "Analyse a whole module's architecture — layers, ports and request flow"
agent: code-explorer
subtask: true
---

Scope: **a whole module**.

Module: `$ARGUMENTS` (under `app/modules/`)

If the argument is empty, ask which module.

Explain this module's architecture: the four layers, ports (Protocols) and their
implementations, use cases, mappers, and the full flow of a request from router to
database. Also note the cross-module dependencies. Read-only, with `file:line`.
