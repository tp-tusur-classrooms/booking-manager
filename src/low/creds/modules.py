from pydantic import BaseModel


class DatabaseCreds(BaseModel):
    user: str
    password: str


class TokenCreds(BaseModel):
    secret_key: str


class ModulesCreds(BaseModel):
    database: DatabaseCreds
    token: TokenCreds
