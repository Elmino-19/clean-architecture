---
description: Apply a change to one layer across all modules
agent: backend-developer
---

Scope: **one layer across all modules**.

Layer: `$ARGUMENTS`

Allowed values: `domain` | `application` | `infrastructure` | `presentation`.
If empty or invalid, ask. If the change itself is unspecified, first ask what
change to apply.

Apply the requested change to this layer across every module (for example, adding
caching to the `infrastructure` layer). Keep the changes consistent and do not
break the layer rules; check each module. Finish with `make test` and `make lint`.

Within the step budget, if unfinished, stop, report and request an extension.
