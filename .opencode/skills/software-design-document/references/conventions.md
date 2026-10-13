# Conventions (fixed)

## Naming

| Role | Pattern | Generic example |
|---|---|---|
| Module | `snake_case`, singular | `{module}` |
| Entity | `PascalCase`, no suffix | `{Entity}` |
| Value object | `PascalCase`, concept name | `{ValueObject}` |
| Enum | `(str, Enum)` + Status/Type/Role/Level | `{Entity}Status` |
| Domain error | `PascalCase`, base `DomainError`/`DomainErrors` | `{Subject}{Verb}Error` |
| Port (Protocol) | `I` + Repository/Service/Cache | `I{Entity}Repository` |
| Use case | one class per module | `{Module}UseCases` |
| Use case method | `verb_noun` | `create`, `get_all`, `update`, `delete` |
| Mapper | module-level `{action}_{target}_mapper` | `create_entity_mapper`, `entity_model_mapper` |
| Application error | `PascalCase` + `Exception` | `{Module}Exception` |
| ORM model | `PascalCase` + `Model` | `{Entity}Model` |
| Repository impl | `Postgres` + PascalCase + `Repository` | `Postgres{Entity}Repository` |
| Cache impl | `Redis` + PascalCase + `Cache` | `Redis{Entity}Cache` |
| Router | variable `router` | `router = APIRouter(**router_docs)` |
| Schema | `CreateRequest` / `UpdateRequest` / `GetAllResponse` / `{Entity}ListItem` | `{Entity}ListItem` |
| Dependency | `get_` + snake_case | `get_{entity}_repository` |
| Table | `{prefix}_{plural_snake}` | `{prefix}_{entities}` |
| FK | `{entity}_id` | `{entity}_id` |
| Boolean | `is_` / `has_` | `is_active` |
| Timestamp | `{action}_at` | `created_at`, `deleted_at` |
| Actor | `{action}_by` | `created_by`, `deleted_by` |
| Unique constraint | `uq_{plural}_{cols}` | `uq_{entities}_{col}` |
| Index | `ix_{plural}_{cols}` | `ix_{entities}_{col}` |
| Check constraint | `ck_{plural}_{rule}` | `ck_{entities}_{rule}` |

## API contracts

### Envelope

`ResponseFormattingMiddleware` wraps every JSON response. A handler returns a
plain schema and never builds the envelope itself.

```json
{
  "code": 200,
  "method": "GET",
  "path": "/api/v1/{module}/",
  "timestamp": "2026-07-31T12:34:56Z",
  "details": { "message": "Resource retrieved successfully", "data": { } }
}
```

| Field | Meaning |
|---|---|
| `code` | HTTP status code |
| `method` / `path` | request method and path |
| `timestamp` | ISO 8601, UTC |
| `details.message` | a `ResponseMessages` constant — never an ad-hoc string |
| `details.data` | the endpoint payload, or `{"errors": ...}` on failure |

Swagger, ReDoc and `text/event-stream` responses bypass the wrapper.

### Pagination

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `page` | int | `1` | ≥ 1 |
| `limit` | int | `20` | 1–100 |
| `sort_order` | enum | `desc` | `asc` \| `desc` |
| `sort_by` | enum | per module | must be a real column |

Every list response carries a `pagination` block:

```json
{ "total": 87, "page": 2, "limit": 20, "total_pages": 5, "has_next": true, "has_prev": true }
```

The total is computed in the **same query** with a window function
(`func.count(...).over()`) — never a second `COUNT(*)` round trip. Bounded, small
lists are not paginated and the document marks them "no pagination".

### Error catalogue

| Status | Message | When |
|---|---|---|
| `400` | `VALIDATION_ERROR` | a domain rule failed — as `DomainException` |
| `400` | `BAD_REQUEST` | an update made no effective change |
| `401` | `UNAUTHORIZED_ERROR` | credential missing, invalid, revoked or expired |
| `403` | `AUTHORIZATION_ERROR` | authenticated but not permitted |
| `404` | `RESOURCE_NOT_FOUND` | record missing or soft-deleted |
| `405` | `METHOD_NOT_ALLOWED` | method unsupported on that path |
| `409` | `CONFLICT` | natural-key collision (duplicate name) |
| `422` | `VALIDATION_ERROR` | Pydantic rejected the request before the handler ran |
| `500` | `INTERNAL_ERROR` | unexpected — the module's generic exception |
| `502` | `BAD_GATEWAY` | upstream service failed |
| `504` | `GATEWAY_TIMEOUT` | upstream service timed out |

`400` and `422` are genuinely different: `422` means FastAPI rejected the request
shape; `400` means a business rule failed inside the code.

## Shared infrastructure checklist

Each item is either present or explicitly "not in this system".

| Item | Decision |
|---|---|
| Settings | `pydantic-settings`; most fields `required` so startup fails with `ValidationError` rather than at runtime |
| Database URL | derived from the `POSTGRESQL_*` keys, never set directly |
| Migration | Alembic; `upgrade head` on startup; each structural change is a separate idempotent file |
| Logging | structured JSON to stderr; a `request_id` on every request; exceptions always via `logger.opt(exception=e).error(...)` |
| Health | `GET /health/` public — DB + Redis |
| CORS | only from the configured origins |
| Rate limit | only if the product needs it |
| Docker | Postgres + Redis + pgAdmin + RedisInsight; `api` waits for both healthchecks |
| First migration | `versions/` starts empty; the first migration creates the whole schema |
