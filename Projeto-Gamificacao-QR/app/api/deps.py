from fastapi import Depends, Request
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import verify_admin_session
from app.repositories.supabase_repo import SupabaseRepository
from app.services.moderation import NickModerationService
from app.services.participants import ParticipantService
from app.services.gamification import GamificationService


def get_repo(settings: Settings = Depends(get_settings)) -> SupabaseRepository:
    return SupabaseRepository(settings)


def get_participant_service(repo: SupabaseRepository = Depends(get_repo), settings: Settings = Depends(get_settings)) -> ParticipantService:
    return ParticipantService(repo, NickModerationService(settings.blocked_nick_terms), settings.participant_session_days)


def get_gamification_service(repo: SupabaseRepository = Depends(get_repo), settings: Settings = Depends(get_settings)) -> GamificationService:
    return GamificationService(repo, settings.event_timezone)


def current_participant(request: Request, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    token = request.cookies.get(settings.participant_cookie_name)
    if not token:
        raise AppError("Faça seu cadastro ou recupere sua sessão para continuar.", 401)
    return service.get_by_session(token)


def current_admin(request: Request, settings: Settings = Depends(get_settings)):
    token = request.cookies.get(settings.admin_cookie_name, "")
    if not verify_admin_session(settings.admin_session_secret, token, settings.admin_session_hours * 3600):
        raise AppError("Acesso administrativo não autorizado.", 401)
    return True
