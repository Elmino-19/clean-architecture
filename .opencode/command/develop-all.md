---
description: Implement all modules from the given document/requirement
agent: backend-developer
---

Scope: **all modules**.

Requirement/document: `$ARGUMENTS`

If the argument is empty, ask where the reference is (the design document, the
module list, …).

Implement the modules one at a time; run `make test` after each so it stays
green. Respect the dependency order (DAG) and build the base modules first.

Within the step budget, if not everything fits, stop, give a progress summary
(which modules are done, what remains) and request an extension.
