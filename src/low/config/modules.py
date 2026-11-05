from pathlib import Path

from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    server: str
    port: int
    db_name: str
    pool_size: int


class TokenConfig(BaseModel):
    access_token_expire_min: int
    refresh_token_expire_days: int
    algorithm: str


class MailerConfig(BaseModel):
    smtp_server: str
    sender_email: str
    templates_path: Path
    mock_sending: bool


class FilesConfig(BaseModel):
    public_path: Path
    public_url: str


class VerificationTokenConfig(BaseModel):
    code_length: int
    expiry_minutes: int
    max_attempts: int


class ModulesConfig(BaseModel):
    database: DatabaseConfig
    token: TokenConfig
    verification_token: VerificationTokenConfig
    mailer: MailerConfig
    files: FilesConfig
