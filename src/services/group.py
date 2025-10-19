"""Service module for managing groups within the application."""

from sqlalchemy.orm import Session

from src.db.schema import Group, User
from src.model.user import GroupModel, UserModel


class GroupService:
    """Service for managing groups. Provides methods to create groups,
    retrieve groups, and promote users to admin status within groups."""

    def __init__(self, session: Session):
        self._db = session

    def create_group(self, name: str, creating_user: UserModel) -> GroupModel:
        """Create a new group and add the creating user as both a member and an admin.

        This method will:
        - Check for an existing group with the given name and raise if one exists.
        - Verify the creating_user exists in the database and raise if not.
        - Create a new Group record with the provided name.
        - Add the creating user to the group's members and admins.
        - Persist the new group to the database and return a validated GroupModel.

        Args:
            name (str): The desired unique name for the new group.
            creating_user (UserModel): The user who creates the group; must exist
            in the database.

        Returns:
            GroupModel: A validated model representing the newly created group,
            including its users and admins.

        Raises:
            ValueError: If a group with the given name already exists.
            ValueError: If the creating_user does not exist in the database.

        Side effects:
            - Inserts a new Group into the database.
            - Adds database relationships between the group and the creating user.
            - Commits the transaction and refreshes the returned object from the DB.
        """
        if self._db.query(Group).filter_by(name=name).first():
            raise ValueError(f"Group with name '{name}' already exists.")

        creator_user = self._db.query(User).filter_by(id=creating_user.id).first()
        if not creator_user:
            raise ValueError(
                f"Creator user with id '{creating_user.id}' does not exist."
            )

        new_group = Group(name=name)
        new_group.users.append(creator_user)
        new_group.admins.append(creator_user)

        self._db.add(new_group)
        self._db.commit()
        self._db.refresh(new_group)

        return GroupModel.model_validate(new_group)

    def get_group_by_name(self, name: str) -> GroupModel | None:
        """
        Retrieve a group by its name.

        This method will:
        - Query the database for a Group with the exact given name.
        - Return a validated GroupModel if found, otherwise None.

        Args:
            name (str): Exact, case-sensitive name of the group to look up.

        Returns:
            (GroupModel | None): A validated GroupModel

        Notes:
            - The query uses filter_by(name=name) and returns the first match;
              if multiple rows share the same name only the first is returned.
            - This is a read-only operation and does not commit or modify the
              database session.
        """

        db_group = self._db.query(Group).filter_by(name=name).first()
        if db_group:
            return GroupModel.model_validate(db_group)
        return None

    def promote_to_admin(
        self, group: GroupModel, admin_user: UserModel, new_admin_user: UserModel
    ) -> GroupModel:
        """Promote a user to admin status within a group.

        This method will:
        - Verify the group exists in the database.
        - Verify the admin_user exists and is an admin of the group.
        - Verify the new_admin_user exists and is a member of the group.
        - Add the new_admin_user to the group's admins if not already an admin.
        - Commit the changes and return the updated GroupModel.

        Args:
            group (GroupModel): The group in which to promote a user.
            admin_user (UserModel): The current admin performing the promotion.
            new_admin_user (UserModel): The user to be promoted to admin.

        Returns:
            GroupModel: The updated group with the new admin included.
        Raises:
            ValueError: If the group does not exist.
            ValueError: If the admin_user does not exist or is not an admin of the group
            ValueError: If the new_admin_user does not exist or is not a member of the
            group
        """
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
