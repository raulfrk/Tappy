from sqlalchemy.orm import Session

from src.db.schema import Group, User
from src.model.user import GroupModel, TelegramGroupedUser, TelegramUser


class TelegramUserService:

    def __init__(self, session: Session):
        self._db = session

    def create_user(self, telegram_id: int, telegram_username: str) -> TelegramUser:
        db_user = self._db.query(User).filter_by(telegram_id=telegram_id).first()

        if db_user:
            # Change username if it changed on telegram
            if db_user.telegram_username != telegram_username:
                db_user.telegram_username = telegram_username
                self._db.commit()
                self._db.refresh(db_user)
            return TelegramUser.model_validate(db_user)

        new_user = User(telegram_id=telegram_id, telegram_username=telegram_username)
        self._db.add(new_user)
        self._db.commit()
        self._db.refresh(new_user)
        return TelegramUser.model_validate(new_user)

    def get_grouped_user(self, telegram_id: int) -> TelegramGroupedUser | None:
        db_user = self._db.query(User).filter_by(telegram_id=telegram_id).first()
        if db_user:
            return TelegramGroupedUser.model_validate(db_user)
        return None

    def assign_group(
        self, group: GroupModel, user: TelegramUser
    ) -> TelegramGroupedUser:
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

        Conditions:
        - The kicker user must be a member of the group.
        - The kicker user must be an admin of the group.
        - The target user must be a member of the group and not an admin.
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
