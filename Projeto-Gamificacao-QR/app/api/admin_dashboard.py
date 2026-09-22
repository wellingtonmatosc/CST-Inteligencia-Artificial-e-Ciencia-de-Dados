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


class FinalTiebreakPayload(BaseModel):
    score: int = Field(ge=0, le=100)
    note: str | None = Field(default=None, max_length=500)


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
    """Combina cadastro administrativo com progresso e critérios de desempate."""
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
        row["needs_final_tiebreak"] = bool(stats.get("needs_final_tiebreak"))
        row["final_tiebreak_score"] = int(stats.get("final_tiebreak_score") or 0)
        row["final_tiebreak_recorded"] = bool(stats.get("final_tiebreak_recorded"))
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


def _event_days(repo: SupabaseRepository) -> list[dict]:
    return (
        repo.raw_table("event_days")
        .select("day_number,label,event_date,active,is_final_event,updated_at")
        .order("day_number")
        .execute().data
        or []
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
    event_days = _event_days(repo)
    final_day = next((day for day in event_days if day.get("is_final_event")), None)
    unresolved_ties = sum(1 for row in ranking if row.get("needs_final_tiebreak"))

    return {
        "mode": "individual",
        "admin_mode": "single",
        "participants": participants,
        "ranking": ranking,
        "event_days": event_days,
        "final_day": final_day,
        "recent_activity": recent_activity,
        "monitoring": {
            "timezone": "America/Cuiaba",
            "unusual_window": "00:00–05:59",
            "unusual_recent": unusual_recent,
            "policy": "signal_only",
        },
        "ranking_rules": {
            "order": [
                "points",
                "correct_answers",
                "first_try_correct",
                "distinct_qrs",
                "active_days",
                "final_tiebreak_score",
            ],
            "final_tiebreak": "supervised_day_7",
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
            "unresolved_ties": unresolved_ties,
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


@router.put("/final-tiebreak/{participant_id}")
def set_final_tiebreak(
    participant_id: str,
    payload: FinalTiebreakPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    participants = repo.select("participants", id=participant_id)
    if not participants:
        raise AppError("Participante não encontrado.", 404)
    if participants[0].get("is_organizer"):
        raise AppError("Contas da organização não participam do desempate.", 422)

    now_iso = datetime.now(LOCAL_TIMEZONE).isoformat()
    data = {
        "score": payload.score,
        "note": (payload.note or "").strip() or None,
        "recorded_by": admin["username"],
        "updated_at": now_iso,
    }
    existing = repo.select("final_tiebreak_results", participant_id=participant_id)
    if existing:
        updated = repo.update("final_tiebreak_results", data, participant_id=participant_id)
        result = updated[0] if updated else {"participant_id": participant_id, **data}
    else:
        result = repo.insert(
            "final_tiebreak_results",
            {"participant_id": participant_id, "recorded_at": now_iso, **data},
        )

    _audit(
        repo,
        admin,
        "final_tiebreak_recorded",
        participant_id,
        score=payload.score,
        note=data["note"],
    )
    return {"ok": True, "result": result}


@router.delete("/final-tiebreak/{participant_id}")
def clear_final_tiebreak(
    participant_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    existing = repo.select("final_tiebreak_results", participant_id=participant_id)
    if not existing:
        return {"ok": True, "removed": False}
    previous_score = int(existing[0].get("score") or 0)
    repo.delete("final_tiebreak_results", participant_id=participant_id)
    _audit(
        repo,
        admin,
        "final_tiebreak_cleared",
        participant_id,
        previous_score=previous_score,
    )
    return {"ok": True, "removed": True}
