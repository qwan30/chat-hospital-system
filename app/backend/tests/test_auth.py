"""Tests for the /me authentication endpoint and its get_current_user dependency.

These tests exercise the auth logic in get_current_user: JWT validation,
static bearer token fallback, missing/invalid credentials, inactive users,
and malformed Authorization headers.
"""

import pytest
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy import update

from hospital_ai.api.deps import get_current_user
from hospital_ai.api.routes.auth import demo_login, demo_status, login_for_access_token, me
from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import User
from hospital_ai.schemas.auth import DemoLoginRequest, UserRead

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


# ---------------------------------------------------------------------------
# Backend-issued demo authentication
# ---------------------------------------------------------------------------


def _demo_settings(settings):
    settings.demo_jwt_secret = "demo-test-secret-with-at-least-32-bytes"
    settings.demo_jwt_issuer = "test-demo-issuer"
    return settings


@pytest.mark.asyncio
async def test_demo_status_requires_demo_mode_and_secret(session_and_settings):
    _, settings = session_and_settings
    response = await demo_status(settings=_demo_settings(settings))
    assert response.enabled is True

    settings.demo_jwt_secret = ""
    assert (await demo_status(settings=settings)).enabled is False

    settings.demo_jwt_secret = "demo-test-secret-with-at-least-32-bytes"
    settings.demo_mode = False
    assert (await demo_status(settings=settings)).enabled is False


@pytest.mark.asyncio
async def test_demo_login_issues_allowlisted_cardiologist_jwt(session_and_settings):
    import jwt

    session, settings = session_and_settings
    settings = _demo_settings(settings)
    response = await demo_login(
        request=_dummy_request(),
        payload=DemoLoginRequest(role="cardiologist"),
        session=session,
        settings=settings,
    )

    claims = jwt.decode(
        response.access_token,
        settings.demo_jwt_secret,
        algorithms=["HS256"],
        issuer=settings.demo_jwt_issuer,
        options={"verify_aud": False},
    )
    assert claims["demo"] is True
    assert claims["iss"] == settings.demo_jwt_issuer
    assert claims["email"] == "doctor@example.test"
    assert claims["role"] == "cardiologist"
    assert claims["exp"] > claims["iat"]
    assert response.user.email == "doctor@example.test"


@pytest.mark.asyncio
async def test_demo_login_is_disabled_when_demo_mode_is_false(session_and_settings):
    session, settings = session_and_settings
    settings = _demo_settings(settings)
    settings.demo_mode = False

    with pytest.raises(HTTPException) as exc_info:
        await demo_login(
            request=_dummy_request(),
            payload=DemoLoginRequest(role="admin"),
            session=session,
            settings=settings,
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Demo authentication is disabled."


@pytest.mark.asyncio
async def test_demo_login_requires_backend_secret(session_and_settings):
    session, settings = session_and_settings
    settings.demo_mode = True
    settings.demo_jwt_secret = ""

    with pytest.raises(HTTPException) as exc_info:
        await demo_login(
            request=_dummy_request(),
            payload=DemoLoginRequest(role="admin"),
            session=session,
            settings=settings,
        )

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == "Demo authentication is unavailable."


def test_demo_login_rejects_unknown_role_and_identity_fields():
    with pytest.raises(ValidationError):
        DemoLoginRequest(role="unknown")

    with pytest.raises(ValidationError):
        DemoLoginRequest(role="admin", email="admin@example.test")


@pytest.mark.asyncio
async def test_demo_jwt_resolves_through_current_user_and_is_rejected_when_disabled(session_and_settings):
    session, settings = session_and_settings
    settings = _demo_settings(settings)
    response = await demo_login(
        request=_dummy_request(),
        payload=DemoLoginRequest(role="cardiologist"),
        session=session,
        settings=settings,
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=response.access_token)

    user = await get_current_user(credentials=credentials, session=session, settings=settings)
    assert user.email == "doctor@example.test"

    settings.demo_mode = False
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, session=session, settings=settings)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
