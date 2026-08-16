from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from hospital_ai.db.models import Notification, User


@pytest.mark.asyncio
async def test_create_notification(session_and_settings):
    session, _ = session_and_settings
    user = User(
        email="test_notify@hospital.org",
        full_name="Dr. Notification Test",
        role="doctor",
    )
    session.add(user)
    await session.flush()

    notification = Notification(
        user_id=user.id,
        kind="system",
        title="System Update",
        body="System maintenance scheduled for tonight.",
        reference_url="https://hospital.org/updates/1",
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.kind == "system"
    assert notification.title == "System Update"
    assert notification.body == "System maintenance scheduled for tonight."
    assert notification.is_read is False
    assert notification.reference_url == "https://hospital.org/updates/1"
    assert notification.created_at is not None
    assert notification.updated_at is not None


@pytest.mark.asyncio
async def test_notification_user_relationship_cascade(session_and_settings):
    session, _ = session_and_settings
    user = User(
        email="cascade_notify@hospital.org",
        full_name="Dr. Cascade",
        role="doctor",
    )
    session.add(user)
    await session.flush()

    n1 = Notification(
        user_id=user.id,
        kind="access",
        title="Access Granted",
        body="Access granted to patient record.",
    )
    session.add(n1)
    await session.commit()

    # Re-fetch user with notifications
    await session.refresh(user, attribute_names=["notifications"])
    assert len(user.notifications) == 1
    assert user.notifications[0].title == "Access Granted"

    # Delete user
    await session.delete(user)
    await session.commit()

    # Verify notification is deleted
    res = await session.get(Notification, n1.id)
    assert res is None


@pytest.mark.asyncio
async def test_notification_invalid_kind_constraint(session_and_settings):
    session, _ = session_and_settings
    user = User(
        email="invalid_kind@hospital.org",
        full_name="Dr. Invalid Kind",
        role="doctor",
    )
    session.add(user)
    await session.flush()

    notification = Notification(
        user_id=user.id,
        kind="invalid_kind_value",
        title="Test Title",
        body="Test Body",
    )
    session.add(notification)
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
