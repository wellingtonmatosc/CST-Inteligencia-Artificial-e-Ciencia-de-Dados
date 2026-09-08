"""Cria ou atualiza usuário administrativo no banco.

A senha é lidaida com getpass e somente o hash Argon2 é persistido.
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.security import hash_password
from app.repositories.supabase_repo import SupabaseRepository

ROLES = {"admin", "operator", "validator", "viewer"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cria/atualiza usuário administrativo do Trilhas Poéticas")
    p.add_argument("username")
    p.add_argument("--role", default="admin", choices=sorted(ROLES))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    password = getpass.getpass("Senha (mínimo 10 caracteres): ")
    confirm = getpass.getpass("Confirme a senha: ")
    if password != confirm:
        raise SystemExit("As senhas não conferem.")
    if len(password) < 10:
        raise SystemExit("A senha precisa ter pelo menos 10 caracteres.")

    repo = SupabaseRepository(get_settings())
    try:
        rows = repo.raw_table("admin_users").select("id").ilike("username", args.username.strip()).limit(1).execute().data or []
        payload = {"username": args.username.strip(), "password_hash": hash_password(password), "role": args.role, "active": True}
        if rows:
            repo.update("admin_users", payload, id=rows[0]["id"])
            print("Usuário administrativo atualizado.")
        else:
            repo.insert("admin_users", payload)
            print("Usuário administrativo criado.")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
