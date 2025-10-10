from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
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
        return f"<Group(id={self.id})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
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

    def __repr__(self) -> str:
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
    __tablename__ = "taps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
        Integer, nullable=False, default=300
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
