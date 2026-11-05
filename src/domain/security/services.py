from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Any, Self
from uuid import UUID, uuid4

import aiosmtplib
import bcrypt
from jose import JWTError, jwt

from src.low.config.modules import MailerConfig
from src.low.exceptions import ServerException, UnauthorizatedException
from src.low.logging import logger


class EmailSenderService:
    def __init__(self: Self, mailer_config: MailerConfig, email_password: str) -> None:
        self.logger = logger.register_logger("mailer")
        self.email_address = mailer_config.sender_email
        self.email_password = email_password
        self.templates_path = mailer_config.templates_path
        self.mock_sending = mailer_config.mock_sending

        raw = mailer_config.smtp_server
        host, _, port_str = raw.rpartition(":")
        if not host or not port_str.isdigit():
            raise ServerException(
                f"Invalid smtp_server format '{raw}', expected 'host:port'"
            )
        self._smtp_host = host
        self._smtp_port = int(port_str)

    def _load_template(self: Self, name: str) -> Template:
        template_file = self.templates_path / name
        try:
            return Template(template_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.logger.warning(f"Email template '{name}' not found, using fallback")
            return Template("Код: $code")

    async def _send(self: Self, recipient: str, subject: str, body: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.email_address
        message["To"] = recipient
        message.attach(MIMEText(body, "html", "utf-8"))

        send_args: dict[str, Any] = {
            "hostname": self._smtp_host,
            "port": self._smtp_port,
            "username": self.email_address,
            "password": self.email_password,
            "use_tls": True,
        }

        if self.mock_sending:
            self.logger.info("Mocking sending")
            self.logger.debug(
                f"Mock request to aiosmtplib, body: {body}, args: {send_args}"
            )
        else:
            await aiosmtplib.send(message, **send_args)

    async def send_password_reset_code(
        self: Self, recipient_email: str, reset_code: str
    ) -> None:
        body = self._load_template("password_reset.html").safe_substitute(
            code=reset_code, email=recipient_email
        )
        await self._send(recipient_email, "Сброс пароля", body)

    async def send_email_verification_code(
        self: Self, recipient_email: str, verification_code: str
    ) -> None:
        body = self._load_template("email_verification.html").safe_substitute(
            code=verification_code, email=recipient_email
        )
        await self._send(recipient_email, "Подтверждение email", body)

    async def send_email_change_code(
        self: Self, recipient_email: str, change_code: str
    ) -> None:
        body = self._load_template("email_change.html").safe_substitute(
            code=change_code, email=recipient_email
        )
        await self._send(recipient_email, "Смена email", body)


class HasherService:
    def validate_password(
        self: Self, plain_password: str, hashed_password: str
    ) -> bool:
        return bcrypt.checkpw(
            bytes(plain_password, encoding="utf-8"),
            bytes(hashed_password, encoding="utf-8"),
        )

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
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise UnauthorizatedException from ValueError

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
