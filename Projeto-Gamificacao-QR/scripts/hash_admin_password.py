"""Gera um hash Argon2 para ADMIN_PASSWORD_HASH sem gravar a senha em disco."""
from __future__ import annotations

from getpass import getpass
from app.core.security import hash_password


def main() -> None:
    password = getpass("Senha administrativa: ")
    confirmation = getpass("Repita a senha: ")
    if password != confirmation:
        raise SystemExit("As senhas não coincidem.")
    if len(password) < 10:
        raise SystemExit("Use uma senha com pelo menos 10 caracteres.")
    print(hash_password(password))


if __name__ == "__main__":
    main()
