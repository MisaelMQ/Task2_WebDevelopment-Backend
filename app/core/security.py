from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Any

import jwt
from pwdlib import PasswordHash
from app.core.config import get_settings

password_hash = PasswordHash.recommended()

def hash_password(
    plain_password: str,
) -> str:
    return password_hash.hash(
        plain_password
    )

def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(
    *,
    user_id: int,
    username: str,
    role: str,
) -> tuple[str, int]:
    settings = get_settings()

    current_time = datetime.now(timezone.utc)

    expires_in = (
        settings.access_token_expire_minutes * 60
    )

    expiration_time = current_time + timedelta(
        seconds=expires_in
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": current_time,
        "exp": expiration_time,
    }

    encoded_token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return encoded_token, expires_in

def decode_access_token(
    token: str,
) -> dict[str, Any]:
    settings = get_settings()

    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )