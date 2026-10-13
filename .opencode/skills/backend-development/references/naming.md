# Naming

| Thing | Pattern | Example |
|---|---|---|
| Module | `snake_case`, singular | `knowledge` |
| Entity | `PascalCase`, no suffix | `Knowledge` |
| Value object | `PascalCase`, concept name | `Email`, `Money` |
| Enum | `(str, Enum)` + Status/Type/Role/Level | `KnowledgeSortField`, `Role` |
| Domain error | `PascalCase`, base `DomainError`/`DomainErrors` | `DomainErrors` |
| Port (Protocol) | `I` + PascalCase + Repository/Cache/Service | `IKnowledgeRepository` |
| Use case class | `{Module}UseCases` (one per module) | `KnowledgeUseCases` |
| Use case method | `verb_noun` | `create`, `get_all`, `update`, `delete` |
| Mapper | module-level `{action}_{target}_mapper` | `create_entity_mapper`, `entity_model_mapper` |
| Application error | `{Rule}Exception`, base `StandardException` | `KnowledgeNotFoundException` |
| ORM model | `PascalCase` + `Model` | `KnowledgeModel` |
| Table | `{prefix}_{plural_snake}` | `f"{settings.APPLICATION_TABLE_PREFIX}_knowledges"` |
| Repository impl | `Postgres` + PascalCase + `Repository` | `PostgresKnowledgeRepository` |
| Cache impl | `Redis` + PascalCase + `Cache` | `RedisKnowledgeCache` |
| Router variable | `router` | `router = APIRouter(**router_docs)` |
| Request schema | `CreateRequest`, `UpdateRequest` | — |
| Response schema | `GetAllResponse`, `{Entity}ListItem` | `KnowledgeListItem` |
| Pagination params | `{Module}PaginationParams` | `KnowledgePaginationParams` |
| Dependency factory | `get_{thing}` | `get_knowledge_repository` |
| Foreign key | `{entity}_id` | `created_by` |
| Boolean | `is_` / `has_` | `is_active` |
| Timestamp | `{action}_at` | `created_at` |
| Actor | `{action}_by` | `created_by` |
| Unique constraint | `uq_{plural}_{cols}` | `uq_knowledges_name` |
| Index | `ix_{plural}_{cols}` | `ix_knowledges_name_is_active` |
| Check constraint | `ck_{plural}_{rule}` | `ck_keys_value_positive` |
| Enum type (PG) | `{snake}_enum` | `role_enum` |

## Section markers

Inside a file, group related code with a comment header, matching the existing
files:

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
