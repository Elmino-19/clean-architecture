"""In-memory fakes for every port the application layer depends on.

This is what the Protocol-based architecture buys you: a use case can be driven
end to end with no database, no Redis and no network. Each fake honours the same
contract as its Postgres/Redis counterpart, so a test written against a fake
keeps working when the real adapter is swapped in.

Repositories follow the template rule — they `flush`, they never `commit`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.modules.knowledge.domain.entities import Knowledge, KnowledgeList
from app.modules.notification.domain.entities import Notification
from app.modules.shared.domain.enums import Role
from app.modules.user.domain.entities import User
from app.modules.websocket.domain.entities import WebSocketMessage


class FakeUserRepository:
    """Implements IUserRepository."""

    def __init__(self) -> None:
        self.rows: dict[object, User] = {}

    async def create(self, user: User) -> User:
        if user.id is None:
            user.id = uuid4()
        user.created_at = user.created_at or datetime.now()
        self.rows[user.id] = user
        return user

    async def exists_by_email(self, user: User) -> bool:
        return any(row.email == user.email for row in self.rows.values())

    async def get_by_id(self, user: User) -> User | None:
        return self.rows.get(user.id)

    async def get_by_email(self, user: User) -> User | None:
        return next(
            (row for row in self.rows.values() if row.email == user.email), None
        )


class FakeNotificationRepository:
    """Implements INotificationRepository."""

    def __init__(self, users: list[User] | None = None) -> None:
        self.rows: list[Notification] = []
        self.users = users or []

    async def create(self, notification: Notification) -> Notification:
        if notification.id is None:
            notification.id = uuid4()
        self.rows.append(notification)
        return notification

    async def create_broadcast(self, notification: Notification) -> list[Notification]:
        """Fan out to every user whose role is at or above the target."""
        created: list[Notification] = []
        for user in self.users:
            if user.role.value >= notification.originated_from_broadcast.value:
                clone = Notification(
                    user=user,
                    notification_type=notification.notification_type,
                    title=notification.title,
                    body=notification.body,
                    originated_from_broadcast=notification.originated_from_broadcast,
                )
                await self.create(clone)
                created.append(clone)
        return created

    async def get_by_id(self, notification: Notification) -> Notification | None:
        return next((row for row in self.rows if row.id == notification.id), None)

    async def get_all_by_user(self, notification: Notification) -> list[Notification]:
        return [row for row in self.rows if row.user.id == notification.user.id]

    async def update(self, notification: Notification) -> Notification:
        for index, row in enumerate(self.rows):
            if row.id == notification.id:
                self.rows[index] = notification
                return notification
        raise ValueError(f"notification {notification.id} not found")


class FakeConnectionManager:
    """Implements IConnectionManagerService; records what would be sent."""

    def __init__(self) -> None:
        self.sent: list[WebSocketMessage] = []
        self.broadcasts: list[tuple[WebSocketMessage, Role | None]] = []

    async def connect(self, websocket, user: User) -> None:
        return None

    async def disconnect(self, websocket, user: User) -> None:
        return None

    async def send_to_user(self, message: WebSocketMessage) -> None:
        self.sent.append(message)

    async def broadcast_to(
        self, message: WebSocketMessage, minimum_role: Role | None = None
    ) -> None:
        self.broadcasts.append((message, minimum_role))


class FakeKnowledgeRepository:
    """Implements IKnowledgeRepository, including the exists_by_name rules."""

    def __init__(self) -> None:
        self.rows: dict[object, Knowledge] = {}
        self.flush_count = 0
        self.commit_count = 0

    async def create(self, knowledge: Knowledge) -> Knowledge:
        if knowledge.id is None:
            knowledge.id = uuid4()
        knowledge.created_at = knowledge.created_at or datetime.now()
        self.rows[knowledge.id] = knowledge
        self.flush_count += 1
        return knowledge

    async def exists_by_name(self, knowledge: Knowledge) -> bool:
        return any(row.name == knowledge.name for row in self.rows.values())

    async def get_by_id(self, knowledge: Knowledge) -> Knowledge | None:
        return self.rows.get(knowledge.id)

    async def get_all(self, knowledge: Knowledge, pagination) -> KnowledgeList:
        items = [row for row in self.rows.values() if row.is_active]
        return KnowledgeList(items=items, total=len(items))

    async def update(self, knowledge: Knowledge) -> Knowledge:
        if knowledge.id not in self.rows:
            raise ValueError(f"knowledge {knowledge.id} not found")
        self.rows[knowledge.id] = knowledge
        self.flush_count += 1
        return knowledge


class FakeKnowledgeCache:
    """Implements IKnowledgeCache. Never raises, exactly like Redis{Cache}."""

    def __init__(self) -> None:
        self.entries: dict[str, Knowledge] = {}

    async def insert(self, knowledge: Knowledge) -> None:
        self.entries[str(knowledge.id)] = knowledge

    async def insert_many(self, knowledge_list: KnowledgeList) -> None:
        for item in knowledge_list.items:
            await self.insert(item)


class ExplodingCache:
    """A cache that always fails — proves use cases degrade to the database."""

    async def insert(self, knowledge: Knowledge) -> None:
        raise ConnectionError("redis is down")

    async def insert_many(self, knowledge_list: KnowledgeList) -> None:
        raise ConnectionError("redis is down")
