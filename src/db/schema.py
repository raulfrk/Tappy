"""Tappy DB schema: SQLAlchemy ORM models for User, Group, Tap and association tables.
Tappy DB schema — SQLAlchemy 2.x ORM models and association tables.

This module declares the database schema for the Tappy application using
SQLAlchemy's declarative typing (DeclarativeBase, Mapped, mapped_column).
It defines the core domain models (Group, User, Tap), plus lightweight
association tables for many-to-many relationships.

Models and key attributes
- Base
    - DeclarativeBase subclass used as the ORM base for all models.

- Group
    - id: primary key (int, autoincrement).
    - name: unique, non-nullable string.
    - users: many-to-many relationship to User via groups_users.
    - admins: many-to-many relationship to User via groups_admins.
    - __repr__ returns a short identifier useful for debugging.

- User
    - id: BigInteger primary key.
    - telegram_id: BigInteger, unique and non-nullable (business identifier).
    - telegram_username: optional string.
    - telegram_chat_id: BigInteger, non-nullable.
    - groups: many-to-many relationship to Group via groups_users.
    - admin_of_groups: many-to-many relationship to Group via groups_admins.
    - taps: one-to-many relationship for Tap instances where the user is the source
      (cascade="all, delete" to remove taps when a user is deleted).
    - taps_for_user: many-to-many relationship to Tap via taps_destination_users
      (taps targeting this user).
    - acked_taps: one-to-many relationship for Tap instances acked by this user.
    - Index: ix_users_telegram_id on (telegram_id, telegram_chat_id) to speed lookups.
    - __repr__ includes related entity ids for quick inspection.

- Tap
    - id: BigInteger primary key.
    - description: non-nullable string describing the tap.
    - source_user_id: FK -> users.id (non-nullable).
    - source_user: relationship back to User.taps.
    - destination_users: many-to-many relationship to User via taps_destination_users.
    - scheduled_datetime: non-nullable DateTime when the tap is scheduled.
    - nagging_interval_seconds: positive BigInteger with a sensible default (300).
    - acked_until: nullable DateTime until which the tap is considered acknowledged.
    - created_at, updated_at: DateTime timestamps with defaults and onupdate behavior.
    - is_active, is_deleted: boolean flags with server_default values.
    - acked_by_user_id: nullable FK -> users.id and acked_by_user relationship.
    - Several CheckConstraints to enforce temporal and numeric invariants:
        - acked_until IS NULL OR acked_until > created_at
        - scheduled_datetime > created_at
        - nagging_interval_seconds > 0
        - acked_until > scheduled_datetime OR acked_until IS NULL

Association tables
- groups_users: links users and groups (memberships).
- groups_admins: links users and groups (administrators).
- taps_destination_users: links taps and destination users.

Usage notes
- This schema targets SQLAlchemy 2.x typed declarative usage. Map columns use
  mapped_column() and typing via Mapped[] for static analysis and runtime clarity.
- Create the schema with Base.metadata.create_all(engine).
- Take care to provide appropriate BigInteger-compatible primary key handling in
  your target database (autoincrement behavior differs by backend).
- The model includes cascade deletes for taps owned by a user; other relationships
  do not cascade automatically to avoid accidental deletion of shared entities.

Examples
- Creating tables:
    engine = create_engine(<DATABASE_URL>)
    Base.metadata.create_all(engine)

- Typical object creation (using a Session):
    user = User(telegram_id=..., telegram_chat_id=..., telegram_username=...)
    group = Group(name="team")
    group.users.append(user)
    tap = Tap(
        description="Check status",
        source_user=user,
        scheduled_datetime=datetime.utcnow() + timedelta(hours=1),
    tap.destination_users.append(user)

This docstring documents the schema structure and major invariants — consult the
model definitions in this module for full field and relationship details.

Uses SQLAlchemy 2.x declarative typing (DeclarativeBase, Mapped, mapped_column).
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all ORM models in Tappy."""

    pass


groups_users = Table(
    "groups_users",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
)

groups_admins = Table(
    "groups_admins",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
)

taps_destination_users = Table(
    "taps_destination_users",
    Base.metadata,
    Column("tap_id", ForeignKey("taps.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class Group(Base):
    """ORM model for a Group in Tappy."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship(
        "User", secondary="groups_users", back_populates="groups"
    )
    admins: Mapped[list["User"]] = relationship(
        "User", secondary="groups_admins", back_populates="admin_of_groups"
    )

    def __repr__(self) -> str:
        """String representation of a Group instance for debugging."""
        return f"<Group(id={self.id})>"


class User(Base):
    """ORM model for a User in Tappy."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String, nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="groups_users", back_populates="users"
    )
    admin_of_groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="groups_admins", back_populates="admins"
    )
    taps: Mapped[list["Tap"]] = relationship(
        back_populates="source_user",
        cascade="all, delete",
        foreign_keys="Tap.source_user_id",
    )
    taps_for_user: Mapped[list["Tap"]] = relationship(
        secondary=taps_destination_users, back_populates="destination_users"
    )
    acked_taps: Mapped[list["Tap"]] = relationship(
        back_populates="acked_by_user", foreign_keys="Tap.acked_by_user_id"
    )

    __table_args__ = (Index("ix_users_telegram_id", "telegram_id", "telegram_chat_id"),)

    def __repr__(self) -> str:
        """String representation of a User instance for debugging."""
        return (
            f"<User("
            f"id={self.id}, "
            f"telegram_id={self.telegram_id}, "
            f"groups={[group.id for group in self.groups]}, "
            f"admin_of_groups={[group.id for group in self.admin_of_groups]}, "
            f"taps={[tap.id for tap in self.taps]}, "
            f"taps_for_user={[tap.id for tap in self.taps_for_user]}, "
            f"acked_taps={[tap.id for tap in self.acked_taps]}"
            f")>"
        )


class Tap(Base):
    """ORM model for a Tap: a scheduled action from a source user to one or more
    destination users."""

    __tablename__ = "taps"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    source_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    source_user: Mapped[User] = relationship(
        back_populates="taps",
        foreign_keys=[source_user_id],
    )

    destination_users: Mapped[list[User]] = relationship(
        secondary=taps_destination_users, back_populates="taps_for_user"
    )
    scheduled_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    nagging_interval_seconds: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=300
    )
    acked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )
    is_deleted: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    acked_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    acked_by_user: Mapped[User | None] = relationship(
        back_populates="acked_taps", foreign_keys=[acked_by_user_id]
    )

    __table_args__ = (
        CheckConstraint(
            "acked_until IS NULL OR acked_until > created_at",
            name="check_acked_until_after_created_at",
        ),
        CheckConstraint(
            "scheduled_datetime > created_at",
            name="check_scheduled_datetime_after_created_at",
        ),
        CheckConstraint(
            "nagging_interval_seconds > 0",
            name="check_nagging_interval_positive",
        ),
        CheckConstraint(
            "acked_until > scheduled_datetime OR acked_until IS NULL",
            name="check_acked_until_after_scheduled_datetime",
        ),
    )

    def __repr__(self) -> str:
        """String representation of a Tap instance for debugging."""
        return (
            f"<Tap("
            f"id={self.id}, "
            f"description={self.description}, "
            f"source_user_id={self.source_user_id}, "
            f"scheduled_datetime={self.scheduled_datetime}, "
            f"is_active={self.is_active}, "
            f"is_deleted={self.is_deleted}, "
            f"acked_until={self.acked_until}, "
            f"acked_by_user_id={self.acked_by_user_id}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at}, "
            f"nagging_interval_seconds={self.nagging_interval_seconds}, "
            f"destination_users={[user.id for user in self.destination_users]}, "
            f"acked_by_user={[self.acked_by_user.id if self.acked_by_user else None]}, "
            f"source_user={[self.source_user.id if self.source_user else None]}"
            f")>"
        )
