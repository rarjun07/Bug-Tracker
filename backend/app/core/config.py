from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bug Tracker API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://bugtracker:bugtracker@localhost:5432/bugtracker"
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)
    frontend_origin: str = "http://localhost:5173"

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Railway's standard PostgreSQL URL needs an explicit installed driver."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
