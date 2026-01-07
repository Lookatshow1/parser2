from fastapi import APIRouter, Depends

from app.api.schemas import AuthMeResponse
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/me", tags=["auth"])


@router.get("", response_model=AuthMeResponse)
def get_me(user: User = Depends(get_current_user)):
    return user
