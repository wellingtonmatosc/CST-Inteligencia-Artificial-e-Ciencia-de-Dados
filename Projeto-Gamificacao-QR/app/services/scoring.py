"""Regras puras de pontuação para facilitar testes e auditoria."""
from __future__ import annotations


def score_for_attempt(base_points: int, attempt_number: int) -> int:
    if attempt_number <= 0:
        raise ValueError("attempt_number deve ser >= 1")
    if attempt_number == 1:
        return base_points
    if attempt_number == 2:
        return round(base_points * 0.70)
    if attempt_number == 3:
        return round(base_points * 0.50)
    return 0


MILESTONES = {3: 5, 5: 10}


def milestone_points(completed_normal_activities: int) -> list[tuple[int, int]]:
    """Retorna marcos que já deveriam ter sido alcançados."""
    return [(threshold, points) for threshold, points in MILESTONES.items() if completed_normal_activities >= threshold]
