import pytest
from sqlalchemy.orm import Session

from src.model.user import GroupModel, TelegramUser
from src.services.group import GroupService
from src.services.telegram_user import TelegramUserService
from src.test.common_users import (
    admin_user_create,
    outsider_user_create,
    target_user_create,
)


def test_create_group(db: Session) -> None:
    """Test creating a group."""

    service = GroupService(db)
    admin_user = TelegramUserService(db).create_user(admin_user_create)
    group = service.create_group(name="Test Group", creating_user=admin_user)

    assert group.id is not None
    assert group.name == "Test Group"
    # Test that creating the same group again raises an error
    with pytest.raises(ValueError):
        service.create_group(name="Test Group", creating_user=admin_user)

    # Test that creating a group with a non-existent user raises an error
    non_existent_user = TelegramUser(telegram_id=999, id=999)
    with pytest.raises(ValueError):
        service.create_group(name="Another Group", creating_user=non_existent_user)


def test_get_group_by_name(db: Session) -> None:
    """Test getting a group by name when the group does not exist."""

    service = GroupService(db)
    group = service.get_group_by_name(name="NonExistentGroup")
    assert group is None

    # Test getting a group by name when the group exists
    admin_user = TelegramUserService(db).create_user(admin_user_create)
    created_group = service.create_group(name="ExistingGroup", creating_user=admin_user)
    fetched_group = service.get_group_by_name(name="ExistingGroup")
    assert fetched_group is not None
    assert fetched_group.id == created_group.id
    assert fetched_group.name == created_group.name


def test_promote_to_admin(db: Session) -> None:
    """Test promoting a user to admin in a group."""

    # Create users
    user_service = TelegramUserService(db)
    admin_user = user_service.create_user(admin_user_create)
    target_user = user_service.create_user(target_user_create)
    outsider_user = user_service.create_user(outsider_user_create)

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

    # Test promoting a non-existent user should raise an error
    non_existent_user = user_service.get_grouped_user(telegram_id=999)
    assert non_existent_user is None
    with pytest.raises(ValueError):
        group_service.promote_to_admin(
            group,
            admin_user,
            TelegramUser(telegram_id=999, id=999),
        )
    # Test promoting by a non-existent admin should raise an error
    non_existent_admin = user_service.get_grouped_user(telegram_id=998)
    assert non_existent_admin is None
    with pytest.raises(ValueError):
        group_service.promote_to_admin(
            group,
            TelegramUser(telegram_id=998, id=998),
            target_user,
        )
    # Test promoting in a non-existent group should raise an error
    non_existent_group = group_service.get_group_by_name(name="NonExistentGroup")
    assert non_existent_group is None
    with pytest.raises(ValueError):
        group_service.promote_to_admin(
            GroupModel(name="NonExistentGroup", id=999),
            admin_user,
            target_user,
        )
