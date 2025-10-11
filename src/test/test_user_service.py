import pytest
from sqlalchemy.orm import Session

from src.model.user import GroupModel, TelegramUser
from src.services.group import GroupService
from src.services.telegram_user import TelegramUserService


def test_create_telegram_user(db: Session) -> None:
    """Test creating a Telegram user."""

    service = TelegramUserService(db)
    user = service.create_user(telegram_id=12345)

    assert user.id is not None
    assert user.telegram_id == 12345

    # Test that creating the same user again returns the existing user
    user2 = service.create_user(telegram_id=12345)
    assert user2.id == user.id
    assert user2.telegram_id == user.telegram_id


def test_assign_group_to_user(db: Session) -> None:
    """Test assigning a group to a Telegram user."""

    # Create a user
    user_service = TelegramUserService(db)
    user = user_service.create_user(telegram_id=12345)
    new_user = user_service.create_user(telegram_id=67890)

    # Create a group
    group_service = GroupService(db)
    group = group_service.create_group(name="Test Group", creating_user=user)
    # Assign the group to the user
    updated_user = user_service.assign_group(group, new_user)

    assert len(updated_user.groups) == 1
    assert updated_user.groups[0].name == "Test Group"

    # Assign the same group again and ensure no duplicates
    updated_user2 = user_service.assign_group(group, new_user)
    assert len(updated_user2.groups) == 1  # Still only one group assigned

    # User Model has groups populated correctly
    assert updated_user2.groups[0].name == "Test Group"


def test_exit_from_group(db: Session) -> None:
    """Test exiting a group for a Telegram user."""

    # Create a user
    user_service = TelegramUserService(db)
    user_service.create_user(telegram_id=12345)

    user = user_service.get_grouped_user(telegram_id=12345)
    assert user is not None
    # Create a group
    group_service = GroupService(db)
    group = group_service.create_group(name="Test Group", creating_user=user)

    user_groups = user_service.get_grouped_user(telegram_id=12345)
    assert user_groups is not None
    # Ensure the user is assigned to the group
    assert len(user_groups.groups) == 1

    # Exit the group
    updated_user = user_service.exit_from_group(group, user_groups)
    assert len(updated_user.groups) == 0

    # Exiting a group that the user is not part of should not raise an error
    updated_user2 = user_service.exit_from_group(group, user_groups)
    assert len(updated_user2.groups) == 0  # Still no groups assigned

    # Test that exiting a non-existent group raises an error
    non_existent_group = group_service.get_group_by_name(name="NonExistentGroup")
    assert non_existent_group is None
    with pytest.raises(ValueError):
        user_service.exit_from_group(
            GroupModel(name="NonExistentGroup", id=999),
            TelegramUser(telegram_id=12345, id=user.id),
        )

    # Test that exiting a non-existent user raises an error
    non_existent_user = user_service.get_grouped_user(telegram_id=99999)
    assert non_existent_user is None
    with pytest.raises(ValueError):
        user_service.exit_from_group(
            group,
            TelegramUser(telegram_id=99999, id=99999),
        )


def test_kick_from_group(db: Session) -> None:
    """Test kicking a user from a group."""

    # Create users
    user_service = TelegramUserService(db)
    admin_user = user_service.create_user(telegram_id=1)
    other_admin_user = user_service.create_user(telegram_id=5)

    target_user = user_service.create_user(telegram_id=2)
    outsider_user = user_service.create_user(telegram_id=3)
    regular_user = user_service.create_user(telegram_id=4)

    # Create a group
    group_service = GroupService(db)
    group = group_service.create_group(name="Test Group", creating_user=admin_user)

    # Assign both users to the group
    target_user = user_service.assign_group(group, target_user)
    regular_user = user_service.assign_group(group, regular_user)
    other_admin_user = user_service.assign_group(group, other_admin_user)
    # Promote other_admin_user to admin
    group = group_service.promote_to_admin(group, admin_user, other_admin_user)

    # Kick the target user
    updated_target_user = user_service.kick_from_group(group, admin_user, target_user)
    assert (
        len(updated_target_user.groups) == 0
    )  # Target user should be removed from the group

    # Add target user back to the group for further tests
    target_user = user_service.assign_group(group, target_user)
    # Attempt to kick a user by a non-admin should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, regular_user, target_user)
    # Attempt to kick a user who is not in the group should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, admin_user, outsider_user)
    # Attempt to kick an admin should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, admin_user, other_admin_user)
    # Attempt to kick oneself should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, regular_user, regular_user)

    # Attempt to kick by an admin who is not in the group should raise an error
    outsider_admin = user_service.create_user(telegram_id=6)
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, outsider_admin, target_user)

    # Attempting to kick an non-existent user should raise an error
    non_existent_user = user_service.get_grouped_user(telegram_id=999)
    assert non_existent_user is None
    with pytest.raises(ValueError):
        user_service.kick_from_group(
            group,
            admin_user,
            TelegramUser(telegram_id=999, id=999),
        )

    # Attempting to kick user by non-existent admin should raise an error
    non_existent_admin = user_service.get_grouped_user(telegram_id=998)
    assert non_existent_admin is None
    with pytest.raises(ValueError):
        user_service.kick_from_group(
            group,
            TelegramUser(telegram_id=998, id=998),
            target_user,
        )
    # Attempting to kick from a non-existent group should raise an error
    non_existent_group = group_service.get_group_by_name(name="NonExistentGroup")
    assert non_existent_group is None
    with pytest.raises(ValueError):
        user_service.kick_from_group(
            GroupModel(name="NonExistentGroup", id=999),
            admin_user,
            target_user,
        )


def test_assign_group(db: Session) -> None:
    """Test assigning a user to a group."""

    user_service = TelegramUserService(db)
    group_service = GroupService(db)

    # Create users
    user1 = user_service.create_user(telegram_id=1)
    user2 = user_service.create_user(telegram_id=2)

    # Create a group
    group = group_service.create_group(name="Test Group", creating_user=user1)

    # Assign user2 to the group
    grouped_user = user_service.assign_group(group, user2)
    assert len(grouped_user.groups) == 1
    assert grouped_user.groups[0].name == "Test Group"

    # Assigning the same user again should not duplicate the group
    grouped_user = user_service.assign_group(group, user2)
    assert len(grouped_user.groups) == 1  # Still only one group

    # Attempting to assign a non-existent user should raise an error
    non_existent_user = TelegramUserService(db).get_grouped_user(telegram_id=999)
    assert non_existent_user is None
    with pytest.raises(ValueError):
        user_service.assign_group(group, TelegramUser(telegram_id=999, id=999))
    # Attempting to assign to a non-existent group should raise an error
    non_existent_group = group_service.get_group_by_name(name="NonExistentGroup")
    assert non_existent_group is None
    with pytest.raises(ValueError):
        user_service.assign_group(
            GroupModel(name="NonExistentGroup", id=999),
            TelegramUser(telegram_id=1, id=user1.id),
        )
