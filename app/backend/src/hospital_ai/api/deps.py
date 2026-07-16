import logging
from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import User
from hospital_ai.db.session import get_session
from hospital_ai.services.jwt_auth import JwtAuthService

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def get_request_ip(request: Request) -> str:
    # Uvicorn handles proxy headers securely if --proxy-headers is enabled.
    # Manually parsing X-Forwarded-For here allows IP spoofing.
    if request.client:
        return request.client.host
    return "unknown"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    # P1-3: Try JWT validation first when configured.
    # Falls back to static token map if JWT is not configured or fails.
    jwt_service = JwtAuthService(settings)
    jwt_data = await jwt_service.validate_token(credentials.credentials)
    if jwt_data is not None:
        result = await session.execute(select(User).where(User.email == jwt_data.email, User.is_active.is_(True)))
        user = result.scalar_one_or_none()
        if user is not None:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User validated via JWT but no active local account found."
        )

    # Static token fallback (local dev and legacy clients)
    email = settings.token_user_map.get(credentials.credentials)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown bearer token.")

    result = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active or seeded.")
    return user


async def session_dependency() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def require_role(roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker
