# Layer recipes

Concrete patterns for each file. Naming follows `references/naming.md`.

## domain/entities.py

```python
@dataclass(kw_only=True, slots=True)
class Knowledge(BaseEntity):
    name: str = field(default=None, repr=True, compare=True)
    description: str | None = field(default=UNSET, repr=False, compare=False)
    created_by: User = field(default=None, repr=False, compare=False)
    updated_by: User = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        errors: list[str] = []
        # normalise first, then validate
        if errors:
            raise DomainErrors(errors)

    def deactivate(self, updated_by: User) -> None:
        super().deactivate()
        self.updated_by = updated_by
```

- `kw_only=True, slots=True` always.
- Validation and normalisation in `__post_init__`. Collect **all** errors and
  raise them at once as `DomainErrors(errors)` — never only the first.
- Partial-update fields default to `UNSET`.
- Soft delete exposed as `deactivate(actor)`.

## domain/value_objects.py

A plain class (not a dataclass) with the order `_normalize()` → `_validate()`,
plus value-based `__str__` / `__eq__`. An invalid value raises a `DomainError`.

## domain/enums.py

Always `(str, Enum)`:

```python
class KnowledgeSortField(str, Enum):
    NAME = "name"
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
```

## application/interfaces.py

`typing.Protocol` with `...` bodies (no `@abstractmethod`):

```python
class IKnowledgeRepository(Protocol):
    async def create(self, knowledge: Knowledge) -> Knowledge: ...
    async def exists_by_name(self, knowledge: Knowledge) -> bool: ...
    async def get_by_id(self, knowledge: Knowledge) -> Knowledge | None: ...
    async def get_all(self, knowledge: Knowledge, pagination: KnowledgePagination) -> KnowledgeList: ...
    async def update(self, knowledge: Knowledge) -> Knowledge: ...
```

## application/use_cases.py

One `{Module}UseCases` class; dependencies injected in `__init__`; `async`
methods using the **3-branch** error shape:

```python
class KnowledgeUseCases:
    def __init__(self, cache: IKnowledgeCache, repository: IKnowledgeRepository,
                 shared_service: SharedUseCases) -> None:
        self.cache = cache
        self.repository = repository
        self.shared_service = shared_service

    async def create(self, knowledge: Knowledge) -> Knowledge:
        try:
            if await self.repository.exists_by_name(knowledge):
                raise KnowledgeNameAlreadyExistsException(name=knowledge.name)
            return await self.repository.create(knowledge)
        except StandardException:
            raise
        except DomainError as e:
            raise DomainException(e)
        except Exception as e:
            logger.opt(exception=e).error(
                "An unexpected error occurred during the create knowledge use case."
            )
            raise KnowledgeException()
```

- **All business rules live here.**
- Never `commit`.
- Partial update: keep the stored value wherever the incoming value `is UNSET`,
  build the merged record; if nothing changed, raise the "not modified"
  exception (400).

## application/mappers.py

Module-level functions grouped by `# ENTITY / DTOS` and `# ENTITY / MODELS`.
Uses `from automapper import mapper` (package `py-automapper`):

```python
def create_entity_mapper(payload: CreateRequest, authentication: Authentication) -> Knowledge:
    return mapper.to(Knowledge).map(
        payload,
        fields_mapping={
            "name": payload.name,
            "created_by": authentication.user,
            "updated_by": authentication.user,
        },
    )

def model_entity_mapper(model: KnowledgeModel) -> Knowledge: ...
def entity_model_mapper(knowledge: Knowledge) -> KnowledgeModel: ...
def entities_get_all_mapper(knowledge_list, pagination) -> GetAllResponse: ...
```

This file may import `presentation/schemas.py` and `infrastructure/models.py`
(the boundary exception).

## application/exceptions.py

A generic `{Module}Exception` (500) plus one exception per business rule, each
extending `StandardException`:

```python
class KnowledgeNotFoundException(StandardException):
    def __init__(self, id: str) -> None:
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            message=ResponseMessages.RESOURCE_NOT_FOUND.value,
            data={"errors": f"Knowledge with id '{id}' not found."},
        )
```

Messages always come from `ResponseMessages`, never ad-hoc strings.

## infrastructure/models.py

```python
class KnowledgeModel(BaseModel):
    __tablename__ = f"{settings.APPLICATION_TABLE_PREFIX}_knowledges"
    __table_args__ = (Index("ix_knowledges_name_is_active", "name", "is_active"),)

    name: Mapped[str] = mapped_column(String(255), name="name", nullable=False, unique=True)
    created_by: Mapped[UUID] = mapped_column(SQUID(as_uuid=True), ForeignKey(...), name="created_by")
```

- Extends `BaseModel`; **do not redeclare** `id`/`is_active`/`created_at`/`updated_at`.
- `__tablename__` always includes `settings.APPLICATION_TABLE_PREFIX`.

## infrastructure/repositories.py

`Postgres{Entity}Repository(I{Entity}Repository)`, `__init__(self, session)`,
**2-branch** error shape, and **`flush` only**:

```python
class PostgresKnowledgeRepository(IKnowledgeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, knowledge: Knowledge) -> Knowledge:
        try:
            db_knowledge = entity_model_mapper(knowledge)
            self.session.add(db_knowledge)
            await self.session.flush()          # flush, never commit
            return model_entity_mapper(db_knowledge)
        except StandardException:
            raise
        except Exception as e:
            logger.opt(exception=e).error("An error occurred in the create repository.")
            raise KnowledgeException()
```

For lists, compute the total in the **same query** with
`func.count(...).over()` — no second `COUNT(*)`. Sort only via the enum:
`getattr(Model, pagination.sort_by.value)`.

## infrastructure/caches.py

`Redis{Entity}Cache(I{Entity}Cache)`, namespaced keys, **never-raise**:

```python
class RedisKnowledgeCache(IKnowledgeCache):
    def __init__(self, cache: Redis) -> None:
        self.cache = cache
        self.prefix = f"{settings.REDIS_NAMESPACE}:knowledge:"

    def _key(self, suffix: str) -> str:
        return f"{self.prefix}{suffix}"
```

Every cache operation must catch, `logger.warning`, and return `None` — a cache
outage degrades to the database and never fails a request. If the module has no
cache, leave the file with a reason comment.

## infrastructure/services.py

Stateful or external systems behind a Protocol (e.g. `ITokenService`). If there
are none, leave the file without an implementation.

## presentation/schemas.py

Pydantic v2 with full `Field` + `ConfigDict`:

```python
model_config = ConfigDict(
    title="CreateRequest",
    str_strip_whitespace=True,
    extra="forbid",
    validate_default=True,
    validate_assignment=True,
    validate_return=True,
)
```

Names: `CreateRequest`, `UpdateRequest`, `{Entity}ListItem`, `GetAllResponse`.
`UpdateRequest` needs a `model_validator(mode="after")` requiring at least one
field. Lists use a `{Module}PaginationParams` wrapper around `PaginationParams` +
`sort_by`.

## presentation/docs.py

Two things:

- `router_docs` — `prefix`, `tags`, and shared `responses` (400/401/403/405/409/
  422/500/502/504).
- one dict per endpoint, e.g. `create_docs`, with `summary`, `status_code`,
  `response_model`, and `StandardResponse` examples. Example `data` is built from
  `ResponseMessages`.

## presentation/dependencies.py

Factories using `Annotated[T, Depends(...)]` that return the **Protocol** type,
not the concrete class:

```python
def get_knowledge_repository(session: Annotated[AsyncSession, Depends(get_async_session)]) -> IKnowledgeRepository:
    return PostgresKnowledgeRepository(session=session)

def get_knowledge_use_cases(cache, repository, shared_service) -> KnowledgeUseCases:
    return KnowledgeUseCases(cache=cache, repository=repository, shared_service=shared_service)
```

## presentation/routers.py

```python
router = APIRouter(**router_docs)

@router.post("/", **create_docs)
@router.post("", include_in_schema=False)     # both slash forms are required
async def create(
    payload: CreateRequest,
    authentication: Annotated[Authentication, Depends(authenticate_manager)],
    use_case: Annotated[KnowledgeUseCases, Depends(get_knowledge_use_cases)],
) -> CreateResponse:
    try:
        request_domain = create_entity_mapper(payload, authentication)
        response_domain = await use_case.create(request_domain)
        return entity_create_mapper(response_domain)
    except StandardException:
        raise
    except DomainError as e:
        raise DomainException(e)
    except Exception as e:
        logger.opt(exception=e).error("An error occurred in the create endpoint.")
        raise KnowledgeException()
```

- Body is exactly `payload → mapper → use case → mapper → return`.
- **Register both the trailing-slash and non-slash route.** OpenAPI shows only
  the slashed one; forgetting the other is the classic "works in Swagger, 403/404
  from the client".
- Handlers never build the envelope and never contain business logic.
- Choose the auth dependency: `no_authentication`, `authenticate_user`,
  `authenticate_manager`, `authenticate_admin`.
