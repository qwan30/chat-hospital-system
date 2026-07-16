"""Authentication API routes.
Các endpoint API xử lý đăng nhập, cấp phát token và lấy thông tin tài khoản hiện tại.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import User
from hospital_ai.schemas.auth import TokenResponse, UserRead

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate user with username and password, returning a bearer access token.
    Xác thực người dùng bằng tài khoản/mật khẩu và trả về bearer access token.
    """
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
    """Return the profile details of the currently authenticated user.
    Trả về thông tin chi tiết của tài khoản người dùng đang đăng nhập hiện tại.
    """
    return current_user
