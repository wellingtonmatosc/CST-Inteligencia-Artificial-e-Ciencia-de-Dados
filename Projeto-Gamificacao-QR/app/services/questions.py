"""Validação de respostas e requisitos de acessibilidade das questões."""
from __future__ import annotations

import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value.strip().lower())
        .encode("ascii", "ignore")
        .decode("ascii")
        .split()
    )


def evaluate_answer(question: dict[str, Any], answer: Any) -> bool:
    kind = question["kind"]
    correct = question.get("correct_answer") or {}
    expected = correct.get("value")

    if kind in {"multiple_choice", "true_false"}:
        return answer == expected
    if kind == "short_text":
        accepted = correct.get("accepted", [expected] if expected is not None else [])
        return normalize_text(str(answer)) in {normalize_text(str(v)) for v in accepted}
    if kind in {"association", "ordering"}:
        return answer == expected
    return False


def validate_accessibility_metadata(question: dict[str, Any]) -> list[str]:
    """Valida requisitos mínimos antes de uma questão ser ativada."""
    issues: list[str] = []
    a11y = question.get("accessibility") or {}
    if not a11y.get("instructions_clear", False):
        issues.append("Instruções precisam ser claras e objetivas.")
    if question.get("media_type") == "image" and not a11y.get("alt_text"):
        issues.append("Imagem precisa de texto alternativo equivalente.")
    if question.get("media_type") in {"audio", "video"} and not a11y.get("transcript"):
        issues.append("Áudio/vídeo precisa de transcrição ou legenda equivalente.")
    if a11y.get("depends_on_color_only", False):
        issues.append("A questão não pode depender apenas de cor.")
    if a11y.get("requires_speed", False):
        issues.append("A questão não pode exigir rapidez para pontuar.")
    return issues
