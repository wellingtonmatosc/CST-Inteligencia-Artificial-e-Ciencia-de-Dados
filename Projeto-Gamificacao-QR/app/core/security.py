"""Primitivas de segurança para participantes e administração."""
from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_ph = PasswordHasher()


def random_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def random_access_code(length: int = 8) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash:
        return False
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def sign_admin_session(
    secret: str,
    username: str = "admin",
    role: str = "admin",
    source: str = "environment",
) -> str:
    return URLSafeTimedSerializer(secret, salt="admin-session").dumps(
        {"username": username, "role": role, "source": source}
    )


def read_admin_session(secret: str, token: str, max_age_seconds: int) -> dict | None:
    if not token:
        return None
    try:
        data = URLSafeTimedSerializer(secret, salt="admin-session").loads(
            token, max_age=max_age_seconds
        )
    except (BadSignature, SignatureExpired):
        return None
    role = data.get("role")
    username = data.get("username")
    if role not in {"admin", "operator", "validator", "viewer"} or not username:
        return None
    return {
        "username": str(username),
        "role": str(role),
        "source": str(data.get("source") or "session"),
    }


def verify_admin_session(secret: str, token: str, max_age_seconds: int) -> bool:
    """Compatibilidade com os testes antigos; a aplicação usa read_admin_session."""
    return read_admin_session(secret, token, max_age_seconds) is not None
