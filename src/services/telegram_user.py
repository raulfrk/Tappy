"""Service module for managing Telegram users."""

from typing import TYPE_CHECKING

import loguru
from sqlalchemy.orm import Session

from src.db.schema import Group, User
from src.model.user import (
    GroupModel,
    TelegramGroupedUser,
    TelegramUser,
    TelegramUserCreate,
)

if TYPE_CHECKING:
    from loguru import Logger


class TelegramUserService:
    """Service for managing Telegram users. Provides methods to create users,
    retrieve grouped users, assign users to groups, exit users from groups,
    and kick users from groups."""

    def __init__(self, session: Session, log: "Logger" = loguru.logger):
        """Initialize the TelegramUserService with a database session and logger."""
        self._db = session
        self._log = log
        self._log = self._log.bind(service="TelegramUserService")

    def create_user(self, t_user_create: TelegramUserCreate) -> TelegramUser:
        """
        Create a new Telegram user or update an existing user's username.
        This method will:
        - Check if a user with the given telegram_id already exists.
        - If the user exists and the username has changed, update the username.
        - If the user does not exist, create a new User record.
        - Persist changes to the database and return a validated TelegramUser model.
        Args:
            t_user_create (TelegramUserCreate): The data required to create or update
            a Telegram user.
        Returns:
            TelegramUser: A validated model representing the created or updated user.
        """
        db_user = (
            self._db.query(User)
            .filter_by(telegram_id=t_user_create.telegram_id)
            .first()
        )
        self._log.info("handling user create", request=t_user_create)
        if db_user:
            # Change username if it changed on telegram
            if db_user.telegram_username != t_user_create.telegram_username:
                self._log.info(
                    "user changed username, updating db",
                    old_username=db_user.telegram_username,
                    new_username=t_user_create.telegram_username,
                )
                db_user.telegram_username = t_user_create.telegram_username
                self._db.commit()
                self._db.refresh(db_user)
            return TelegramUser.model_validate(db_user)

        new_user = User(**t_user_create.model_dump())
        self._db.add(new_user)
        self._db.commit()
        self._db.refresh(new_user)
        return TelegramUser.model_validate(new_user)

    def get_grouped_user(self, telegram_id: int) -> TelegramGroupedUser | None:
        """Retrieve a Telegram user along with their group memberships.
        This method will:
        - Query the database for a user with the given telegram_id.
        - If found, return a validated TelegramGroupedUser model including group data.
        - If not found, return None.
        Args:
            telegram_id (int): The Telegram ID of the user to retrieve.

        Returns:
            (TelegramGroupedUser | None): A validated model representing the user and
            their groups, or None if the user does not exist.
        """
        db_user = self._db.query(User).filter_by(telegram_id=telegram_id).first()
        if db_user:
            return TelegramGroupedUser.model_validate(db_user)
        return None

    def assign_group(
        self, group: GroupModel, user: TelegramUser
    ) -> TelegramGroupedUser:
        """Assign a user to a group.
        This method will:
        - Verify that both the user and group exist in the database.
        - Add the group to the user's memberships if not already present.
        - Persist changes to the database and return a validated TelegramGroupedUser
          model.
        Args:
            group (GroupModel): The group to assign the user to.
            user (TelegramUser): The user to be assigned to the group.
        Returns:
            TelegramGroupedUser: A validated model representing the user and their
            updated group memberships.

        Raises:
            ValueError: If the user does not exist in the database.
            ValueError: If the group does not exist in the database.
        """
        db_user = self._db.query(User).filter_by(telegram_id=user.telegram_id).first()
        if not db_user:
            raise ValueError(
                f"User with telegram_id '{user.telegram_id}' does not exist."
            )
        db_group = self._db.query(Group).filter_by(name=group.name).first()
        if not db_group:
            raise ValueError(f"Group with name '{group.name}' does not exist.")
        if db_group not in db_user.groups:
            db_user.groups.append(db_group)
            self._db.commit()
        self._db.refresh(db_user)
        return TelegramGroupedUser.model_validate(db_user)

    def exit_from_group(
        self, group: GroupModel, user: TelegramUser
    ) -> TelegramGroupedUser:
        """Remove a user from a group.
        This method will:
        - Verify that both the user and group exist in the database.
        - Remove the group from the user's memberships if present.
        - Persist changes to the database and return a validated TelegramGroupedUser
          model.
        Args:
            group (GroupModel): The group to remove the user from.
            user (TelegramUser): The user to be removed from the group.
        Returns:
            TelegramGroupedUser: A validated model representing the user and their
            updated group memberships.
        Raises:
            ValueError: If the user does not exist in the database.
            ValueError: If the group does not exist in the database.
        """
        db_user = self._db.query(User).filter_by(telegram_id=user.telegram_id).first()
        if not db_user:
            raise ValueError(
                f"User with telegram_id '{user.telegram_id}' does not exist."
            )
        db_group = self._db.query(Group).filter_by(name=group.name).first()
        if not db_group:
            raise ValueError(f"Group with name '{group.name}' does not exist.")
        if db_group in db_user.groups:
            db_user.groups.remove(db_group)
            self._db.commit()
        self._db.refresh(db_user)
        return TelegramGroupedUser.model_validate(db_user)

    def kick_from_group(
        self, group: GroupModel, kicking_user: TelegramUser, target_user: TelegramUser
    ) -> TelegramGroupedUser:
        """Kick a user from a group.

        This method will:
        - Verify that the kicking_user and target_user exist in the database.
        - Verify that the kicking_user is not trying to kick themselves.
        - Verify that the group exists in the database.
        - Verify that both users are members of the group.
        - Verify that the kicking_user is an admin of the group.
        - Verify that the target_user is not an admin of the group.
        - Remove the target_user from the group's memberships.
        - Persist changes to the database and return a validated TelegramGroupedUser
          model.
        Args:
            group (GroupModel): The group from which to kick the user.
            kicking_user (TelegramUser): The user performing the kick action.
            target_user (TelegramUser): The user to be kicked from the group.
        Returns:
            TelegramGroupedUser: A validated model representing the target user and
            their updated group memberships.
        Raises:
            ValueError: If the kicking_user does not exist in the database.
            ValueError: If the target_user does not exist in the database.
            ValueError: If the kicking_user is trying to kick themselves.
            ValueError: If the group does not exist in the database.
            ValueError: If the kicking_user is not a member of the group.
            ValueError: If the target_user is not a member of the group.
            ValueError: If the kicking_user is not an admin of the group.
            ValueError: If the target_user is an admin of the group.
        """

        kicking_user_db: User | None = (
            self._db.query(User).filter_by(telegram_id=kicking_user.telegram_id).first()
        )
        if not kicking_user_db:
            raise ValueError(
                f"Kicking user with telegram_id '{kicking_user.telegram_id}' does "
                "not exist."
            )
        target_user_db: User | None = (
            self._db.query(User).filter_by(telegram_id=target_user.telegram_id).first()
        )
        if not target_user_db:
            raise ValueError(
                f"Target user with telegram_id '{target_user.telegram_id}' does "
                "not exist."
            )

        if kicking_user_db.telegram_id == target_user_db.telegram_id:
            raise ValueError("A user cannot kick themselves from a group.")
        group_db = self._db.query(Group).filter_by(name=group.name).first()
        if not group_db:
            raise ValueError(f"Group with name '{group.name}' does not exist.")
        if group_db not in kicking_user_db.groups:
            raise ValueError("Kicking user is not a member of the group.")
        if group_db not in target_user_db.groups:
            raise ValueError("Target user is not a member of the group.")
        if group_db not in kicking_user_db.admin_of_groups:
            raise ValueError("Kicking user is not an admin of the group.")
        if group_db in target_user_db.admin_of_groups:
            raise ValueError("Target user is an admin of the group.")

        target_user_db.groups.remove(group_db)
        self._db.commit()
        self._db.refresh(target_user_db)
        return TelegramGroupedUser.model_validate(target_user_db)
