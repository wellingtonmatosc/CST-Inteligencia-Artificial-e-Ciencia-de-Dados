"""Cria categorias, zonas e as cinco equipes de forma idempotente."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.repositories.supabase_repo import SupabaseRepository

CATEGORIES = [
    ("inteligencia-artificial", "Inteligência Artificial"),
    ("ciencia-de-dados", "Ciência de Dados"),
    ("logica-tecnologia", "Lógica e Tecnologia"),
    ("historia-mt", "História de Mato Grosso"),
    ("geografia-mt", "Geografia de Mato Grosso"),
    ("cultura-regional", "Cultura Regional"),
    ("literatura", "Literatura"),
    ("poesia", "Poesia"),
    ("arte", "Arte"),
    ("sustentabilidade", "Sustentabilidade e Meio Ambiente"),
    ("ifmt", "Conhecimentos sobre o IFMT"),
    ("cidadania-etica-digital", "Cidadania e Ética Digital"),
]

ZONES = [
    ("cantina", "Cantina"),
    ("terreo", "Térreo"),
    ("primeiro-andar", "1º andar"),
    ("externo-opcional", "Área externa opcional"),
]

TEAMS = [
    ("tarsila", "Equipe Tarsila", "Tarsila do Amaral", "Identidade brasileira, experimentação e Modernismo."),
    ("anita", "Equipe Anita", "Anita Malfatti", "Ruptura, vanguarda e transformação artística."),
    ("mario", "Equipe Mário", "Mário de Andrade", "Literatura, pesquisa cultural e diversidade brasileira."),
    ("oswald", "Equipe Oswald", "Oswald de Andrade", "Antropofagia cultural, inovação e irreverência."),
    ("pagu", "Equipe Pagu", "Patrícia Galvão", "Expressão cultural, participação e contestação."),
]


def upsert_named(repo: SupabaseRepository, table: str, rows: list[tuple[str, str]]) -> int:
    created = 0
    for slug, name in rows:
        existing = repo.select(table, slug=slug)
        if existing:
            repo.update(table, {"name": name, "active": True}, id=existing[0]["id"])
        else:
            repo.insert(table, {"slug": slug, "name": name, "active": True}); created += 1
    return created


def upsert_teams(repo: SupabaseRepository) -> int:
    created = 0
    for slug, name, reference_name, description in TEAMS:
        existing = repo.select("teams", slug=slug)
        data = {"name": name, "reference_name": reference_name, "description": description, "active": True}
        if existing:
            repo.update("teams", data, id=existing[0]["id"])
        else:
            repo.insert("teams", {"slug": slug, **data}); created += 1
    return created


def main() -> None:
    settings = get_settings(); configure_logging(settings.log_level)
    repo = SupabaseRepository(settings)
    try:
        categories = upsert_named(repo, "categories", CATEGORIES)
        zones = upsert_named(repo, "zones", ZONES)
        teams = upsert_teams(repo)
    finally:
        repo.close()
    logging.getLogger(__name__).info("Seed concluído: %s categorias, %s zonas e %s equipes criadas", categories, zones, teams)


if __name__ == "__main__":
    main()
