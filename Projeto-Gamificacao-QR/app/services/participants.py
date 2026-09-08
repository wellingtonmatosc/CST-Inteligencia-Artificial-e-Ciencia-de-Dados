"""Cadastro, login, sessão, recuperação e vínculo opcional à base institucional."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.errors import AppError
from app.core.security import hash_password, random_access_code, random_token, sha256_hex, verify_password
from app.repositories.supabase_repo import SupabaseRepository
from app.services.moderation import NickModerationService, normalize_for_moderation

MAX_PIN_FAILURES = 5
PIN_LOCK_MINUTES = 2


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class ParticipantService:
    def __init__(self, repo: SupabaseRepository, moderation: NickModerationService, session_days: int = 30):
        self.repo = repo
        self.moderation = moderation
        self.session_days = session_days

    def register(self, payload: dict) -> tuple[dict, str, str]:
        ok, reason = self.moderation.validate(payload["nick"])
        if not ok:
            raise AppError(reason or "Nick inválido.", 422)

        participant_type = payload["participant_type"]
        if participant_type == "student" and not payload.get("registration"):
            raise AppError("Matrícula é obrigatória para aluno.", 422)
        if participant_type == "student" and not payload.get("course_class"):
            raise AppError("Curso/turma é obrigatório para aluno.", 422)

        normalized_nick = normalize_for_moderation(payload["nick"])
        for row in self.repo.select("blocked_terms", active=True):
            term = normalize_for_moderation(row.get("term", ""))
            if term and term in normalized_nick:
                raise AppError("Esse nome de usuário não pode ser utilizado. Escolha outro.", 422)

        existing = self.repo.raw_table("participants").select("id").ilike("nick", payload["nick"].strip()).limit(1).execute().data or []
        if existing:
            raise AppError("Esse nick já está em uso.", 409)

        access_code = random_access_code()
        participant = self.repo.insert("participants", {
            "full_name": payload["full_name"].strip(),
            "nick": payload["nick"].strip(),
            "participant_type": participant_type,
            "registration": (payload.get("registration") or "").strip() or None,
            "course_class": payload.get("course_class") or None,
            "institution": payload.get("institution") or None,
            "password_hash": hash_password(payload["pin"]),
            "access_code_hash": sha256_hex(access_code),
        })

        if not participant.get("is_organizer") and not participant.get("team_id"):
            team_id = self.repo.rpc("trilhas_assign_team", {"p_participant_id": participant["id"]})
            if team_id:
                participant["team_id"] = team_id

        session_token = self._create_session(participant["id"])
        return participant, session_token, access_code

    def login(self, nick: str, pin: str) -> tuple[dict, str]:
        rows = self.repo.raw_table("participants").select("*").ilike("nick", nick.strip()).eq("active", True).limit(1).execute().data or []
        if not rows:
            raise AppError("Nick ou PIN inválidos.", 401)

        participant = rows[0]
        now = datetime.now(timezone.utc)
        locked_until = _parse_datetime(participant.get("pin_locked_until"))
        if locked_until and locked_until > now:
            raise AppError("Muitas tentativas de PIN. Aguarde alguns minutos e tente novamente.", 429)

        password_hash = participant.get("password_hash") or ""
        if not password_hash:
            raise AppError("Esta conta ainda não possui PIN. Defina um PIN na sessão atual ou use o código de recuperação.", 409)

        if not verify_password(password_hash, pin):
            failures = int(participant.get("pin_failed_attempts") or 0) + 1
            update = {"pin_failed_attempts": failures, "pin_locked_until": None}
            if failures >= MAX_PIN_FAILURES:
                update = {"pin_failed_attempts": 0, "pin_locked_until": (now + timedelta(minutes=PIN_LOCK_MINUTES)).isoformat()}
            self.repo.update("participants", update, id=participant["id"])
            raise AppError("Nick ou PIN inválidos.", 401)

        if participant.get("pin_failed_attempts") or participant.get("pin_locked_until"):
            self.repo.update("participants", {"pin_failed_attempts": 0, "pin_locked_until": None}, id=participant["id"])
        return participant, self._create_session(participant["id"])

    def recover(self, access_code: str, new_pin: str) -> tuple[dict, str, str]:
        code_hash = sha256_hex(access_code.strip().upper())
        rows = self.repo.select("participants", access_code_hash=code_hash, active=True)
        if not rows:
            raise AppError("Código de recuperação inválido.", 404)

        participant = rows[0]
        new_access_code = random_access_code()
        self.repo.update("participants", {
            "password_hash": hash_password(new_pin),
            "access_code_hash": sha256_hex(new_access_code),
            "pin_failed_attempts": 0,
            "pin_locked_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, id=participant["id"])
        session_token = self._create_session(participant["id"])
        return participant, session_token, new_access_code

    def set_pin(self, participant_id: str, pin: str) -> None:
        self.repo.update("participants", {
            "password_hash": hash_password(pin),
            "pin_failed_attempts": 0,
            "pin_locked_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, id=participant_id)

    def _create_session(self, participant_id: str) -> str:
        token = random_token()
        expires = datetime.now(timezone.utc) + timedelta(days=self.session_days)
        self.repo.insert("participant_sessions", {"participant_id": participant_id, "token_hash": sha256_hex(token), "expires_at": expires.isoformat()})
        return token

    def get_by_session(self, token: str) -> dict:
        result = self.repo.rpc("game_participant_from_session", {"p_token_hash": sha256_hex(token)})
        if not isinstance(result, dict) or not result.get("ok"):
            raise AppError("Sessão inválida ou expirada.", 401)
        participant = result.get("participant")
        if not participant:
            raise AppError("Participante não encontrado.", 401)
        return participant

    def get_home_state_by_session(self, token: str) -> dict:
        result = self.repo.rpc(
            "trilhas_home_state_from_session",
            {"p_token_hash": sha256_hex(token)},
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise AppError("Sessão inválida ou expirada.", 401)
        participant = result.get("participant")
        summary = result.get("summary")
        if not participant or not isinstance(summary, dict):
            raise AppError("Não foi possível carregar seu progresso.", 503)
        return {"participant": participant, "summary": summary}

    def logout(self, token: str | None) -> None:
        if not token:
            return
        self.repo.update("participant_sessions", {"revoked_at": datetime.now(timezone.utc).isoformat()}, token_hash=sha256_hex(token))
