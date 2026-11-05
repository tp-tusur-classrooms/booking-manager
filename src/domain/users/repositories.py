from src.domain.base.base_repository import BaseRepository
from src.domain.common import models
import src.domain.users.schemas as user_schemas


class UserRepository(
    BaseRepository[
        models.User,
        user_schemas.CreateUser,
        user_schemas.UpdateUser,
        user_schemas.FilterUser,
        user_schemas.UserWith,
    ]
): ...
