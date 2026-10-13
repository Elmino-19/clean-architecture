"""Domain-layer tests: pure, no I/O, no fixtures beyond direct construction."""

from datetime import date
from uuid import uuid4

import pytest

from app.modules.knowledge.domain.entities import Knowledge
from app.modules.shared.domain.entities import (
    DomainError,
    DomainErrors,
    PaginatedList,
    Pagination,
)
from app.modules.shared.domain.value_objects import UNSET, Email, Name
from app.modules.user.domain.entities import User
from app.modules.user.domain.enums import Gender


def make_user(role="user") -> User:
    return User(
        name=Name(first_name="Erfan", last_name="Rahimi"),
        email=f"{uuid4().hex[:8]}@example.com",
        gender=Gender.OTHER,
        birthdate=date(1990, 1, 1),
        role=role,
    )


class TestPagination:
    def test_defaults(self):
        pagination = Pagination()
        assert pagination.page == 1
        assert pagination.per_page == 20
        assert pagination.offset == 0

    def test_offset_is_derived_from_page(self):
        assert Pagination(page=3, per_page=10).offset == 20

    def test_rejects_page_below_one(self):
        with pytest.raises(DomainErrors) as exc:
            Pagination(page=0)
        assert "Page must be at least 1." in exc.value.errors

    def test_rejects_per_page_above_limit(self):
        with pytest.raises(DomainErrors):
            Pagination(per_page=101)

    def test_collects_every_error_at_once(self):
        with pytest.raises(DomainErrors) as exc:
            Pagination(page=0, per_page=0)
        assert len(exc.value.errors) == 2


class TestPaginatedList:
    def test_rejects_negative_total(self):
        with pytest.raises(DomainErrors):
            PaginatedList(total=-1)


class TestEmail:
    def test_normalizes_to_lowercase(self):
        assert str(Email("Foo.Bar@Example.COM")) == "foo.bar@example.com"

    def test_rejects_invalid_email(self):
        with pytest.raises(DomainError):
            Email("not-an-email")


class TestName:
    def test_rejects_too_short_first_name(self):
        with pytest.raises(DomainError) as exc:
            Name(first_name="A", last_name="Rahimi")
        assert "First name must be at least 3" in exc.value.message

    def test_rejects_digits_in_names(self):
        with pytest.raises(DomainError):
            Name(first_name="Erf4n", last_name="Rahimi")

    def test_normalizes_and_defaults_preferred_name(self):
        name = Name(first_name="  erfAN  ", last_name="rahimi")
        assert name.first_name == "Erfan"
        assert name.preferred_name == "Erfan"


class TestUser:
    def test_rejects_minor(self):
        with pytest.raises(DomainErrors) as exc:
            User(
                name=Name(first_name="Erfan", last_name="Rahimi"),
                email="kid@example.com",
                gender=Gender.OTHER,
                birthdate=date(2020, 1, 1),
            )
        assert any("at least 18" in e for e in exc.value.errors)

    def test_censors_email_for_display(self):
        user = make_user()
        assert user.censored_email != str(user.email)
        assert user.censored_email.endswith("@example.com")
        # The local part keeps only its first character.
        local = user.censored_email.split("@")[0]
        assert len(local) > 1
        assert set(local[1:]) == {"*"}


class TestKnowledge:
    def test_normalizes_and_capitalizes_name(self):
        knowledge = Knowledge(name="  machine   learning  ")
        assert knowledge.name == "Machine learning"

    def test_rejects_name_shorter_than_three(self):
        with pytest.raises(DomainErrors) as exc:
            Knowledge(name="ab")
        assert any("at least 3 characters" in e for e in exc.value.errors)

    def test_rejects_illegal_characters(self):
        with pytest.raises(DomainErrors) as exc:
            Knowledge(name="bad*name!")
        assert any("only letters" in e for e in exc.value.errors)

    def test_blank_description_becomes_none(self):
        assert Knowledge(name="Valid name", description="   ").description is None

    def test_deactivate_flips_is_active_and_records_actor(self):
        knowledge = Knowledge(name="Valid name")
        actor = make_user()
        assert knowledge.is_active is True
        knowledge.deactivate(actor)
        assert knowledge.is_active is False
        assert knowledge.updated_by is actor

    def test_description_defaults_to_unset_not_none(self):
        # UNSET means "field omitted"; None means "explicitly cleared".
        assert Knowledge(name="Valid name").description is UNSET
