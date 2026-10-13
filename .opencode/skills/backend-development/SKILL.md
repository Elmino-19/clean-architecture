---
name: backend-development
description: Use when implementing or reviewing backend code in this FastAPI project — adding or changing a module, use case, repository, cache, service, router, schema, docs, or dependency. Triggers on module, endpoint, use case, repository, router, schema, service, migration, ORM model, FastAPI, clean architecture, DDD, domain/application/infrastructure/presentation. For a design document use software-design-document instead.
---

# Backend Development

Implementation guide for this project's FastAPI **Clean Architecture + DDD**
layout. Every module is a bounded context split into four layers.

Read only what you need:

| File | Read it for |
|---|---|
| `references/architecture.md` | layer tree, import rules, `shared`, cross-module DAG |
| `references/layers.md` | the exact recipe for each file in each layer |
| `references/cross-cutting.md` | errors, transactions, envelope, pagination, auth |
| `references/naming.md` | the full naming table |
| `references/checklist.md` | done-checklist and anti-patterns |

## Golden rule

**Read `app/modules/key/` before writing.** It is the only module that exercises
every layer (cache with tombstones, a service, full CRUD, actor projections).
`knowledge` is the simple CRUD + notification reference.

## The rules that actually matter

1. **Four layers, inward dependencies.**
   `presentation → infrastructure → application → domain`. `domain` imports no
   framework (no FastAPI, SQLAlchemy, Pydantic, Redis, no I/O).
2. **Each module is four folders** — `domain/ application/ infrastructure/
   presentation/` — each holding its own files (`entities.py`, `use_cases.py`,
   `repositories.py`, `schemas.py`, …). See `references/architecture.md`.
3. **Business rules live in the use case.** Not in the router, not in the
   repository. The router body is always
   `payload → mapper → use case → mapper → return`.
4. **Repositories `flush`, never `commit`.** The only `commit`/`rollback` lives
   in the session dependencies (`get_session` / `get_async_session` in
   `app/core/database.py`). There is **no** `IUnitOfWork`.
5. **Three error shapes** — pick by layer:
   - use case / router: `except StandardException: raise` → `DomainError` →
     `DomainException` → `Exception` → log + `{Module}Exception`
   - repository / service: `except StandardException: raise` → `Exception` → log.
   - cache: never raise — catch, `logger.warning`, `return None`.
   `except StandardException` **must come first** (it extends `HTTPException`).
6. **Soft delete only.** `entity.deactivate(actor)` sets `is_active=false`; reads
   filter `is_active.is_(True)`.
7. **No envelope in handlers.** Return a plain schema;
   `ResponseFormattingMiddleware` wraps it in `StandardResponse`.
8. **Snake_case everywhere** — code, DB and JSON. No camelCase conversion.
9. **Type everything.** No `Any`, no missing annotations.
10. **Every module is registered in two places:** the model in `migrations/env.py`
    (`_ = [...]`), and the router in `app/app.py` (`routers`).

## Workflow — add a module

1. Scaffold: `uv run python scripts/create_module.py` (creates the four folders,
   their files, and the test package).
2. Write **domain** first: entity/VO/enum and their validation.
3. **application**: `interfaces.py` (Protocols) → `exceptions.py` →
   `use_cases.py` → `mappers.py`.
4. **infrastructure**: `models.py` → `repositories.py` → `caches.py` /
   `services.py` if needed.
5. **presentation**: `schemas.py` → `docs.py` → `dependencies.py` → `routers.py`.
6. Register the model in `migrations/env.py`, then
   `make migration m="create_{module}"` and `make migrate`.
7. Register the router in `app/app.py`.
8. Write tests with in-memory fakes (`test/fakes.py`), then
   `make test && make lint`.

For the code of each numbered step, open `references/layers.md`.

## Quick naming reference

| Thing | Pattern |
|---|---|
| Entity / VO / Enum | `PascalCase`; enum always `(str, Enum)` |
| Port (Protocol) | `I{Entity}Repository` / `Cache` / `Service` |
| Use case class | `{Module}UseCases` (one per module) |
| Mapper | module-level `{action}_{target}_mapper` |
| ORM model | `{Entity}Model`, `BaseModel`, table `{prefix}_{plural}` |
| Repository / Cache | `Postgres{Entity}Repository` / `Redis{Entity}Cache` |
| Dependency | `get_{thing}` returning the Protocol type |
| Schema | `CreateRequest`, `UpdateRequest`, `GetAllResponse`, `{Entity}ListItem` |

Full table: `references/naming.md`.

## Before you finish

Run `references/checklist.md` top to bottom. It catches the mistakes this
architecture punishes most (unregistered model, half-registered routes, a
`commit` in a repository, business logic in a router).
