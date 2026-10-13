---
description: Implement a whole module (four layers + registrations + migration + tests)
agent: backend-developer
---

Scope: **a whole module**.

Module: `$ARGUMENTS` (under `app/modules/`)

If the argument is empty, ask which module and what feature.

Implement the whole module following the architecture:

1. If it does not exist, scaffold with `uv run python scripts/create_module.py`.
2. Layers in order: domain → application → infrastructure → presentation.
3. Register the model in `migrations/env.py`, then run
   `make migration m="create_{module}"` and `make migrate`.
4. Register the router in `app/app.py` (both route forms).
5. Write unit tests with fakes in `test/fakes.py`.
6. Finish by running `make test` and `make lint` until green.

Within the step budget, if unfinished, stop, report and request an extension.
