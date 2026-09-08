"""Cadastro, login, sessão, recuperação e logout de participantes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.errors import AppError
from app.core.security import (
    hash_password,
    random_access_code,
    random_token,
    sha256_hex,
    verify_password,
)
from app.repositories.supabase_repo import SupabaseRepository
from app.services.moderation import NickModerationService, normalize_for_moderation


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

        existing = (
            self.repo.raw_table("participants")
            .select("id")
            .ilike("nick", payload["nick"].strip())
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            raise AppError("Esse nick já está em uso.", 409)

        access_code = random_access_code()
        participant = self.repo.insert(
            "participants",
            {
                "full_name": payload["full_name"].strip(),
                "nick": payload["nick"].strip(),
                "participant_type": participant_type,
                "registration": payload.get("registration") or None,
                "course_class": payload.get("course_class") or None,
                "institution": payload.get("institution") or None,
                "password_hash": hash_password(payload["password"]),
                "access_code_hash": sha256_hex(access_code),
            },
        )
        session_token = self._create_session(participant["id"])
        return participant, session_token, access_code

    def login(self, nick: str, password: str) -> tuple[dict, str]:
        rows = (
            self.repo.raw_table("participants")
            .select("*")
            .ilike("nick", nick.strip())
            .eq("active", True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            raise AppError("Nick ou senha inválidos.", 401)

        participant = rows[0]
        password_hash = participant.get("password_hash") or ""
        if not password_hash:
            raise AppError(
                "Esta conta ainda não possui senha. Defina uma senha na sessão atual ou use o código de recuperação.",
                409,
            )
        if not verify_password(password_hash, password):
            raise AppError("Nick ou senha inválidos.", 401)

        return participant, self._create_session(participant["id"])

    def recover(self, access_code: str, new_password: str) -> tuple[dict, str, str]:
        """Redefine a senha usando o código e rotaciona o próprio código de recuperação."""
        code_hash = sha256_hex(access_code.strip().upper())
        rows = self.repo.select("participants", access_code_hash=code_hash, active=True)
        if not rows:
            raise AppError("Código de recuperação inválido.", 404)

        participant = rows[0]
        new_access_code = random_access_code()
        self.repo.update(
            "participants",
            {
                "password_hash": hash_password(new_password),
                "access_code_hash": sha256_hex(new_access_code),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            id=participant["id"],
        )
        participant["password_hash"] = "updated"
        session_token = self._create_session(participant["id"])
        return participant, session_token, new_access_code

    def set_password(self, participant_id: str, password: str) -> None:
        """Cria ou altera a senha a partir de uma sessão já autenticada."""
        self.repo.update(
            "participants",
            {
                "password_hash": hash_password(password),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            id=participant_id,
        )

    def _create_session(self, participant_id: str) -> str:
        token = random_token()
        expires = datetime.now(timezone.utc) + timedelta(days=self.session_days)
        self.repo.insert(
            "participant_sessions",
            {
                "participant_id": participant_id,
                "token_hash": sha256_hex(token),
                "expires_at": expires.isoformat(),
            },
        )
        return token

    def get_by_session(self, token: str) -> dict:
        """Valida a sessão e obtém o participante em uma única chamada ao banco."""
        result = self.repo.rpc(
            "game_participant_from_session",
            {"p_token_hash": sha256_hex(token)},
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise AppError("Sessão inválida ou expirada.", 401)
        participant = result.get("participant")
        if not participant:
            raise AppError("Participante não encontrado.", 401)
        return participant

    def logout(self, token: str | None) -> None:
        """Revoga a sessão atual no servidor; é idempotente."""
        if not token:
            return
        self.repo.update(
            "participant_sessions",
            {"revoked_at": datetime.now(timezone.utc).isoformat()},
            token_hash=sha256_hex(token),
        )
