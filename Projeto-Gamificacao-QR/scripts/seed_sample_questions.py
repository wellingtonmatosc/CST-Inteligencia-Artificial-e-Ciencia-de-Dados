"""Insere questões demonstrativas acessíveis para validar o MVP.

O conteúdo deve passar por revisão pedagógica antes do evento. O script é idempotente
por texto da pergunta e não vincula questões a QR normal automaticamente.
"""
from __future__ import annotations

import logging
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.repositories.supabase_repo import SupabaseRepository

A11Y = {"instructions_clear": True, "depends_on_color_only": False, "requires_speed": False}

QUESTIONS = [
    ("inteligencia-artificial", "multiple_choice", "Qual alternativa descreve melhor aprendizado de máquina?", ["Modelos aprendem padrões a partir de dados", "Todo programa usa robôs físicos", "É apenas armazenamento de arquivos", "É sinônimo de internet"], "Modelos aprendem padrões a partir de dados"),
    ("ciencia-de-dados", "multiple_choice", "Em uma análise de dados, qual ação normalmente vem antes de interpretar os resultados?", ["Verificar e preparar os dados", "Apagar os dados originais", "Escolher o resultado desejado", "Publicar sem conferir"], "Verificar e preparar os dados"),
    ("logica-tecnologia", "true_false", "Um algoritmo pode ser entendido como uma sequência organizada de passos para resolver um problema.", ["Verdadeiro", "Falso"], "Verdadeiro"),
    ("historia-mt", "multiple_choice", "Cuiabá foi fundada no início de qual século?", ["Século XVI", "Século XVII", "Século XVIII", "Século XX"], "Século XVIII"),
    ("geografia-mt", "multiple_choice", "Qual conjunto reúne os três grandes biomas presentes em Mato Grosso?", ["Amazônia, Cerrado e Pantanal", "Caatinga, Pampa e Pantanal", "Mata Atlântica, Pampa e Caatinga", "Amazônia, Pampa e Mata Atlântica"], "Amazônia, Cerrado e Pantanal"),
    ("cultura-regional", "true_false", "Siriri e cururu fazem parte de manifestações culturais tradicionais de Mato Grosso.", ["Verdadeiro", "Falso"], "Verdadeiro"),
    ("literatura", "multiple_choice", "Qual elemento apresenta quem participa dos acontecimentos de uma narrativa?", ["Personagens", "Margens", "Índice remissivo", "Bibliografia"], "Personagens"),
    ("poesia", "true_false", "Em poesia, verso é cada linha que compõe um poema.", ["Verdadeiro", "Falso"], "Verdadeiro"),
    ("arte", "multiple_choice", "Qual prática favorece uma experiência artística mais acessível?", ["Oferecer descrição textual de elementos visuais relevantes", "Usar somente cores para comunicar informação", "Retirar legendas dos vídeos", "Impedir ampliação do texto"], "Oferecer descrição textual de elementos visuais relevantes"),
    ("sustentabilidade", "multiple_choice", "Qual sequência representa os chamados 3 Rs do consumo consciente?", ["Reduzir, reutilizar e reciclar", "Recolher, remover e rejeitar", "Repetir, registrar e revisar", "Reservar, reparar e rotular"], "Reduzir, reutilizar e reciclar"),
    ("ifmt", "multiple_choice", "Na sigla IFMT, o que significa MT?", ["Mato Grosso", "Mato Grosso do Sul", "Minas Técnicas", "Método Tecnológico"], "Mato Grosso"),
    ("cidadania-etica-digital", "multiple_choice", "Qual prática aumenta a segurança de uma conta digital?", ["Usar senha exclusiva e autenticação em dois fatores", "Compartilhar a senha com colegas", "Repetir a mesma senha em todos os serviços", "Desativar atualizações de segurança"], "Usar senha exclusiva e autenticação em dois fatores")
]


def options(values: list[str]) -> list[dict[str, str]]:
    return [{"value": value, "label": value} for value in values]


def main() -> None:
    settings = get_settings(); configure_logging(settings.log_level)
    repo = SupabaseRepository(settings); logger = logging.getLogger(__name__)
    categories = {row["slug"]: row["id"] for row in repo.raw_table("categories").select("id,slug").execute().data or []}
    created = 0
    for slug, kind, prompt, raw_options, correct in QUESTIONS:
        category_id = categories.get(slug)
        if not category_id:
            raise SystemExit(f"Categoria ausente: {slug}. Execute seed_content.py primeiro.")
        if repo.select("questions", prompt=prompt):
            continue
        repo.insert("questions", {"category_id": category_id, "kind": kind, "prompt": prompt, "options": options(raw_options), "correct_answer": {"value": correct}, "difficulty": 1, "accessibility": A11Y, "active": True})
        created += 1
    logger.info("Questões demonstrativas criadas: %s", created)


if __name__ == "__main__":
    main()
