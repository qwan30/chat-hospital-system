from fastapi import APIRouter, Depends

from hospital_ai.api.deps import get_current_user
from hospital_ai.db.models import User
from hospital_ai.schemas.auth import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
