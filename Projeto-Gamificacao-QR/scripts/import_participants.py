"""Importa a base institucional para Trilhas Poéticas.

O arquivo de saída contém os códigos de ativação em texto puro e NÃO deve ser
commitado. No banco ficam somente hashes SHA-256 desses códigos.

CSV esperado:
full_name,participant_type,registration,course_class,institution,is_organizer

participant_type: student | staff | external
is_organizer: true/false, 1/0, sim/nao
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import random_access_code, sha256_hex
from app.repositories.supabase_repo import SupabaseRepository

REQUIRED = {"full_name", "participant_type"}
TRUTHY = {"1", "true", "sim", "s", "yes", "y"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Importa participantes institucionais do Trilhas Poéticas")
    p.add_argument("--input", type=Path, required=True, help="CSV institucional")
    p.add_argument("--output", type=Path, default=Path("participantes_ativacao.csv"), help="CSV local com códigos de ativação")
    p.add_argument("--yes", action="store_true", help="Não pedir confirmação")
    return p.parse_args()


def pending_nick(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pre-{digest}"


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Arquivo não encontrado: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise SystemExit(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {k: (v or "").strip() for k, v in raw.items()}
            if not row["full_name"]:
                raise SystemExit(f"Linha {i}: full_name vazio")
            if row["participant_type"] not in {"student", "staff", "external"}:
                raise SystemExit(f"Linha {i}: participant_type inválido")
            if row["participant_type"] == "student" and (not row.get("registration") or not row.get("course_class")):
                raise SystemExit(f"Linha {i}: aluno exige registration e course_class")
            if row["participant_type"] == "staff" and not row.get("registration"):
                raise SystemExit(f"Linha {i}: servidor deve possuir registration para evitar duplicidade")
            row["is_organizer"] = "true" if row.get("is_organizer", "").lower() in TRUTHY else "false"
            rows.append(row)
    return rows


def main() -> None:
    args = parse_args()
    configure_logging(get_settings().log_level)
    log = logging.getLogger(__name__)
    rows = read_rows(args.input)
    print(f"Registros válidos: {len(rows)}")
    print(f"Organizadores: {sum(r['is_organizer']=='true' for r in rows)}")
    if not args.yes:
        if input("Digite SIM para importar: ").strip().upper() != "SIM":
            raise SystemExit("Cancelado.")

    repo = SupabaseRepository(get_settings())
    output: list[dict[str, str]] = []
    created = skipped = 0
    try:
        for idx, row in enumerate(rows, start=1):
            registration = row.get("registration") or None
            existing = repo.select("participants", registration=registration) if registration else []
            if existing:
                skipped += 1
                output.append({
                    "full_name": row["full_name"], "registration": registration or "",
                    "activation_code": "", "team_id": existing[0].get("team_id") or "", "status": "existing"
                })
                continue

            activation_code = random_access_code()
            seed = registration or f"{row['full_name']}|{idx}"
            participant = repo.insert("participants", {
                "full_name": row["full_name"],
                "nick": pending_nick(seed),
                "participant_type": row["participant_type"],
                "registration": registration,
                "course_class": row.get("course_class") or None,
                "institution": row.get("institution") or None,
                "access_code_hash": sha256_hex(activation_code),
                "password_hash": None,
                "is_organizer": row["is_organizer"] == "true",
                "active": True,
            })
            team_id = None
            if not participant.get("is_organizer"):
                team_id = repo.rpc("trilhas_assign_team", {"p_participant_id": participant["id"]})
            output.append({
                "full_name": row["full_name"], "registration": registration or "",
                "activation_code": activation_code, "team_id": team_id or "", "status": "created"
            })
            created += 1
    finally:
        repo.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["full_name", "registration", "activation_code", "team_id", "status"])
        writer.writeheader(); writer.writerows(output)
    log.info("Importação concluída: %s criados, %s existentes", created, skipped)
    print(f"Saída local: {args.output.resolve()}")
    print("IMPORTANTE: o CSV de saída contém códigos de ativação. Não envie para o GitHub.")


if __name__ == "__main__":
    main()
