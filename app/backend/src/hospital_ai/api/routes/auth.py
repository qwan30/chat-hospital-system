from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.api.limiter import limiter
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import User
from hospital_ai.schemas.auth import DemoLoginRequest, DemoStatusResponse, TokenResponse, UserRead

router = APIRouter()

DEMO_ROLE_EMAILS = {
    "cardiologist": "doctor@example.test",
    "hospitalist": "doctor@example.test",
    "rn": "nurse@example.test",
    "pharmacist": "pharmacist@example.test",
    "front_desk": "records@example.test",
    "admin": "admin@example.test",
    "security": "security@example.test",
}


def _demo_auth_enabled(settings: Settings) -> bool:
    return settings.demo_mode and bool(settings.demo_jwt_secret.strip())


@router.get("/demo/status", response_model=DemoStatusResponse)
async def demo_status(settings: Settings = Depends(get_settings)) -> DemoStatusResponse:
    return DemoStatusResponse(enabled=_demo_auth_enabled(settings))


@router.post("/demo", response_model=TokenResponse)
@limiter.limit("10/minute")
async def demo_login(
    request: Request,
    payload: DemoLoginRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    if not settings.demo_mode:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo authentication is disabled.")
    if not settings.demo_jwt_secret.strip() or not settings.demo_jwt_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Demo authentication is unavailable."
        )

    email = DEMO_ROLE_EMAILS[payload.role]
    result = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Demo authentication is unavailable."
        )

    issued_at = datetime.now(UTC)
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "role": payload.role,
        "demo": True,
        "iss": settings.demo_jwt_issuer,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.demo_token_ttl_minutes),
    }
    access_token = jwt.encode(claims, settings.demo_jwt_secret, algorithm="HS256")
    return TokenResponse(access_token=access_token, token_type="bearer", user=user)


# Brute-force protection: this endpoint authenticates credentials, so it needs a
# tighter limit than the global default. slowapi requires `request` to derive the
# client key, and FastAPI injects it automatically.
@router.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    if form_data.password != "demo":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    email = form_data.username.lower()
    result = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active or seeded.")

    # In a real app, verify password hash here.
    # We fallback to static dev tokens for the portfolio.
    access_token = next((t for t, e in settings.token_user_map.items() if e == user.email), None)
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token configured for this user")

    return TokenResponse(access_token=access_token, token_type="bearer", user=user)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
