# Cross-cutting rules

## The three error shapes

| Shape | Where | Pattern |
|---|---|---|
| **3-branch** | use case, router | `StandardException` → raise · `DomainError` → `DomainException` · `Exception` → log + `{Module}Exception` |
| **2-branch** | repository, service | `StandardException` → raise · `Exception` → log + `{Module}Exception` |
| **never-raise** | cache | catch · `logger.warning` · `return None` |

`except StandardException` must always be **first**. `StandardException` extends
`HTTPException`, so any other order swallows every deliberate 404/409 into a 500.

The 2-branch shape has no `DomainError` arm: those layers never evaluate domain
rules. The never-raise shape has no re-raise arm at all.

## Transactions

- Repositories **`flush`**, never `commit`/`rollback`.
- Use cases never call `commit`.
- The only `commit`/`rollback` lives in the session dependencies (`get_session`
  for sync/migrations, `get_async_session` for the request path) in
  `app/core/database.py`; `get_async_session` commits after the request succeeds.
- **There is no `IUnitOfWork`. Do not add one.**

## Response envelope

`ResponseFormattingMiddleware` wraps every JSON response. A handler returns a
plain schema; it never constructs this:

```json
{
  "code": 200, "method": "GET", "path": "/api/v1/{module}/",
  "timestamp": "2026-01-01T00:00:00Z",
  "details": { "message": "...", "data": { } }
}
```

`details.message` is always a `ResponseMessages` constant. Swagger, ReDoc and
`text/event-stream` responses bypass the wrapper.

## Soft delete

No physical deletes. `entity.deactivate(actor)` sets `is_active=false`; the
repository `update`s the row; every read filters `is_active.is_(True)`.

## The `UNSET` sentinel

Distinguishes "field omitted" from "field explicitly null". It flows through
three places:

1. the entity defaults the field to `UNSET`;
2. the update mapper sets it from `payload.model_fields_set`
   (`payload.name if "name" in payload.model_fields_set else UNSET`);
3. the use case keeps the stored value wherever the incoming value `is UNSET`.

Always compare with `is` / `is not`, never `==`.

## Pagination

`PaginationParams` (page / limit / sort_order) + `PaginationMeta` (total / page /
limit / total_pages / has_next / has_prev). Compute `total` in the **same query**
with `func.count(...).over()`. `sort_by` comes only from the module's sort enum.
Bounded, small lists are not paginated.

## Authentication

Pick the dependency by access tier:

| Dependency | Reaches |
|---|---|
| `no_authentication` | public |
| `authenticate_user` | any authenticated user |
| `authenticate_manager` | manager and above |
| `authenticate_admin` | admin only |

Each path is declared once in the lowest tier that should reach it, in both slash
forms.

## Enum values in PostgreSQL

PostgreSQL stores enum **member names** uppercase (`ADMIN`, `KNOWLEDGE_CREATED`),
not the Python values. Keep this in mind for raw SQL and seed migrations.

## Time

Store timestamps with timezone. Business-timezone conversion happens only at the
edge; this template keeps a single timezone constant in
`shared/application/utils.py`.

## Tests (unit-first)

Drive use cases with **in-memory fakes of their Protocols**; construct entities
directly; touch no database, Redis or network. Fakes live in `test/fakes.py` —
add a fake when a module brings a new port. Tests mirror `app/modules` under
`test/modules/`. `pytest` runs with `asyncio_mode = "auto"`.

```python
async def test_rejects_duplicate_name(use_cases, manager):
    await use_cases.create(Knowledge(name="Duplicate", created_by=manager))
    with pytest.raises(KnowledgeNameAlreadyExistsException):
        await use_cases.create(Knowledge(name="Duplicate", created_by=manager))
```

## The global response contract

- `400` — a domain rule failed (`DomainException`) or "no effective change".
- `401` — missing/invalid/revoked/expired credential.
- `403` — authenticated but not permitted.
- `404` — missing or soft-deleted.
- `405` — method not allowed on that path.
- `409` — natural-key collision (duplicate name).
- `422` — Pydantic rejected the payload before the handler ran.
- `500` — unexpected; the module's generic exception.
- `502` — an upstream service failed.
- `504` — an upstream service timed out.
