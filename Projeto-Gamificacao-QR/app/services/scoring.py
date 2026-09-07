"""Regras puras de pontuação para facilitar testes e auditoria."""
from __future__ import annotations


def score_for_attempt(base_points: int, attempt_number: int) -> int:
    """Regra genérica mantida para bônus e fluxos legados."""
    if attempt_number <= 0:
        raise ValueError("attempt_number deve ser >= 1")
    if attempt_number == 1:
        return base_points
    if attempt_number == 2:
        return round(base_points * 0.70)
    if attempt_number == 3:
        return round(base_points * 0.50)
    return 0


def normal_max_attempts(question_kind: str) -> int:
    """V/F tem uma tentativa; os demais tipos normais têm no máximo duas."""
    return 1 if question_kind == "true_false" else 2


def normal_score_for_attempt(attempt_number: int) -> int:
    """Pontuação por acerto em atividade normal: 10 na 1ª e 6 na 2ª."""
    if attempt_number <= 0:
        raise ValueError("attempt_number deve ser >= 1")
    if attempt_number == 1:
        return 10
    if attempt_number == 2:
        return 6
    return 0


def normal_participation_points() -> int:
    """Pontuação concedida quando todas as tentativas normais terminam sem acerto."""
    return 2


MILESTONES = {3: 5, 5: 10}


def milestone_points(completed_normal_activities: int) -> list[tuple[int, int]]:
    """Retorna marcos que já deveriam ter sido alcançados."""
    return [(threshold, points) for threshold, points in MILESTONES.items() if completed_normal_activities >= threshold]
