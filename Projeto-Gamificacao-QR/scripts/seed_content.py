"""Cria categorias e zonas básicas do projeto de forma idempotente."""
from __future__ import annotations

import logging
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


def upsert_by_slug(repo: SupabaseRepository, table: str, rows: list[tuple[str, str]]) -> int:
    created = 0
    for slug, name in rows:
        existing = repo.select(table, slug=slug)
        if existing:
            repo.update(table, {"name": name, "active": True}, id=existing[0]["id"])
            continue
        repo.insert(table, {"slug": slug, "name": name, "active": True})
        created += 1
    return created


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    repo = SupabaseRepository(settings)
    categories = upsert_by_slug(repo, "categories", CATEGORIES)
    zones = upsert_by_slug(repo, "zones", ZONES)
    logging.getLogger(__name__).info("Seed concluído: %s categorias e %s zonas criadas", categories, zones)


if __name__ == "__main__":
    main()
