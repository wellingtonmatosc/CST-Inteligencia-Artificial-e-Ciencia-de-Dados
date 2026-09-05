"""Primitivas de segurança para sessões e administração."""
from __future__ import annotations

import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
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
    except (VerifyMismatchError, VerificationError):
        return False


def sign_admin_session(secret: str) -> str:
    return URLSafeTimedSerializer(secret, salt="admin-session").dumps({"role": "admin"})


def verify_admin_session(secret: str, token: str, max_age_seconds: int) -> bool:
    if not token:
        return False
    try:
        data = URLSafeTimedSerializer(secret, salt="admin-session").loads(token, max_age=max_age_seconds)
        return data.get("role") == "admin"
    except (BadSignature, SignatureExpired):
        return False
