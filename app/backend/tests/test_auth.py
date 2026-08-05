"""Tests for the /me authentication endpoint and its get_current_user dependency.

These tests exercise the auth logic in get_current_user: JWT validation,
static bearer token fallback, missing/invalid credentials, inactive users,
and malformed Authorization headers.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import update

from hospital_ai.api.deps import get_current_user
from hospital_ai.api.routes.auth import login_for_access_token, me
from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import User
from hospital_ai.schemas.auth import UserRead

# ---------------------------------------------------------------------------
# /me handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_returns_current_user(session_and_settings):
    """GET /me returns the authenticated user object unchanged."""
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await me(current_user=doctor)

    assert response.id == DOCTOR_ID
    assert response.email == "doctor@example.test"
    assert response.full_name == "Dr. Dev Doctor"
    assert response.role == "doctor"
    assert response.is_active is True

    # Verify the response matches the UserRead schema shape
    assert isinstance(UserRead.from_orm(response), UserRead)


# ---------------------------------------------------------------------------
# /auth/token handler
# ---------------------------------------------------------------------------


def _dummy_request() -> Request:
    """Minimal ASGI Request so the rate-limit decorator can derive a client key."""
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/token",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
    )


@pytest.mark.asyncio
async def test_login_for_access_token_success(session_and_settings):
    """POST /auth/token returns token for valid seeded user with 'demo' password."""
    from fastapi.security import OAuth2PasswordRequestForm

    session, settings = session_and_settings
    form_data = OAuth2PasswordRequestForm(
        username="doctor@example.test",
        password="demo",
        scope="",
        client_id=None,
        client_secret=None,
        grant_type="password",
    )

    response = await login_for_access_token(
        request=_dummy_request(), form_data=form_data, session=session, settings=settings
    )
    assert response.access_token == "dev-doctor"
    assert response.user.email == "doctor@example.test"
    assert response.user.role == "doctor"


@pytest.mark.asyncio
async def test_login_for_access_token_invalid_password(session_and_settings):
    """POST /auth/token returns 401 for invalid password."""
    from fastapi.security import OAuth2PasswordRequestForm

    session, settings = session_and_settings
    form_data = OAuth2PasswordRequestForm(
        username="doctor@example.test",
        password="wrong",
        scope="",
        client_id=None,
        client_secret=None,
        grant_type="password",
    )

    with pytest.raises(HTTPException) as exc_info:
        await login_for_access_token(request=_dummy_request(), form_data=form_data, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_login_for_access_token_unknown_user(session_and_settings):
    """POST /auth/token returns 401 for unknown user."""
    from fastapi.security import OAuth2PasswordRequestForm

    session, settings = session_and_settings
    form_data = OAuth2PasswordRequestForm(
        username="unknown@example.test",
        password="demo",
        scope="",
        client_id=None,
        client_secret=None,
        grant_type="password",
    )

    with pytest.raises(HTTPException) as exc_info:
        await login_for_access_token(request=_dummy_request(), form_data=form_data, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User is not active or seeded" in exc_info.value.detail


# ---------------------------------------------------------------------------
# get_current_user -- static bearer token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_valid_static_token(session_and_settings):
    """A known static bearer token (dev-doctor) resolves to the doctor user."""
    session, settings = session_and_settings
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-doctor")

    user = await get_current_user(credentials=credentials, session=session, settings=settings)

    assert user.id == DOCTOR_ID
    assert user.email == "doctor@example.test"
    assert user.full_name == "Dr. Dev Doctor"
    assert user.role == "doctor"
    assert user.is_active is True


# ---------------------------------------------------------------------------
# get_current_user -- JWT token (HS256)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_valid_jwt_token(session_and_settings):
    """A valid HS256 JWT with known claims resolves to the correct user."""
    import jwt as pyjwt

    session, settings = session_and_settings

    # Enable JWT validation in settings for this test
    settings.jwt_issuer = "test-issuer"
    settings.jwt_hmac_secret = "test-secret"
    settings.jwt_algorithm = "HS256"

    token = pyjwt.encode(
        {
            "sub": str(DOCTOR_ID),
            "email": "doctor@example.test",
            "name": "Dr. Dev Doctor",
            "role": "doctor",
            "iss": "test-issuer",
        },
        "test-secret",
        algorithm="HS256",
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await get_current_user(credentials=credentials, session=session, settings=settings)

    assert user.id == DOCTOR_ID
    assert user.email == "doctor@example.test"
    assert user.role == "doctor"


@pytest.mark.asyncio
async def test_get_current_user_jwt_fallback_to_static(session_and_settings):
    """A JWT-validated user not in the local DB falls through to static tokens."""
    import jwt as pyjwt

    session, settings = session_and_settings

    # Enable JWT but sign for a non-existent email
    settings.jwt_issuer = "test-issuer"
    settings.jwt_hmac_secret = "test-secret"
    settings.jwt_algorithm = "HS256"

    token = pyjwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "email": "ghost@example.test",
            "name": "Ghost User",
            "role": "doctor",
            "iss": "test-issuer",
        },
        "test-secret",
        algorithm="HS256",
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # This token is NOT in the static map either, so it should 401
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User validated via JWT but no active local account found." in exc_info.value.detail


# ---------------------------------------------------------------------------
# get_current_user -- error cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(session_and_settings):
    """An unknown bearer token returns 401."""
    session, settings = session_and_settings
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="nonexistent")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Unknown bearer token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_no_credentials(session_and_settings):
    """Missing credentials (None) returns 401 with appropriate detail."""
    session, settings = session_and_settings

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing bearer token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(session_and_settings):
    """A valid static token for a deactivated user returns 401."""
    session, settings = session_and_settings

    # Deactivate the doctor
    await session.execute(update(User).where(User.id == DOCTOR_ID).values(is_active=False))
    await session.commit()

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-doctor")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "not active" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_malformed_header(session_and_settings):
    """A non-Bearer Authorization scheme returns 401."""
    session, settings = session_and_settings
    credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="dev-doctor")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing bearer token" in exc_info.value.detail
