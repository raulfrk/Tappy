import pytest
from sqlalchemy.orm import Session

from src.services.group import GroupService
from src.services.telegram_user import TelegramUserService


def test_create_group(db: Session) -> None:
    """Test creating a group."""

    service = GroupService(db)
    admin_user = TelegramUserService(db).create_user(telegram_id=1)
    group = service.create_group(name="Test Group", creating_user=admin_user)

    assert group.id is not None
    assert group.name == "Test Group"
    # Test that creating the same group again raises an error
    with pytest.raises(ValueError):
        service.create_group(name="Test Group", creating_user=admin_user)


def test_promote_to_admin(db: Session) -> None:
    """Test promoting a user to admin in a group."""

    # Create users
    user_service = TelegramUserService(db)
    admin_user = user_service.create_user(telegram_id=1)
    target_user = user_service.create_user(telegram_id=2)
    outsider_user = user_service.create_user(telegram_id=3)

    # Create a group
    group_service = GroupService(db)
    group = group_service.create_group(name="Test Group", creating_user=admin_user)

    # Assign the target user to the group
    target_user = user_service.assign_group(group, target_user)
    # Attempt to promote the target user to admin by a non-admin should raise an error
    with pytest.raises(ValueError):
        group_service.promote_to_admin(group, target_user, target_user)
    # Attempt to promote a user who is not in the group should raise an error
    with pytest.raises(ValueError):
        group_service.promote_to_admin(group, admin_user, outsider_user)
    # Promote the target user to admin
    group = group_service.promote_to_admin(group, admin_user, target_user)
    # Verify that the target user is now an admin
    assert len(group.admins) == 2
    admin_ids = [admin.id for admin in group.admins]
    assert admin_user.id in admin_ids
    assert target_user.id in admin_ids
    # Promoting the same user again should not raise an error and should not duplicate
    group = group_service.promote_to_admin(group, admin_user, target_user)
    assert len(group.admins) == 2  # Still only two admins
    admin_ids = [admin.id for admin in group.admins]
    assert admin_user.id in admin_ids
    assert target_user.id in admin_ids
