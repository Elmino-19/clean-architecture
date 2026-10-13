# Architecture rules (fixed)

## Dependency direction

`presentation → infrastructure → application → domain`. No layer depends on a
layer outside it.

| Layer | May import |
|---|---|
| `domain` | `shared`, other modules' `domain` — **no** FastAPI, SQLAlchemy, Pydantic, Redis, any I/O |
| `application` | `domain`, `shared`, other modules' `domain`/`application` |
| `infrastructure` | `domain`, `application`, `core`, `shared` |
| `presentation` | all layers below it, plus `core` |

Cross-module imports go **only** into another module's `domain` or
`application`; never into its `infrastructure`/`presentation`. The graph stays a
DAG.

### The two sanctioned exceptions

1. **`application/mappers.py`** may import `presentation/schemas.py` and
   `infrastructure/models.py` — a mapper exists precisely to cross those
   boundaries. No other file in `application` gets this pass.
2. **Composition roots** (`app/app.py`, each module's
   `presentation/dependencies.py`, `shared/presentation/dependencies.py`) may
   import `infrastructure` implementations to wire ports to adapters.

## Principles

1. **Pure domain.** Plain Python only. Validation in `__post_init__`, value
   equality in `__eq__`, no external dependency.
2. **Ports and adapters.** `application` knows only `typing.Protocol`, never an
   abstract class. This is what lets a use case be tested with an in-memory fake
   and lets Postgres be swapped without touching business logic.
3. **Typed everything.** No `Any`, no ambiguous types. Every input/output is
   typed.
4. **Transaction.** A repository only `flush`es and never `commit`/`rollback`.
   The only `commit`/`rollback` lives in the session dependencies
   (`get_session` for sync/migrations, `get_async_session` for the request path,
   in `core/database.py`); `get_async_session` commits after a successful
   request. **There is no `IUnitOfWork` — do not design one.**
5. **Soft delete.** No physical delete. `is_active=false`. Reads filter
   `is_active=true`.
6. **Time.** Store timestamps in UTC. Business-timezone conversion only in
   presentation or a shared utility.
7. **`UNSET`.** For partial updates, distinguish "field omitted" from "field
   explicitly null". The entity defaults to `UNSET`; the mapper sets it from
   `payload.model_fields_set`; the use case keeps the stored value wherever the
   incoming value `is UNSET`. Always compare with `is` / `is not`.
8. **API contract — snake_case.** Code, database and JSON are all snake_case; no
   camelCase conversion anywhere. Schemas are Pydantic v2 with `ConfigDict`,
   extending `BaseModel`; the response envelope is added by
   `StandardResponse` in middleware, never by a handler.
9. **The handler boundary never leaks.** A router never builds the envelope,
   never holds business logic, never sees an ORM model. Its body is exactly
   `payload → mapper → use case → mapper → return`.

## Error shapes

| Shape | Where | Pattern |
|---|---|---|
| **3-branch** | use case, router | `StandardException` → raise · `DomainError` → map · `Exception` → log + generic error |
| **2-branch** | repository, service | `StandardException` → raise · `Exception` → log + module error |
| **never-raise** | cache | catch · log · `return None` |

```python
# 3-branch
except StandardException:
    raise
except DomainError as e:
    raise DomainException(e)
except Exception as e:
    logger.opt(exception=e).error("An error occurred in the create endpoint.")
    raise EntityException()
```

⚠️ `except StandardException` **must come first**. `StandardException` extends
`HTTPException`, so any other order swallows every deliberate 404/409 into a 500.

The 2-branch shape has no `DomainError` arm (those layers never evaluate domain
rules). The never-raise shape has no re-raise arm at all (a cache outage must
fall back to the database and never fail the request).

## Module tree

```text
app/modules/{module}/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py          # entities; validation in __post_init__
│   ├── value_objects.py     # framework-free value objects
│   └── enums.py             # (str, Enum)
├── application/
│   ├── __init__.py
│   ├── interfaces.py        # Protocols: I{Entity}Repository / Cache / Service
│   ├── use_cases.py         # one {Module}UseCases class — business rules here
│   ├── mappers.py           # module-level boundary functions
│   ├── exceptions.py        # {Module}Exception + one per business rule
│   └── utils.py             # module-local helpers
├── infrastructure/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy models on BaseModel
│   ├── repositories.py      # Postgres{Entity}Repository — flush, never commit
│   ├── caches.py            # Redis{Entity}Cache — never-raise
│   └── services.py          # external/stateful systems behind a Protocol
└── presentation/
    ├── __init__.py
    ├── routers.py           # handlers: payload → mapper → use case → mapper → return
    ├── schemas.py           # Pydantic v2 with Field + ConfigDict
    ├── docs.py              # router_docs + {action}_docs
    └── dependencies.py      # Depends factories returning the Protocol type
```

**Empty file rule.** A file with no implementation yet is still created, with a
reason comment — never deleted:

```python
# No cache in this phase — reason: read volume is low, cache adds no value yet.
```

An empty-but-documented file means "this module does not cache"; a missing file
means "no decision taken".

## Section markers

Inside a file, group code with comment headers:

```python
# === SECTION: Entities ===
# === SECTION: Value Objects ===
# === SECTION: Enums ===
# === SECTION: Exceptions ===
# === SECTION: Ports ===
# === SECTION: Use Cases ===
# === SECTION: Mappers ===
# === SECTION: Models ===
# === SECTION: Repositories ===
# === SECTION: Caches ===
# === SECTION: Services ===
# === SECTION: Schemas ===
# === SECTION: Dependencies ===
# === SECTION: Routers ===
```

## Project layout

```text
app/
├── app.py               # FastAPI instance + router registration + startup
├── core/                # settings, security, database, cache, middleware, migrations, logging
├── modules/
│   ├── shared/          # base types — no routes
│   └── {module}/        # four folders, as above
migrations/versions/     # Alembic — first migration creates the whole schema
scripts/                 # helpers (create_module, seed, …)
test/                    # mirrors app/modules + fakes.py
```

The base module is called `shared` (not `core`, not `common`): `core` holds
global settings/infrastructure, `shared` holds the base types every module
builds on and has **no routes**.

## Contents of `shared`

| File | Contents |
|---|---|
| `domain/entities.py` | `BaseEntity`, `DomainError`, `DomainErrors`, `Pagination`, `PaginatedList` |
| `domain/value_objects.py` | `UNSET`, `RESOURCE_NAME_PATTERN`, `Email`, `Name`, `Phone` |
| `domain/enums.py` | `ApplicationEnvironment`, `CookieSameSite`, `ResponseMessages`, `Role`, `SortOrder` |
| `infrastructure/models.py` | `Base` (DeclarativeBase), `BaseModel` (mixin: `id`, `is_active`, `created_at`, `updated_at`) |
| `application/exceptions.py` | `StandardException`, `DomainException`, `CoreException`, `OriginNotAllowedException` |
| `application/use_cases.py` | `SharedUseCases` — notifications and user lookups |
| `presentation/schemas.py` | `StandardResponse`, `PaginationParams`, `PaginationMeta`, `CreateResponse`, `UpdateResponse`, `DeleteResponse` |
| `presentation/dependencies.py` | cross-module factories |

`BaseModel` (ORM) and `BaseEntity` (domain) both provide `id` (UUID,
`gen_random_uuid()`), `is_active` (soft-delete flag), `created_at`, `updated_at`
— **never redeclare them**.
