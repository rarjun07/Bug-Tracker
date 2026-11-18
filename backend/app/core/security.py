from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
_dummy_password_hash = password_hash.hash("dummy-password-for-timing-equalization")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def verify_unknown_user_password(plain_password: str) -> None:
    """Spend comparable time verifying a password when the account does not exist."""
    password_hash.verify(plain_password, _dummy_password_hash)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    secret_key = settings.jwt_secret_key.get_secret_value()
    if len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be set to at least 32 characters")

    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        secret_key,
        algorithm="HS256",
    )
