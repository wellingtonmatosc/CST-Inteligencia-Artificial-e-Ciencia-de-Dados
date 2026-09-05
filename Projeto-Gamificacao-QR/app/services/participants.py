"""Cadastro, sessão e recuperação de participantes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from app.core.errors import AppError
from app.core.security import random_access_code, random_token, sha256_hex
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

        existing = self.repo.raw_table("participants").select("id").ilike("nick", payload["nick"].strip()).execute().data or []
        if existing:
            raise AppError("Esse nick já está em uso.", 409)

        access_code = random_access_code()
        participant = self.repo.insert("participants", {
            "full_name": payload["full_name"].strip(),
            "nick": payload["nick"].strip(),
            "participant_type": participant_type,
            "registration": payload.get("registration") or None,
            "course_class": payload.get("course_class") or None,
            "institution": payload.get("institution") or None,
            "access_code_hash": sha256_hex(access_code),
        })
        session_token = self._create_session(participant["id"])
        return participant, session_token, access_code

    def recover(self, access_code: str) -> tuple[dict, str]:
        code_hash = sha256_hex(access_code.strip().upper())
        rows = self.repo.select("participants", access_code_hash=code_hash, active=True)
        if not rows:
            raise AppError("Código de recuperação inválido.", 404)
        participant = rows[0]
        session_token = self._create_session(participant["id"])
        return participant, session_token

    def _create_session(self, participant_id: str) -> str:
        token = random_token()
        expires = datetime.now(timezone.utc) + timedelta(days=self.session_days)
        self.repo.insert("participant_sessions", {
            "participant_id": participant_id,
            "token_hash": sha256_hex(token),
            "expires_at": expires.isoformat(),
        })
        return token

    def get_by_session(self, token: str) -> dict:
        token_hash = sha256_hex(token)
        now = datetime.now(timezone.utc).isoformat()
        sessions = (
            self.repo.raw_table("participant_sessions")
            .select("id,participant_id,expires_at,revoked_at")
            .eq("token_hash", token_hash)
            .is_("revoked_at", "null")
            .gt("expires_at", now)
            .limit(1)
            .execute().data or []
        )
        if not sessions:
            raise AppError("Sessão inválida ou expirada.", 401)
        self.repo.update("participant_sessions", {"last_seen_at": now}, id=sessions[0]["id"])
        participants = self.repo.select("participants", id=sessions[0]["participant_id"], active=True)
        if not participants:
            raise AppError("Participante não encontrado.", 401)
        return participants[0]
