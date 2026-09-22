from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import current_admin, get_repo, require_admin_role
from app.core.errors import AppError
from app.repositories.supabase_repo import SupabaseRepository

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])
LOCAL_TIMEZONE = ZoneInfo("America/Cuiaba")


class ParticipantActivePayload(BaseModel):
    active: bool


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
        # Apenas sinaliza para revisão; nunca bloqueia nem altera pontuação.
        item["unusual_hour"] = unusual
        output.append(item)
    return output


def attach_individual_progress(participants: list[dict], ranking: list[dict]) -> list[dict]:
    """Combina cadastro administrativo com o progresso competitivo individual."""
    progress = {str(row.get("id")): row for row in ranking if row.get("id")}
    output: list[dict] = []
    for participant in participants:
        row = dict(participant)
        stats = progress.get(str(row.get("id")), {})
        row["points"] = int(stats.get("points") or 0)
        row["position"] = stats.get("position")
        row["trails_completed"] = int(stats.get("trails_completed") or 0)
        row["stations_validated"] = int(stats.get("stations_validated") or 0)
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

    return {
        "mode": "individual",
        "admin_mode": "single",
        "participants": participants,
        "ranking": ranking,
        "recent_activity": recent_activity,
        "monitoring": {
            "timezone": "America/Cuiaba",
            "unusual_window": "00:00–05:59",
            "unusual_recent": unusual_recent,
            "policy": "signal_only",
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
