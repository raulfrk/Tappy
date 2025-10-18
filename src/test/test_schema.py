"""
Test cases for schema-related functionalities.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from sqlalchemy import UUID, inspect
from sqlalchemy.orm import Session


def future_datetime() -> datetime:
    """Generate a datetime object set 1 day in the future."""
    return datetime.now() + timedelta(days=1)


def to_primitive(obj: Any) -> Any:
    """Recursively convert objects to YAML-safe primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (Decimal, UUID)):
        return str(obj)
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except Exception:
            return obj.hex()
    if isinstance(obj, dict):
        return {str(k): to_primitive(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_primitive(v) for v in obj]
    # Catch-all: stringify anything else (e.g., SQLAlchemy types like INTEGER())
    return str(obj)


def test_appropriate_db_structure(db: Session, data_regression: Any) -> None:
    """Test that the database schema matches the expected structure using
    regressions."""
    inspector = inspect(db.bind)
    assert inspector is not None
    tables = inspector.get_table_names()
    schema_info = {}
    for table in tables:
        columns = inspector.get_columns(table)
        constraints = inspector.get_check_constraints(table)
        pk_constraints = inspector.get_pk_constraint(table)
        fk = inspector.get_foreign_keys(table)
        indexes = inspector.get_indexes(table)
        schema_info[table] = {
            "columns": pd.DataFrame(to_primitive(columns)).to_dict(orient="records"),
            "constraints": pd.DataFrame(to_primitive(constraints)).to_dict(
                orient="records"
            ),
            "primary_key": pk_constraints,
            "foreign_keys": pd.DataFrame(to_primitive(fk)).to_dict(orient="records"),
            "indexes": pd.DataFrame(to_primitive(indexes)).to_dict(orient="records"),
        }
    data_regression.check(schema_info)


def test_relationships(db: Session) -> None:
    """Test that relationships between User, Tap, and Group are set up correctly."""
    from src.db.schema import Group, Tap, User

    user1 = User(telegram_id=12345, telegram_username="abc", telegram_chat_id=1)
    user2 = User(telegram_id=67890, telegram_username="def", telegram_chat_id=2)
    group1 = Group(name="Group1")
    group2 = Group(name="Group2")

    user1.groups.append(group1)
    user2.groups.append(group1)
    user2.admin_of_groups.append(group2)

    tap1 = Tap(
        source_user=user1,
        description="Test Tap",
        scheduled_datetime=future_datetime(),
    )
    tap1.destination_users.append(user2)

    db.add_all([user1, user2, group1, group2, tap1])
    db.commit()

    assert user1 in group1.users
    assert user2 in group1.users
    assert user2 in group2.admins
    assert tap1 in user1.taps
    assert user2 in tap1.destination_users
    assert tap1.source_user == user1
    assert user1.taps[0].description == "Test Tap"
    assert user2.taps_for_user[0] == tap1
    assert tap1.created_at <= datetime.now()
    assert tap1.scheduled_datetime > datetime.now()


def test_constraints(db: Session) -> None:
    """Test that constraints are enforced correctly."""
    from src.db.schema import Tap, User

    user1 = User(telegram_id=12345, telegram_username="newuser", telegram_chat_id=1)
    db.add(user1)
    db.commit()

    # Test that acked_until must be after created_at
    tap1 = Tap(
        source_user=user1,
        description="Test Tap with invalid acked_until",
        scheduled_datetime=future_datetime(),
        created_at=datetime.now(),
        acked_until=datetime.now() - timedelta(days=1),  # Invalid
    )
    db.add(tap1)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()

    # Test that scheduled_datetime must be after created_at
    tap2 = Tap(
        source_user=user1,
        description="Test Tap with invalid scheduled_datetime",
        scheduled_datetime=datetime.now() - timedelta(days=1),  # Invalid
        created_at=datetime.now(),
    )
    db.add(tap2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()

    # Test that nagging_interval_seconds must be positive
    tap3 = Tap(
        source_user=user1,
        description="Test Tap with invalid nagging_interval_seconds",
        scheduled_datetime=future_datetime(),
        created_at=datetime.now(),
        nagging_interval_seconds=-10,  # Invalid
    )
    db.add(tap3)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()

    # Test acked_until is not before scheduled_datetime
    tap4 = Tap(
        source_user=user1,
        description="Test Tap with acked_until before scheduled_datetime",
        scheduled_datetime=future_datetime(),
        created_at=datetime.now(),
        acked_until=datetime.now()
        + timedelta(hours=1),  # Invalid if scheduled_datetime
        nagging_interval_seconds=300,
    )
    db.add(tap4)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()
