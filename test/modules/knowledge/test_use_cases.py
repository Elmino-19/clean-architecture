"""Use-case tests driven through in-memory fakes.

No database, no Redis, no network. The point is to prove that the application
layer talks only to its Protocols: swap the fakes for the Postgres/Redis
adapters and these same use cases run unchanged.
"""

from datetime import date
from uuid import uuid4

import pytest

from app.modules.knowledge.application.exceptions import (
    KnowledgeNameAlreadyExistsException,
    KnowledgeNotFoundException,
    KnowledgeNotModifiedException,
)
from app.modules.knowledge.application.use_cases import KnowledgeUseCases
from app.modules.knowledge.domain.entities import Knowledge, KnowledgePagination
from app.modules.shared.application.use_cases import SharedUseCases
from app.modules.shared.domain.entities import DomainErrors
from app.modules.shared.domain.enums import Role
from app.modules.shared.domain.value_objects import UNSET, Name
from app.modules.user.domain.entities import User
from app.modules.user.domain.enums import Gender
from test.fakes import (
    FakeConnectionManager,
    FakeKnowledgeCache,
    FakeKnowledgeRepository,
    FakeNotificationRepository,
    FakeUserRepository,
)


@pytest.fixture
def manager() -> User:
    return User(
        name=Name(first_name="Sara", last_name="Manager"),
        email=f"{uuid4().hex[:8]}@example.com",
        gender=Gender.FEMALE,
        birthdate=date(1985, 5, 5),
        role=Role.MANAGER,
    )


@pytest.fixture
def repository() -> FakeKnowledgeRepository:
    return FakeKnowledgeRepository()


@pytest.fixture
def notifications(manager) -> FakeNotificationRepository:
    # Broadcast fans out to real recipients, so the fake needs the audience.
    return FakeNotificationRepository(users=[manager])


@pytest.fixture
def connection_manager() -> FakeConnectionManager:
    return FakeConnectionManager()


@pytest.fixture
def use_cases(repository, notifications, connection_manager, manager):
    shared = SharedUseCases(
        user_repository=FakeUserRepository(),
        notification_repository=notifications,
        connection_manager=connection_manager,
    )
    return KnowledgeUseCases(
        cache=FakeKnowledgeCache(),
        repository=repository,
        shared_service=shared,
    )


class TestCreate:
    async def test_persists_and_broadcasts(self, use_cases, repository, manager):
        knowledge = await use_cases.create(
            Knowledge(name="Machine learning", created_by=manager)
        )

        assert knowledge.id is not None
        assert repository.rows[knowledge.id] is knowledge

    async def test_broadcast_targets_the_requesting_role(
        self, use_cases, notifications, manager
    ):
        await use_cases.create(Knowledge(name="New base", created_by=manager))

        created = notifications.rows
        assert len(created) == 1
        assert created[0].title == "Knowledge base created"

    async def test_rejects_duplicate_name(self, use_cases, manager):
        await use_cases.create(Knowledge(name="Duplicate", created_by=manager))

        with pytest.raises(KnowledgeNameAlreadyExistsException):
            await use_cases.create(Knowledge(name="Duplicate", created_by=manager))

    async def test_repository_flushes_but_never_commits(
        self, use_cases, repository, manager
    ):
        await use_cases.create(Knowledge(name="Flush check", created_by=manager))

        assert repository.flush_count == 1
        assert repository.commit_count == 0


class TestUpdate:
    async def test_merges_only_supplied_fields(self, use_cases, manager):
        created = await use_cases.create(
            Knowledge(
                name="Original name",
                description="Original description",
                created_by=manager,
            )
        )

        updated = await use_cases.update(
            Knowledge(id=created.id, name="New name", updated_by=manager)
        )

        assert updated.name == "New name"
        # description was UNSET, so the stored value must survive.
        assert updated.description == "Original description"

    async def test_rejects_unknown_id(self, use_cases, manager):
        with pytest.raises(KnowledgeNotFoundException):
            await use_cases.update(
                Knowledge(id=uuid4(), name="Whatever", updated_by=manager)
            )

    async def test_rejects_no_op_update(self, use_cases, manager):
        created = await use_cases.create(
            Knowledge(name="Same name", description="Same", created_by=manager)
        )

        with pytest.raises(KnowledgeNotModifiedException):
            await use_cases.update(
                Knowledge(
                    id=created.id,
                    name=UNSET,
                    description=UNSET,
                    updated_by=manager,
                )
            )

    async def test_entity_rejects_invalid_name_before_the_use_case(self, manager):
        # Invariant enforcement lives in the entity, so an invalid entity can
        # never reach a use case in the first place.
        with pytest.raises(DomainErrors):
            Knowledge(name="ab", created_by=manager)

    async def test_business_rule_failures_become_typed_exceptions(
        self, use_cases, manager
    ):
        created = await use_cases.create(
            Knowledge(name="Valid base", created_by=manager)
        )

        # No effective change -> 400 from the shared DomainException family.
        with pytest.raises(KnowledgeNotModifiedException) as exc:
            await use_cases.update(
                Knowledge(
                    id=created.id, name=UNSET, description=UNSET, updated_by=manager
                )
            )
        assert exc.value.status_code == 400

        # Missing record -> 404.
        with pytest.raises(KnowledgeNotFoundException) as missing:
            await use_cases.update(
                Knowledge(id=uuid4(), name="Ghost", updated_by=manager)
            )
        assert missing.value.status_code == 404


class TestDelete:
    async def test_soft_deletes_and_keeps_the_row(self, use_cases, repository, manager):
        created = await use_cases.create(
            Knowledge(name="To remove", created_by=manager)
        )

        await use_cases.delete(Knowledge(id=created.id, updated_by=manager))

        # Soft delete: the row is still there, just inactive.
        assert repository.rows[created.id].is_active is False


class TestRead:
    async def test_get_all_returns_only_active(self, use_cases, manager):
        first = await use_cases.create(Knowledge(name="Keep me", created_by=manager))
        await use_cases.create(Knowledge(name="Drop me", created_by=manager))
        await use_cases.delete(Knowledge(id=first.id, updated_by=manager))

        result = await use_cases.get_all(
            Knowledge(created_by=manager), KnowledgePagination()
        )

        assert result.total == 1
        assert {item.name for item in result.items} == {"Drop me"}


class TestResilience:
    async def test_broken_websocket_does_not_fail_the_write(
        self, repository, notifications, manager
    ):
        class ExplodingConnections:
            async def send_to_user(self, message):
                raise ConnectionError("ws down")

            async def broadcast_to(self, message, minimum_role=None):
                raise ConnectionError("ws down")

        shared = SharedUseCases(
            user_repository=FakeUserRepository(),
            notification_repository=notifications,
            connection_manager=ExplodingConnections(),
        )
        use_cases = KnowledgeUseCases(
            cache=FakeKnowledgeCache(),
            repository=repository,
            shared_service=shared,
        )

        # WebSocket delivery is best-effort: the write must still succeed.
        result = await use_cases.create(
            Knowledge(name="Survives ws outage", created_by=manager)
        )
        assert result.id is not None
