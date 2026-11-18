from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bug Tracker API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://bugtracker:bugtracker@localhost:5432/bugtracker"
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
