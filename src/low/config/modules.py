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


class FilesConfig(BaseModel):
    public_path: Path
    public_url: str


class ModulesConfig(BaseModel):
    database: DatabaseConfig
    token: TokenConfig
    files: FilesConfig
