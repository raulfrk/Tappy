import pytest
from sqlalchemy.orm import Session

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


def test_kick_from_group(db: Session) -> None:
    """Test kicking a user from a group."""

    # Create users
    user_service = TelegramUserService(db)
    admin_user = user_service.create_user(telegram_id=1)
    target_user = user_service.create_user(telegram_id=2)
    outsider_user = user_service.create_user(telegram_id=3)
    regular_user = user_service.create_user(telegram_id=4)

    # Create a group
    group_service = GroupService(db)
    group = group_service.create_group(name="Test Group", creating_user=admin_user)

    # Assign both users to the group
    target_user = user_service.assign_group(group, target_user)
    regular_user = user_service.assign_group(group, regular_user)

    # Kick the target user
    updated_target_user = user_service.kick_from_group(group, admin_user, target_user)
    assert (
        len(updated_target_user.groups) == 0
    )  # Target user should be removed from the group

    # Attempt to kick a user by a non-admin should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, regular_user, target_user)
    # Attempt to kick a user who is not in the group should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, admin_user, outsider_user)
    # Attempt to kick an admin should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, admin_user, admin_user)
    # Attempt to kick oneself should raise an error
    with pytest.raises(ValueError):
        user_service.kick_from_group(group, regular_user, regular_user)
