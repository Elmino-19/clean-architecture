---
description: Implement or fix a single file following the architecture and layer rules
agent: backend-developer
---

Scope: **a single file**.

Target: `$ARGUMENTS`

If the argument is empty, ask which file and what change.

First load the `backend-development` skill and the relevant layer recipe in
`references/layers.md`. Change only this file unless a dependency forces
otherwise (report that too). Respect the layer rules, the error shape and naming.
Finish by running `make lint` (and the related test).
