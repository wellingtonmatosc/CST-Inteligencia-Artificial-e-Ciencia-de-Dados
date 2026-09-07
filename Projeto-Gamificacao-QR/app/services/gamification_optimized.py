"""Atalhos de alto desempenho para as operações mais frequentes do jogo.

As regras continuam equivalentes ao serviço principal, mas as operações normais
são executadas por funções PostgreSQL (RPC), reduzindo várias idas ao Supabase
para uma única chamada por ação.
"""
from __future__ import annotations

from app.core.errors import AppError
from app.services.gamification import GamificationService


class OptimizedGamificationService(GamificationService):
    def get_qr(self, participant_id: str, code: str) -> dict:
        result = self.repo.rpc(
            "game_get_normal_activity",
            {
                "p_participant_id": participant_id,
                "p_code": code,
                "p_activity_date": self._today(),
            },
        )

        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)

        if result.get("fallback"):
            return super().get_qr(participant_id, code)

        if not result.get("ok"):
            error = result.get("error")
            if error == "invalid_qr":
                raise AppError("QR Code inválido ou inativo.", 404)
            if error == "participant_not_found":
                raise AppError("Participante não encontrado.", 401)
            if error == "no_unseen_question":
                raise AppError("Você já respondeu todas as questões inéditas disponíveis neste ponto.", 409)
            raise AppError("Não foi possível carregar esta atividade.", 409)

        result.pop("ok", None)
        return result

    def answer_normal(self, participant_id: str, run_id: str, answer) -> dict:
        result = self.repo.rpc(
            "game_answer_normal",
            {
                "p_participant_id": participant_id,
                "p_run_id": run_id,
                "p_answer": answer,
                "p_activity_date": self._today(),
            },
        )

        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)

        if not result.get("ok"):
            error = result.get("error")
            if error == "activity_not_found":
                raise AppError("Atividade não encontrada.", 404)
            if error == "already_finalized":
                raise AppError("Esta atividade já foi finalizada.", 409)
            raise AppError("Não foi possível registrar a resposta.", 409)

        result.pop("ok", None)
        return result

    def ranking(self, limit: int = 100) -> list[dict]:
        result = self.repo.rpc("game_ranking", {"p_limit": limit})
        return result if isinstance(result, list) else []
