from functools import lru_cache

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import read_admin_session
from app.repositories.supabase_repo import SupabaseRepository
from app.services.moderation import NickModerationService
from app.services.participants import ParticipantService
from app.services.trilhas import TrilhasService


@lru_cache
def _shared_repo() -> SupabaseRepository:
    """Mantém o pool HTTP do Supabase entre requisições enquanto o processo estiver ativo."""
    return SupabaseRepository(get_settings())


def get_repo() -> SupabaseRepository:
    return _shared_repo()


def get_participant_service(
    repo: SupabaseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> ParticipantService:
    return ParticipantService(
        repo,
        NickModerationService(settings.blocked_nick_terms),
        settings.participant_session_days,
    )


def get_trilhas_service(
    repo: SupabaseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> TrilhasService:
    return TrilhasService(repo, settings.event_timezone)


def current_participant(
    request: Request,
    service: ParticipantService = Depends(get_participant_service),
    settings: Settings = Depends(get_settings),
):
    token = request.cookies.get(settings.participant_cookie_name)
    if not token:
        raise AppError("Entre ou crie sua conta para continuar.", 401)
    return service.get_by_session(token)


def current_admin(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    token = request.cookies.get(settings.admin_cookie_name, "")
    data = read_admin_session(
        settings.admin_session_secret,
        token,
        settings.admin_session_hours * 3600,
    )
    if not data:
        raise AppError("Acesso administrativo não autorizado.", 401)
    return data


def require_admin_role(admin: dict, *allowed: str) -> None:
    if admin.get("role") not in set(allowed):
        raise AppError("Seu perfil não tem permissão para esta operação.", 403)
