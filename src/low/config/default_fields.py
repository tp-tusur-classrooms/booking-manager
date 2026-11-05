from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel


class GeneralConfig(BaseModel):
    creds: Path


class FrontendConfig(BaseModel):
    origin: list[AnyHttpUrl]


class NetworkingConfig(BaseModel):
    server_host: str
    server_port: int
    swagger_port: int

    frontend: FrontendConfig


class LoggingConfig(BaseModel):
    console_level: str
    file_level: str
    log_path: Path
    max_log_size_mb: int


class AppSettings(BaseModel):
    # move to general
    """Application-level settings loaded from config JSON.

    IMPORTANT: These fields are intentionally required (no defaults) so that
    configuration is provided by the application's config files instead of
    hard-coded defaults in the codebase.
    """

    API_V1_STR: str
    PROJECT_NAME: str
    VERSION: str
    ENVIRONMENT: str
