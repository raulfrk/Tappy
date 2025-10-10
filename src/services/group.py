from sqlalchemy.orm import Session

from src.db.schema import Group, User
from src.model.user import GroupModel, UserModel


class GroupService:
    def __init__(self, session: Session):
        self._db = session

    def create_group(self, name: str, creating_user: UserModel) -> GroupModel:
        if self._db.query(Group).filter_by(name=name).first():
            raise ValueError(f"Group with name '{name}' already exists.")
        creator_user = self._db.query(User).filter_by(id=creating_user.id).first()
        if not creator_user:
            raise ValueError(
                f"Creating user with id '{creating_user.id}' does not exist."
            )
        new_group = Group(name=name)
        new_group.users.append(creator_user)
        new_group.admins.append(creator_user)
        self._db.add(new_group)
        self._db.commit()
        self._db.refresh(new_group)
        return GroupModel.model_validate(new_group)

    def get_group_by_name(self, name: str) -> GroupModel | None:
        db_group = self._db.query(Group).filter_by(name=name).first()
        if db_group:
            return GroupModel.model_validate(db_group)
        return None

    def promote_to_admin(
        self, group: GroupModel, admin_user: UserModel, new_admin_user: UserModel
    ) -> GroupModel:
        db_group = self._db.query(Group).filter_by(name=group.name).first()
        if not db_group:
            raise ValueError(f"Group with name '{group.name}' does not exist.")
        db_admin_user = self._db.query(User).filter_by(id=admin_user.id).first()
        if not db_admin_user:
            raise ValueError(f"Admin user with id '{admin_user.id}' does not exist.")
        if db_admin_user not in db_group.admins:
            raise ValueError(
                f"User with id '{admin_user.id}' is not an admin of group "
                f"'{group.name}'."
            )
        db_new_admin_user = self._db.query(User).filter_by(id=new_admin_user.id).first()
        if not db_new_admin_user:
            raise ValueError(
                f"New admin user with id '{new_admin_user.id}' does not exist."
            )
        if db_new_admin_user not in db_group.users:
            raise ValueError(
                f"User with id '{new_admin_user.id}' is not a member of group "
                f"'{group.name}'."
            )
        if db_new_admin_user not in db_group.admins:
            db_group.admins.append(db_new_admin_user)
            self._db.commit()
        self._db.refresh(db_group)
        return GroupModel.model_validate(db_group)
