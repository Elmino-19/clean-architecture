# Checklist and anti-patterns

## Before you finish

- [ ] The four folders and their files exist (empty ones carry a reason comment).
- [ ] `domain` imports no framework (no FastAPI, SQLAlchemy, Pydantic, Redis).
- [ ] No module imports another module's `infrastructure` or `presentation`.
- [ ] The new model is registered in `migrations/env.py` and a migration is created.
- [ ] The router is registered in `app/app.py`.
- [ ] Both route forms (with and without trailing slash) are registered.
- [ ] Only `flush` is used — no `commit` in any repository or use case.
- [ ] `except StandardException` comes first everywhere.
- [ ] Business logic lives only in the use case.
- [ ] Every input/output is typed; no `Any`.
- [ ] Messages come from `ResponseMessages`.
- [ ] `make test` and `make lint` pass.

## Anti-patterns

- ❌ Business logic in a router or repository.
- ❌ `commit`/`rollback` in a repository or use case (only the session dependency).
- ❌ Adding an `IUnitOfWork` (this project has none).
- ❌ Importing ORM models, FastAPI, or Pydantic inside `domain`.
- ❌ Cross-module imports into `infrastructure`/`presentation`.
- ❌ `Any` or missing type hints.
- ❌ Physical delete, or a read that forgets `is_active` filtering.
- ❌ Building the response envelope by hand in a handler.
- ❌ Registering only one route form.
- ❌ Comparing `UNSET` with `==` instead of `is`.
- ❌ Ad-hoc error strings instead of `ResponseMessages`.
- ❌ Forgetting to register the model in `migrations/env.py`.
