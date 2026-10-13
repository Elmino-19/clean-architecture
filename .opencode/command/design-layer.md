---
description: Design a cross-cutting concern/layer applied to all modules
agent: sdd-writer
---

Scope: **a cross-cutting concern across all modules**.

Concern/layer: `$ARGUMENTS`

Examples: caching, logging, authorization, rate limiting, auditing.

If the argument is empty, ask which concern.

Load the `software-design-document` skill and write a design for this
cross-cutting concern that applies to every module: the fixed rules, the touch
points in each layer, its effect on the API contract, and the dependencies.
Document only, no code.
