"""Moderação simples e explicável de nomes públicos/nicks."""
from __future__ import annotations

import re
import unicodedata

# Termos proibidos são configuráveis via painel administrativo e BLOCKED_NICK_TERMS.
# A lista padrão fica vazia para evitar regras culturais fixas no código.
DEFAULT_BLOCKED_TERMS: set[str] = set()

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def normalize_for_moderation(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().translate(_LEET)
    return re.sub(r"[^a-z0-9]+", "", value)


class NickModerationService:
    def __init__(self, extra_terms: str = ""):
        terms = set(DEFAULT_BLOCKED_TERMS)
        terms.update(t.strip().lower() for t in extra_terms.split(",") if t.strip())
        self.terms = {normalize_for_moderation(t) for t in terms if t}

    def validate(self, nick: str) -> tuple[bool, str | None]:
        clean = nick.strip()
        if not 3 <= len(clean) <= 24:
            return False, "O nick deve ter entre 3 e 24 caracteres."
        if not re.fullmatch(r"[\w .@-]+", clean, flags=re.UNICODE):
            return False, "Use apenas letras, números, espaço, ponto, hífen, _ ou @."
        normalized = normalize_for_moderation(clean)
        if any(term and term in normalized for term in self.terms):
            return False, "Esse nome de usuário não pode ser utilizado. Escolha outro."
        return True, None
