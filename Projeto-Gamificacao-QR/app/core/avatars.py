"""Catálogo de avatares internos permitidos.

O banco armazena apenas a chave. Nenhuma URL, upload ou dado biométrico é aceito.
"""

DEFAULT_AVATAR_KEY = "avatar-01"
AVATAR_KEYS = tuple(f"avatar-{index:02d}" for index in range(1, 21))
AVATAR_KEY_SET = frozenset(AVATAR_KEYS)


def validate_avatar_key(value: str | None, *, use_default: bool = True) -> str:
    key = (value or "").strip()
    if not key and use_default:
        return DEFAULT_AVATAR_KEY
    if key not in AVATAR_KEY_SET:
        raise ValueError("Avatar inválido.")
    return key
