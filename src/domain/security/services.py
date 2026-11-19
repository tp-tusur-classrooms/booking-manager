from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Self
from uuid import UUID, uuid4

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from src.low.exceptions import UnauthorizatedException


class HasherService:
    def validate_password(
        self: Self, plain_password: str, hashed_password: str
    ) -> bool:
        try:
            return bcrypt.checkpw(
                bytes(plain_password, encoding="utf-8"),
                bytes(hashed_password, encoding="utf-8"),
            )
        except ValueError:
            # bcrypt отклоняет пароли длиннее 72 байт и некорректные хеши.
            return False

    def get_password_hash(self: Self, password: str) -> str:
        return bcrypt.hashpw(
            bytes(password, encoding="utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")


class TokenService:
    _ACCESS_TOKEN_TYPE = "access"
    _REFRESH_TOKEN_TYPE = "refresh"

    def __init__(
        self: Self,
        secret_key: str,
        algorithm: str,
        access_token_expire_minutes: int,
        refresh_token_expire_days: int,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self: Self,
        data: Mapping[str, object],
        expires_delta: timedelta | None = None,
    ) -> str:
        to_encode = dict(data)
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        )
        to_encode.update(
            {"exp": expire, "type": self._ACCESS_TOKEN_TYPE, "jti": str(uuid4())}
        )
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self: Self,
        data: Mapping[str, object],
        expires_delta: timedelta | None = None,
    ) -> str:
        to_encode = dict(data)
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(days=self.refresh_token_expire_days)
        )
        to_encode.update(
            {"exp": expire, "type": self._REFRESH_TOKEN_TYPE, "jti": str(uuid4())}
        )
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self: Self, token: str) -> dict[str, object]:
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require_exp": True, "require_sub": True, "require_jti": True},
            )
        except ExpiredSignatureError as exc:
            raise UnauthorizatedException("Сессия истекла", "token_expired") from exc
        except JWTError as exc:
            raise UnauthorizatedException from exc

    def get_user_id_from_token(self: Self, token: str) -> UUID:
        payload = self.decode_token(token)
        if payload.get("type") != self._ACCESS_TOKEN_TYPE:
            raise UnauthorizatedException
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizatedException
        try:
            return UUID(str(user_id))
        except ValueError:
            raise UnauthorizatedException from ValueError

    def get_user_id_from_refresh_token(self: Self, token: str) -> UUID:
        payload = self.decode_token(token)
        if payload.get("type") != self._REFRESH_TOKEN_TYPE:
            raise UnauthorizatedException
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizatedException
        try:
            return UUID(str(user_id))
        except ValueError:
            raise UnauthorizatedException from ValueError
