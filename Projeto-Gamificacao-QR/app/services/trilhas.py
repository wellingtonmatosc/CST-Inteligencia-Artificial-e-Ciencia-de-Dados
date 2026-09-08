"""Regras da experiência Trilhas Poéticas definida no projeto de extensão.

O serviço mantém as leituras simples no backend e delega ao PostgreSQL as
operações que precisam ser atômicas: validação da estação, pontuação,
sequências e resposta do desafio.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

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
        self.timezone = ZoneInfo(timezone_name)

    def _now(self) -> datetime:
        return datetime.now(self.timezone)

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _question(self, question_id: str | None) -> dict | None:
        if not question_id:
            return None
        rows = (
            self.repo.raw_table("questions")
            .select("id,kind,prompt,options,difficulty,media_type,media_url,accessibility,active")
            .eq("id", question_id)
            .eq("active", True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def _trail_for_qr(self, qr_id: str, participant_id: str) -> dict | None:
        steps = (
            self.repo.raw_table("trail_steps")
            .select("trail_id,step_number")
            .eq("qr_point_id", qr_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not steps:
            return None
        step = steps[0]
        trails = (
            self.repo.raw_table("trails")
            .select("id,slug,name,description,completion_points,completion_title,completion_body,active")
            .eq("id", step["trail_id"])
            .limit(1)
            .execute()
            .data
            or []
        )
        if not trails:
            return None
        all_steps = (
            self.repo.raw_table("trail_steps")
            .select("qr_point_id,step_number")
            .eq("trail_id", step["trail_id"])
            .order("step_number")
            .execute()
            .data
            or []
        )
        completed_rows = self.repo.select(
            "trail_completions",
            "id,points_awarded,completed_at",
            participant_id=participant_id,
            trail_id=step["trail_id"],
        )
        return {
            **trails[0],
            "step_number": step["step_number"],
            "step_count": len(all_steps),
            "completed": bool(completed_rows),
            "completion": completed_rows[0] if completed_rows else None,
        }

    def get_station(self, participant_id: str, code: str) -> dict:
        rows = (
            self.repo.raw_table("qr_points")
            .select("id,code,name,zone_id,station_type,base_points,validation_code_hash,active_from,active_until,location_hint,active")
            .ilike("code", code.strip())
            .eq("active", True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            raise AppError("QR Code inválido ou inativo.", 404)

        qr = rows[0]
        zone_rows = self.repo.select("zones", "id,slug,name", id=qr["zone_id"])
        zone = zone_rows[0] if zone_rows else None
        visit_rows = self.repo.select("station_visits", "*", participant_id=participant_id, qr_point_id=qr["id"])
        visit = visit_rows[0] if visit_rows else None
        trail = self._trail_for_qr(qr["id"], participant_id) if qr.get("station_type") == "sequential" else None

        now = self._now()
        starts = self._parse_datetime(qr.get("active_from"))
        ends = self._parse_datetime(qr.get("active_until"))
        available = True
        availability_reason = None
        if starts and now < starts.astimezone(self.timezone):
            available = False
            availability_reason = "not_started"
        elif ends and now >= ends.astimezone(self.timezone):
            available = False
            availability_reason = "expired"

        payload = {
            "mode": "trail_station",
            "qr": {
                "id": qr["id"],
                "code": qr["code"],
                "name": qr["name"],
                "station_type": qr.get("station_type") or "permanent",
                "station_type_label": STATION_LABELS.get(qr.get("station_type"), "Estação"),
                "base_points": qr.get("base_points") or 0,
                "location_hint": qr.get("location_hint"),
                "zone": zone,
                "active_from": qr.get("active_from"),
                "active_until": qr.get("active_until"),
            },
            "available": available,
            "availability_reason": availability_reason,
            "validated": bool(visit),
            "requires_physical_code": bool(qr.get("validation_code_hash")),
            "trail": trail,
        }

        if not visit:
            return payload

        content_rows = self.repo.select("station_contents", "*", qr_point_id=qr["id"])
        content = content_rows[0] if content_rows else None
        question = self._question(content.get("challenge_question_id") if content else None)
        attempt_rows = (
            self.repo.raw_table("station_attempts")
            .select("attempt_number,correct,answered_at")
            .eq("station_visit_id", visit["id"])
            .order("attempt_number")
            .execute()
            .data
            or []
        )
        last_attempt = attempt_rows[-1] if attempt_rows else None
        if not question:
            challenge_status = "none"
        elif visit["status"] != "completed":
            challenge_status = "pending"
        elif visit.get("challenge_points", 0) > 0:
            challenge_status = "correct"
        elif last_attempt:
            challenge_status = "finished"
        else:
            challenge_status = "none"

        payload.update({"visit": visit, "content": content, "question": question, "challenge_status": challenge_status, "attempts": attempt_rows})
        return payload

    def validate_station(self, participant_id: str, code: str, physical_code: str | None) -> dict:
        result = self.repo.rpc("trilhas_validate_station", {"p_participant_id": participant_id, "p_code": code, "p_physical_code": physical_code})
        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)
        if result.get("ok"):
            return result
        mapping = {
            "participant_not_found": ("Participante não encontrado.", 401),
            "invalid_qr": ("QR Code inválido ou inativo.", 404),
            "invalid_physical_code": ("Código da estação incorreto. Confira o código exibido junto ao QR.", 422),
            "sequence_locked": ("Esta etapa está bloqueada. Conclua primeiro as etapas anteriores da trilha.", 409),
            "sequence_not_configured": ("Esta sequência ainda não foi configurada pela organização.", 503),
            "not_started": ("Esta estação ainda não está disponível.", 409),
            "expired": ("O período desta estação terminou.", 409),
        }
        message, status = mapping.get(result.get("error"), ("Não foi possível validar esta estação.", 409))
        raise AppError(message, status)

    def answer_challenge(self, participant_id: str, code: str, answer) -> dict:
        result = self.repo.rpc("trilhas_answer_challenge", {"p_participant_id": participant_id, "p_code": code, "p_answer": answer})
        if not isinstance(result, dict):
            raise AppError("Resposta inválida do banco de dados.", 503)
        if result.get("ok"):
            return result
        mapping = {
            "invalid_qr": ("QR Code inválido ou inativo.", 404),
            "station_not_validated": ("Valide primeiro o código físico desta estação.", 409),
            "no_challenge": ("Esta estação não possui desafio.", 409),
            "already_completed": ("Este desafio já foi finalizado.", 409),
            "challenge_unavailable": ("O desafio desta estação está temporariamente indisponível.", 503),
        }
        message, status = mapping.get(result.get("error"), ("Não foi possível registrar a resposta.", 409))
        raise AppError(message, status)

    def participant_summary(self, participant_id: str) -> dict:
        result = self.repo.rpc("trilhas_participant_summary", {"p_participant_id": participant_id})
        if not isinstance(result, dict) or not result.get("ok"):
            raise AppError("Não foi possível carregar seu progresso.", 503)
        result.pop("ok", None)
        return result

    def ranking(self) -> list[dict]:
        result = self.repo.rpc("trilhas_team_ranking", {})
        return result if isinstance(result, list) else []
