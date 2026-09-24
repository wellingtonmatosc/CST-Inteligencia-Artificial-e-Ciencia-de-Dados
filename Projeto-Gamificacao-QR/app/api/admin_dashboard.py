from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import current_admin, get_repo, require_admin_role
from app.core.errors import AppError
from app.repositories.supabase_repo import SupabaseRepository

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])
LOCAL_TIMEZONE = ZoneInfo("America/Cuiaba")


class ParticipantActivePayload(BaseModel):
    active: bool


class TestModePayload(BaseModel):
    duration_days: int = Field(ge=1, le=7)
    test_day: int = Field(ge=1, le=7)


class OfficialStartPayload(BaseModel):
    duration_days: int = Field(ge=1, le=7)
    confirmation: str


class ConfirmationPayload(BaseModel):
    confirmation: str


def _count_where(repo: SupabaseRepository, table: str, **filters) -> int:
    query = repo.raw_table(table).select("id", count="exact")
    for key, value in filters.items():
        query = query.eq(key, value)
    result = query.execute()
    return result.count or 0


def _local_access_metadata(value) -> tuple[str | None, bool]:
    if not value:
        return None, False
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        local = parsed.astimezone(LOCAL_TIMEZONE)
        return local.isoformat(), 0 <= local.hour < 6
    except (TypeError, ValueError):
        return None, False


def _recent_activity(repo: SupabaseRepository) -> list[dict]:
    rows = (
        repo.raw_table("station_visits")
        .select(
            "id,participant_id,qr_point_id,validated_at,activity_date,status,"
            "station_points,challenge_points,participants(nick,full_name),qr_points(code,name)"
        )
        .order("validated_at", desc=True)
        .limit(100)
        .execute().data
        or []
    )
    output: list[dict] = []
    for row in rows:
        item = dict(row)
        local_iso, unusual = _local_access_metadata(item.get("validated_at"))
        item["local_access_at"] = local_iso
        item["unusual_hour"] = unusual
        output.append(item)
    return output


def attach_individual_progress(participants: list[dict], ranking: list[dict]) -> list[dict]:
    progress = {str(row.get("id")): row for row in ranking if row.get("id")}
    output: list[dict] = []
    for participant in participants:
        row = dict(participant)
        stats = progress.get(str(row.get("id")), {})
        row["points"] = int(stats.get("points") or 0)
        row["position"] = stats.get("position")
        row["trails_completed"] = int(stats.get("trails_completed") or 0)
        row["stations_validated"] = int(stats.get("stations_validated") or 0)
        row["distinct_qrs"] = int(stats.get("distinct_qrs") or 0)
        row["active_days"] = int(stats.get("active_days") or 0)
        row["correct_answers"] = int(stats.get("correct_answers") or 0)
        row["first_try_correct"] = int(stats.get("first_try_correct") or 0)
        row["best_correct_streak"] = int(stats.get("best_correct_streak") or 0)
        row["tie_count"] = int(stats.get("tie_count") or 1)
        output.append(row)
    return output


def _audit(repo: SupabaseRepository, admin: dict, action: str, participant_id: str, **metadata) -> None:
    repo.insert(
        "audit_log",
        {
            "actor_username": admin["username"],
            "actor_role": admin["role"],
            "action": action,
            "entity_type": "participant",
            "entity_id": participant_id,
            "metadata": metadata,
        },
    )


def _event_control(repo: SupabaseRepository) -> dict:
    rows = repo.select("event_control", singleton=True)
    return rows[0] if rows else {}


@router.get("/event-control")
def event_control(
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    return {
        "control": _event_control(repo),
        "state": repo.rpc("trilhas_event_state", {}) or {},
        "readiness": repo.rpc("trilhas_event_readiness", {}) or {},
    }


@router.put("/event-control/testing")
def set_test_mode(
    payload: TestModePayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    if payload.test_day > payload.duration_days:
        raise AppError("O dia de teste não pode ser maior que a duração escolhida.", 422)
    result = repo.rpc(
        "trilhas_admin_set_test_mode",
        {"p_duration_days": payload.duration_days, "p_test_day": payload.test_day, "p_actor": admin["username"]},
    )
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível iniciar o modo de teste.", 409)
    return result


@router.post("/event-control/clear-tests")
def clear_test_data(
    payload: ConfirmationPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    if payload.confirmation.strip().upper() != "LIMPAR TESTES":
        raise AppError('Digite "LIMPAR TESTES" para confirmar.', 422)
    result = repo.rpc("trilhas_admin_clear_test_data", {"p_actor": admin["username"]})
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("A limpeza só é permitida no modo de teste.", 409)
    return result


@router.post("/event-control/start")
def start_official_event(
    payload: OfficialStartPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    if payload.confirmation.strip().upper() != "INICIAR":
        raise AppError('Digite "INICIAR" para confirmar o início oficial.', 422)
    result = repo.rpc(
        "trilhas_admin_start_official_event",
        {"p_duration_days": payload.duration_days, "p_actor": admin["username"]},
    )
    if not isinstance(result, dict):
        raise AppError("Resposta inválida ao iniciar o evento.", 503)
    if not result.get("ok"):
        if result.get("error") == "event_not_ready":
            raise AppError("O evento ainda não está pronto: confira os 15 QRs, códigos físicos e o banco de questões.", 409)
        raise AppError("Não foi possível iniciar o evento.", 409)
    return result


@router.post("/event-control/end")
def end_official_event(
    payload: ConfirmationPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    if payload.confirmation.strip().upper() != "ENCERRAR":
        raise AppError('Digite "ENCERRAR" para confirmar.', 422)
    result = repo.rpc("trilhas_admin_end_event", {"p_actor": admin["username"]})
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível encerrar o evento.", 409)
    return result


@router.get("/dashboard-data")
def dashboard_data(
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")

    participants = (
        repo.raw_table("participants")
        .select("id,full_name,nick,participant_type,campus,course_name,active,is_organizer,created_at")
        .order("full_name")
        .limit(1000)
        .execute().data
        or []
    )
    ranking = repo.rpc("trilhas_individual_ranking", {}) or []
    if not isinstance(ranking, list):
        ranking = []

    participants = attach_individual_progress(participants, ranking)
    competitors = [p for p in participants if p.get("active") and not p.get("is_organizer")]
    recent_activity = _recent_activity(repo)
    unusual_recent = sum(1 for row in recent_activity if row.get("unusual_hour"))
    shared_positions = sum(1 for row in ranking if int(row.get("tie_count") or 1) > 1)

    return {
        "mode": "individual",
        "admin_mode": "single",
        "participants": participants,
        "ranking": ranking,
        "event_control": _event_control(repo),
        "recent_activity": recent_activity,
        "monitoring": {
            "timezone": "America/Cuiaba",
            "unusual_window": "00:00–05:59",
            "unusual_recent": unusual_recent,
            "policy": "signal_only",
        },
        "ranking_rules": {
            "order": ["points", "trails_completed", "stations_validated"],
            "exact_ties_share_position": True,
            "speed_used": False,
        },
        "stats": {
            "participants_total": len(participants),
            "participants_active": sum(1 for p in participants if p.get("active")),
            "competitors_active": len(competitors),
            "points_total": sum(int(row.get("points") or 0) for row in ranking),
            "active_stations": _count_where(repo, "qr_points", active=True),
            "active_questions": _count_where(repo, "questions", active=True),
            "trails_total": _count_where(repo, "trails", active=True),
            "validations_total": _count_where(repo, "station_visits"),
            "pending_challenges": _count_where(repo, "station_visits", status="validated"),
            "unusual_recent": unusual_recent,
            "shared_positions": shared_positions,
        },
    }


@router.post("/participants/{participant_id}/active")
def set_participant_active(
    participant_id: str,
    payload: ParticipantActivePayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    rows = repo.select("participants", id=participant_id)
    if not rows:
        raise AppError("Participante não encontrado.", 404)

    repo.update("participants", {"active": payload.active}, id=participant_id)
    _audit(repo, admin, "participant_active_changed", participant_id, active=payload.active)
    return {"ok": True, "active": payload.active}
