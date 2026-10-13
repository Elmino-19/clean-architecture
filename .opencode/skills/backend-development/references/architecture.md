# Architecture

## Module tree

Every module is a bounded context with exactly these four folders:

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
│   ├── mappers.py           # module-level functions that cross boundaries
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
    ├── routers.py           # payload → mapper → use case → mapper → return
    ├── schemas.py           # Pydantic v2 with Field + ConfigDict
    ├── docs.py              # router_docs + {action}_docs
    └── dependencies.py      # Depends factories returning the Protocol type
```

**Empty file rule.** If a file has no implementation yet (e.g. the module has no
cache), it is still created — with a comment stating why, never deleted:

```python
# No cache in this phase — reason: read volume is low, cache adds no value yet.
```

A missing file means "no decision taken"; an empty-but-documented file means
"this module does not cache".

## Import rules

| Layer | May import |
|---|---|
| `domain` | `shared`, other modules' `domain`. **No** FastAPI, SQLAlchemy, Pydantic, Redis, I/O |
| `application` | `domain`, `shared`, other modules' `domain`/`application` |
| `infrastructure` | `domain`, `application`, `core`, `shared` |
| `presentation` | all layers below it, plus `core` |

### The two sanctioned exceptions

1. **`application/mappers.py` may import** `presentation/schemas.py` and
   `infrastructure/models.py`. A mapper exists precisely to cross those
   boundaries, so it is allowed to know both sides. No other file in
   `application` gets this pass.
2. **Composition roots** (`app/app.py`, each module's
   `presentation/dependencies.py`, and `shared/presentation/dependencies.py`)
   may import `infrastructure` implementations to wire ports to adapters.

## Cross-module dependencies (DAG)

Cross-module imports are allowed **only into another module's `domain` or
`application`**. Never import another module's `infrastructure` or
`presentation`. The graph must stay acyclic.

Real examples: `knowledge` uses `authentication.domain` and `user.domain`;
mappers use `shared.domain.value_objects.UNSET`.

## The `shared` module

`shared` is a module too, but has no routes. Every module builds on it.

| File | Contents |
|---|---|
| `domain/entities.py` | `BaseEntity`, `DomainError`, `DomainErrors`, `Pagination`, `PaginatedList` |
| `domain/value_objects.py` | `UNSET`, `RESOURCE_NAME_PATTERN`, `Email`, `Name`, `Phone` |
| `domain/enums.py` | `ApplicationEnvironment`, `CookieSameSite`, `ResponseMessages`, `Role`, `SortOrder` |
| `infrastructure/models.py` | `Base`, `BaseModel` |
| `application/exceptions.py` | `StandardException`, `DomainException`, `CoreException`, `OriginNotAllowedException` |
| `application/use_cases.py` | `SharedUseCases` — notifications and user lookups |
| `presentation/schemas.py` | `StandardResponse`, `PaginationParams`, `PaginationMeta`, `CreateResponse`, `UpdateResponse`, `DeleteResponse` |
| `presentation/dependencies.py` | cross-module factories |

**Inherited fields — never redeclare.** `BaseModel` (ORM) and `BaseEntity`
(domain) both provide `id` (UUID, `gen_random_uuid()`), `is_active` (soft-delete
flag), `created_at`, `updated_at`.

## Project layout

```text
app/
├── app.py               # FastAPI instance + router registration + startup
├── core/                # settings, security, database, cache, middleware, migrations, logging
├── modules/
│   ├── shared/          # base types — no routes
│   └── {module}/        # four folders, as above
migrations/versions/     # Alembic — first migration creates the whole schema
test/                    # mirrors app/modules + fakes.py
```
