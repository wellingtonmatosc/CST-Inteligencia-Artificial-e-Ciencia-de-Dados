"""Administração do pool de questões da gamificação por estação e dia."""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import current_admin, get_repo, require_admin_role
from app.core.errors import AppError
from app.repositories.supabase_repo import SupabaseRepository

router = APIRouter(prefix="/api/admin", tags=["admin-question-pool"])


class QuestionPoolPayload(BaseModel):
    station_id: str
    question_id: str
    day_number: int | None = Field(default=None, ge=1, le=7)


class EventDayPayload(BaseModel):
    label: str = Field(min_length=3, max_length=80)
    event_date: date | None = None
    active: bool = True


def _audit(repo: SupabaseRepository, admin: dict, action: str, entity_type: str, entity_id=None, **metadata) -> None:
    repo.insert(
        "audit_log",
        {
            "actor_username": admin["username"],
            "actor_role": admin["role"],
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "metadata": metadata,
        },
    )


def _ensure_exists(repo: SupabaseRepository, table: str, item_id: str, label: str) -> None:
    if not repo.raw_table(table).select("id").eq("id", item_id).limit(1).execute().data:
        raise AppError(f"{label} não encontrado(a).", 404)


@router.get("/question-pool")
def list_question_pool(
    _: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    links = (
        repo.raw_table("station_question_pool")
        .select("id,qr_point_id,question_id,day_number,active,created_at,updated_at")
        .order("created_at")
        .execute().data
        or []
    )
    days = (
        repo.raw_table("event_days")
        .select("day_number,label,event_date,active,is_final_event,updated_at")
        .order("day_number")
        .execute().data
        or []
    )
    stations = repo.raw_table("qr_points").select("id,code,name,active").order("code").execute().data or []
    questions = repo.raw_table("questions").select("id,prompt,kind,difficulty,category_id,active").order("created_at", desc=True).execute().data or []
    categories = repo.raw_table("categories").select("id,slug,name,active").order("name").execute().data or []
    return {
        "links": links,
        "event_days": days,
        "stations": stations,
        "questions": questions,
        "categories": categories,
    }


@router.post("/question-pool")
def add_question_to_pool(
    payload: QuestionPoolPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    _ensure_exists(repo, "qr_points", payload.station_id, "Estação")
    _ensure_exists(repo, "questions", payload.question_id, "Questão")

    candidates = (
        repo.raw_table("station_question_pool")
        .select("id,day_number,active")
        .eq("qr_point_id", payload.station_id)
        .eq("question_id", payload.question_id)
        .execute().data
        or []
    )
    for row in candidates:
        if row.get("day_number") == payload.day_number:
            if not row.get("active", True):
                repo.update("station_question_pool", {"active": True, "updated_at": datetime.utcnow().isoformat() + "Z"}, id=row["id"])
            return {"link": {**row, "active": True}, "already_existed": True}

    link = repo.insert(
        "station_question_pool",
        {
            "qr_point_id": payload.station_id,
            "question_id": payload.question_id,
            "day_number": payload.day_number,
            "active": True,
        },
    )
    _audit(
        repo,
        admin,
        "question_pool_link_created",
        "question_pool_link",
        link["id"],
        station_id=payload.station_id,
        question_id=payload.question_id,
        day_number=payload.day_number,
    )
    return {"link": link, "already_existed": False}


@router.delete("/question-pool/{link_id}")
def remove_question_from_pool(
    link_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    rows = repo.raw_table("station_question_pool").select("id,qr_point_id,question_id,day_number").eq("id", link_id).limit(1).execute().data or []
    if not rows:
        raise AppError("Vínculo do banco de questões não encontrado.", 404)
    row = rows[0]
    repo.delete("station_question_pool", id=link_id)
    _audit(repo, admin, "question_pool_link_removed", "question_pool_link", link_id, **row)
    return {"ok": True}


@router.put("/event-days/{day_number}")
def update_event_day(
    day_number: int,
    payload: EventDayPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    if day_number < 1 or day_number > 7:
        raise AppError("O dia do evento deve ficar entre 1 e 7.", 422)

    rows = repo.raw_table("event_days").select("day_number,is_final_event").eq("day_number", day_number).limit(1).execute().data or []
    if not rows:
        raise AppError("Dia do evento não encontrado.", 404)

    data = {
        "label": payload.label.strip(),
        "event_date": payload.event_date.isoformat() if payload.event_date else None,
        "active": payload.active,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    repo.update("event_days", data, day_number=day_number)
    _audit(repo, admin, "event_day_updated", "event_day", day_number, **data)
    return {"day_number": day_number, **data, "is_final_event": rows[0].get("is_final_event", False)}
