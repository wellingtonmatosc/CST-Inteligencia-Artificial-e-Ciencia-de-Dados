"""Regras da experiência Trilhas Poéticas.

As operações críticas ficam no PostgreSQL e são expostas por RPCs atômicas.
A leitura de uma estação também usa um único RPC para evitar várias viagens
sequenciais entre a Vercel e o Supabase.
"""
from __future__ import annotations

from app.core.errors import AppError
from app.repositories.supabase_repo import SupabaseRepository

STATION_LABELS = {
    "permanent": "Permanente",
    "sequential": "Sequencial",
    "temporary": "Temporário",
    "special": "Especial",
}


class TrilhasService:
    def __init__(self, repo: SupabaseRepository, timezone_name: str = "America/Cuiaba"):
        self.repo = repo
        self.timezone_name = timezone_name

    def get_station(self, participant_id: str, code: str) -> dict:
        result = self.repo.rpc(
            "trilhas_get_station",
            {"p_participant_id": participant_id, "p_code": code.strip()},
        )
        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)
        if not result.get("ok"):
            if result.get("error") == "invalid_qr":
                raise AppError("QR Code inválido ou inativo.", 404)
            raise AppError("Não foi possível carregar esta estação.", 503)

        result.pop("ok", None)
        qr = result.get("qr") or {}
        qr["station_type_label"] = STATION_LABELS.get(
            qr.get("station_type"), "Estação"
        )
        result["qr"] = qr
        return result

    def validate_station(self, participant_id: str, code: str, physical_code: str | None) -> dict:
        result = self.repo.rpc(
            "trilhas_validate_station",
            {
                "p_participant_id": participant_id,
                "p_code": code,
                "p_physical_code": physical_code,
            },
        )
        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)
        if result.get("ok"):
            return result
        mapping = {
            "participant_not_found": ("Participante não encontrado.", 401),
            "invalid_qr": ("QR Code inválido ou inativo.", 404),
            "invalid_physical_code": (
                "Código da estação incorreto. Confira o código exibido junto ao QR.",
                422,
            ),
            "sequence_locked": (
                "Esta etapa está bloqueada. Finalize primeiro as etapas anteriores da trilha.",
                409,
            ),
            "sequence_not_configured": (
                "Esta sequência ainda não foi configurada pela organização.",
                503,
            ),
            "not_started": ("Esta estação ainda não está disponível.", 409),
            "expired": ("O período desta estação terminou.", 409),
        }
        message, status = mapping.get(
            result.get("error"),
            ("Não foi possível validar esta estação.", 409),
        )
        raise AppError(message, status)

    def answer_challenge(self, participant_id: str, code: str, answer) -> dict:
        result = self.repo.rpc(
            "trilhas_answer_challenge",
            {
                "p_participant_id": participant_id,
                "p_code": code,
                "p_answer": answer,
            },
        )
        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)
        if result.get("ok"):
            return result
        mapping = {
            "participant_not_found": ("Participante não encontrado ou inativo.", 401),
            "invalid_qr": ("QR Code inválido ou inativo.", 404),
            "not_started": ("Esta estação ainda não está disponível.", 409),
            "expired": ("O período desta estação terminou. O desafio não aceita mais respostas.", 409),
            "station_not_validated": (
                "Valide primeiro o código físico desta estação.",
                409,
            ),
            "no_challenge": ("Esta estação não possui desafio.", 409),
            "already_completed": ("Este desafio já foi finalizado.", 409),
            "challenge_unavailable": (
                "O desafio desta estação está temporariamente indisponível.",
                503,
            ),
        }
        message, status = mapping.get(
            result.get("error"),
            ("Não foi possível registrar a resposta.", 409),
        )
        raise AppError(message, status)

    def participant_summary(self, participant_id: str) -> dict:
        result = self.repo.rpc(
            "trilhas_participant_summary",
            {"p_participant_id": participant_id},
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise AppError("Não foi possível carregar seu progresso.", 503)
        result.pop("ok", None)
        return result

    def ranking(self) -> list[dict]:
        result = self.repo.rpc("trilhas_team_ranking", {})
        return result if isinstance(result, list) else []
