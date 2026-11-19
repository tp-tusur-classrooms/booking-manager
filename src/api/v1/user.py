from fastapi import APIRouter, Security

from src.api.v1.common import get_current_user
import src.domain.users.schemas as user_schemas
from src.low.exceptions import APIException

router = APIRouter()


@router.get(
    path="/profile",
    response_model=user_schemas.User,
    responses={401: {"model": APIException}},
    tags=["Users"],
)
async def get_profile(
    current_user: user_schemas.User = Security(get_current_user),
) -> user_schemas.User:
    """
    Получение профиля пользователя
    """
    return current_user
