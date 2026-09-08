"""Administração da experiência Trilhas Poéticas.

O navegador nunca acessa o Supabase diretamente. Toda alteração passa pelo
FastAPI, por sessão administrativa assinada e por verificação de papel.
"""
from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app.api.deps import current_admin, get_repo, require_admin_role
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import hash_password, sha256_hex, sign_admin_session, verify_password
from app.repositories.supabase_repo import SupabaseRepository
from app.services.questions import validate_accessibility_metadata

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_ROLES = {"admin", "operator", "validator", "viewer"}
STATION_TYPES = {"permanent", "sequential", "temporary", "special"}
ACTION_TYPES = {
    "recitation",
    "original_work",
    "poem_suggestion",
    "selected_suggestion",
    "artistic_production",
    "social_post",
    "event_participation",
    "other",
}


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class QuestionPayload(BaseModel):
    category_id: str
    kind: str = Field(pattern="^(multiple_choice|true_false|short_text)$")
    prompt: str = Field(min_length=5, max_length=2000)
    options: list = Field(default_factory=list)
    correct_answer: dict
    explanation: str | None = None
    difficulty: int = Field(default=1, ge=1, le=5)
    media_type: str | None = Field(default=None, pattern="^(image|audio|video)$")
    media_url: str | None = None
    accessibility: dict
    active: bool = True


class StationPayload(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=160)
    zone_id: str
    station_type: str = Field(pattern="^(permanent|sequential|temporary|special)$")
    base_points: int = Field(ge=0, le=1000)
    physical_code: str | None = Field(default=None, max_length=80)
    active_from: datetime | None = None
    active_until: datetime | None = None
    location_hint: str | None = Field(default=None, max_length=300)
    active: bool = True


class StationContentPayload(BaseModel):
    content_kind: str = Field(pattern="^(poetry|literature|art|culture|regional|mixed)$")
    title: str = Field(min_length=2, max_length=240)
    body: str | None = Field(default=None, max_length=8000)
    author_name: str | None = Field(default=None, max_length=240)
    media_type: str | None = Field(default=None, pattern="^(image|audio|video)$")
    media_url: str | None = Field(default=None, max_length=2000)
    accessibility: dict = Field(default_factory=dict)
    challenge_question_id: str | None = None
    challenge_points: int = Field(default=10, ge=0, le=20)
    completion_body: str | None = Field(default=None, max_length=4000)


class TrailPayload(BaseModel):
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=1000)
    completion_points: int = Field(default=30, ge=0, le=500)
    completion_title: str | None = Field(default=None, max_length=240)
    completion_body: str | None = Field(default=None, max_length=4000)
    active: bool = True


class TrailStepsPayload(BaseModel):
    qr_point_ids: list[str] = Field(min_length=1, max_length=20)


class OrganizerPayload(BaseModel):
    is_organizer: bool


class ManualPointsPayload(BaseModel):
    participant_id: str
    action_type: str
    description: str = Field(min_length=3, max_length=1000)
    evidence: str | None = Field(default=None, max_length=2000)
    points: int = Field(ge=0, le=200)


class ReversePayload(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AdminUserPayload(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=10, max_length=200)
    role: str = Field(pattern="^(admin|operator|validator|viewer)$")


class BlockedTermPayload(BaseModel):
    term: str = Field(min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=200)


def _set_admin_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        settings.admin_cookie_name,
        token,
        max_age=settings.admin_session_hours * 3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


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


def _count(repo: SupabaseRepository, table: str) -> int:
    result = repo.raw_table(table).select("id", count="exact").execute()
    return result.count or 0


def _station_data(payload: StationPayload, *, keep_hash: str | None = None) -> dict:
    if payload.active_from and payload.active_until and payload.active_until <= payload.active_from:
        raise AppError("O fim da janela precisa ser posterior ao início.", 422)
    physical = (payload.physical_code or "").strip().upper()
    return {
        "code": payload.code.strip().upper(),
        "name": payload.name.strip(),
        "zone_id": payload.zone_id,
        "station_type": payload.station_type,
        "base_points": payload.base_points,
        "validation_code_hash": sha256_hex(physical) if physical else keep_hash,
        "active_from": payload.active_from.isoformat() if payload.active_from else None,
        "active_until": payload.active_until.isoformat() if payload.active_until else None,
        "location_hint": (payload.location_hint or "").strip() or None,
        "active": payload.active,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/login")
def login(
    payload: LoginPayload,
    response: Response,
    repo: SupabaseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
):
    username = payload.username.strip()
    rows = (
        repo.raw_table("admin_users")
        .select("id,username,password_hash,role,active")
        .ilike("username", username)
        .eq("active", True)
        .limit(1)
        .execute()
        .data
        or []
    )
    source = "database"
    role = None
    canonical_username = username
    password_ok = False
    if rows:
        row = rows[0]
        role = row["role"]
        canonical_username = row["username"]
        password_ok = verify_password(row["password_hash"], payload.password)
    else:
        source = "environment"
        username_ok = secrets.compare_digest(username.casefold(), settings.admin_username.strip().casefold())
        password_ok = username_ok and verify_password(settings.admin_password_hash, payload.password)
        if password_ok:
            role = "admin"
            canonical_username = settings.admin_username
    if not password_ok or role not in ADMIN_ROLES:
        raise AppError("Credenciais inválidas.", 401)
    token = sign_admin_session(
        settings.admin_session_secret,
        username=canonical_username,
        role=role,
        source=source,
    )
    _set_admin_cookie(response, token, settings)
    return {"ok": True, "username": canonical_username, "role": role}


@router.post("/logout")
def logout(response: Response, settings: Settings = Depends(get_settings)):
    response.delete_cookie(
        settings.admin_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True}


@router.get("/session")
def session(admin: dict = Depends(current_admin)):
    return admin


@router.get("/overview")
def overview(admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {
        "session": admin,
        "participants": _count(repo, "participants"),
        "questions": _count(repo, "questions"),
        "stations": _count(repo, "qr_points"),
        "trails": _count(repo, "trails"),
        "visits": _count(repo, "station_visits"),
        "manual_actions": _count(repo, "manual_point_actions"),
    }


@router.get("/catalog")
def catalog(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {
        "categories": repo.raw_table("categories").select("id,slug,name,active").order("name").execute().data or [],
        "zones": repo.raw_table("zones").select("id,slug,name,active").order("name").execute().data or [],
        "teams": repo.raw_table("teams").select("id,slug,name,reference_name,description,active").order("name").execute().data or [],
        "blocked_terms": repo.raw_table("blocked_terms").select("id,term,reason,active").order("term").execute().data or [],
    }


@router.get("/questions")
def list_questions(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {
        "questions": repo.raw_table("questions")
        .select("id,prompt,kind,difficulty,active,category_id,accessibility,explanation")
        .order("created_at", desc=True)
        .execute().data or []
    }


@router.post("/questions")
def create_question(
    payload: QuestionPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    data = payload.model_dump()
    issues = validate_accessibility_metadata(data)
    if issues and data["active"]:
        raise AppError("Questão não pode ser ativada: " + " ".join(issues), 422)
    question = repo.insert("questions", data)
    _audit(repo, admin, "question_created", "question", question["id"], prompt=question["prompt"])
    return {"question": question}


@router.post("/questions/{question_id}/toggle")
def toggle_question(
    question_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("questions", id=question_id)
    if not rows:
        raise AppError("Questão não encontrada.", 404)
    if not rows[0]["active"]:
        issues = validate_accessibility_metadata(rows[0])
        if issues:
            raise AppError("Questão não pode ser ativada: " + " ".join(issues), 422)
    active = not rows[0]["active"]
    repo.update("questions", {"active": active}, id=question_id)
    _audit(repo, admin, "question_toggled", "question", question_id, active=active)
    return {"active": active}


@router.get("/participants")
def list_participants(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = (
        repo.raw_table("participants")
        .select("id,full_name,nick,participant_type,registration,course_class,institution,active,is_organizer,team_id,team_revealed_at,activated_at,teams(name,slug)")
        .order("full_name")
        .limit(1000)
        .execute().data or []
    )
    return {"participants": rows}


@router.post("/participants/{participant_id}/organizer")
def set_organizer(
    participant_id: str,
    payload: OrganizerPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    rows = repo.select("participants", id=participant_id)
    if not rows:
        raise AppError("Participante não encontrado.", 404)
    if payload.is_organizer:
        repo.update(
            "participants",
            {"is_organizer": True, "team_id": None, "team_revealed_at": None, "activated_at": None},
            id=participant_id,
        )
    else:
        repo.update("participants", {"is_organizer": False}, id=participant_id)
        repo.rpc("trilhas_assign_team", {"p_participant_id": participant_id})
    _audit(repo, admin, "participant_organizer_changed", "participant", participant_id, is_organizer=payload.is_organizer)
    return {"ok": True, "is_organizer": payload.is_organizer}


@router.get("/stations")
def list_stations(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = (
        repo.raw_table("qr_points")
        .select("id,code,name,zone_id,station_type,base_points,active,active_from,active_until,location_hint,validation_code_hash,zones(name),station_contents(*)")
        .order("created_at")
        .execute().data or []
    )
    for row in rows:
        row["has_physical_code"] = bool(row.pop("validation_code_hash", None))
    return {"stations": rows}


@router.post("/stations")
def create_station(
    payload: StationPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    data = _station_data(payload)
    data.pop("updated_at", None)
    station = repo.insert("qr_points", data)
    _audit(repo, admin, "station_created", "station", station["id"], code=station["code"], station_type=station["station_type"])
    return {"station": station}


@router.put("/stations/{station_id}")
def update_station(
    station_id: str,
    payload: StationPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("qr_points", id=station_id)
    if not rows:
        raise AppError("Estação não encontrada.", 404)
    data = _station_data(payload, keep_hash=rows[0].get("validation_code_hash"))
    updated = repo.update("qr_points", data, id=station_id)
    _audit(repo, admin, "station_updated", "station", station_id, code=data["code"], station_type=data["station_type"])
    return {"station": updated[0] if updated else data}


@router.post("/stations/{station_id}/toggle")
def toggle_station(
    station_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("qr_points", id=station_id)
    if not rows:
        raise AppError("Estação não encontrada.", 404)
    active = not rows[0]["active"]
    repo.update("qr_points", {"active": active}, id=station_id)
    _audit(repo, admin, "station_toggled", "station", station_id, active=active)
    return {"active": active}


@router.put("/stations/{station_id}/content")
def upsert_station_content(
    station_id: str,
    payload: StationContentPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    if not repo.select("qr_points", id=station_id):
        raise AppError("Estação não encontrada.", 404)
    a11y = payload.accessibility or {}
    if payload.media_type == "image" and not a11y.get("alt_text"):
        raise AppError("Imagem essencial precisa de descrição textual equivalente.", 422)
    if payload.media_type in {"audio", "video"} and not a11y.get("transcript"):
        raise AppError("Áudio/vídeo essencial precisa de transcrição ou legenda equivalente.", 422)
    data = payload.model_dump()
    data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    existing = repo.select("station_contents", qr_point_id=station_id)
    if existing:
        rows = repo.update("station_contents", data, qr_point_id=station_id)
        content = rows[0] if rows else {**data, "qr_point_id": station_id}
    else:
        content = repo.insert("station_contents", {"qr_point_id": station_id, **data})
    _audit(repo, admin, "station_content_saved", "station", station_id, title=payload.title)
    return {"content": content}


@router.get("/trails")
def list_trails(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    trails = repo.raw_table("trails").select("*").order("name").execute().data or []
    steps = repo.raw_table("trail_steps").select("trail_id,qr_point_id,step_number,qr_points(code,name)").order("step_number").execute().data or []
    by_trail: dict[str, list] = {}
    for step in steps:
        by_trail.setdefault(step["trail_id"], []).append(step)
    for trail in trails:
        trail["steps"] = by_trail.get(trail["id"], [])
    return {"trails": trails}


@router.post("/trails")
def create_trail(
    payload: TrailPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    trail = repo.insert("trails", payload.model_dump())
    _audit(repo, admin, "trail_created", "trail", trail["id"], name=trail["name"])
    return {"trail": trail}


@router.put("/trails/{trail_id}/steps")
def set_trail_steps(
    trail_id: str,
    payload: TrailStepsPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    if not repo.select("trails", id=trail_id):
        raise AppError("Trilha não encontrada.", 404)
    if len(payload.qr_point_ids) != len(set(payload.qr_point_ids)):
        raise AppError("Uma estação não pode aparecer duas vezes na mesma trilha.", 422)
    for qr_id in payload.qr_point_ids:
        rows = repo.select("qr_points", id=qr_id)
        if not rows:
            raise AppError("Uma das estações informadas não existe.", 422)
        if rows[0].get("station_type") != "sequential":
            repo.update("qr_points", {"station_type": "sequential"}, id=qr_id)
    repo.delete("trail_steps", trail_id=trail_id)
    for number, qr_id in enumerate(payload.qr_point_ids, start=1):
        repo.insert("trail_steps", {"trail_id": trail_id, "qr_point_id": qr_id, "step_number": number})
    _audit(repo, admin, "trail_steps_saved", "trail", trail_id, steps=len(payload.qr_point_ids))
    return {"ok": True, "steps": len(payload.qr_point_ids)}


@router.get("/manual-actions")
def list_manual_actions(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = (
        repo.raw_table("manual_point_actions")
        .select("*,participants(nick,full_name)")
        .order("approved_at", desc=True)
        .limit(500)
        .execute().data or []
    )
    return {"actions": rows}


@router.post("/manual-actions")
def grant_manual_points(
    payload: ManualPointsPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator", "validator")
    if payload.action_type not in ACTION_TYPES:
        raise AppError("Tipo de ação extra inválido.", 422)
    result = repo.rpc(
        "trilhas_admin_grant_manual_points",
        {
            "p_participant_id": payload.participant_id,
            "p_action_type": payload.action_type,
            "p_description": payload.description,
            "p_evidence": payload.evidence,
            "p_points": payload.points,
            "p_actor": admin["username"],
            "p_actor_role": admin["role"],
        },
    )
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível conceder os pontos extras.", 422)
    return result


@router.post("/manual-actions/{action_id}/reverse")
def reverse_manual_points(
    action_id: str,
    payload: ReversePayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator", "validator")
    result = repo.rpc(
        "trilhas_admin_reverse_manual_points",
        {
            "p_action_id": action_id,
            "p_reason": payload.reason,
            "p_actor": admin["username"],
            "p_actor_role": admin["role"],
        },
    )
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível estornar os pontos.", 422)
    return result


@router.get("/audit")
def audit(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.raw_table("audit_log").select("*").order("created_at", desc=True).limit(500).execute().data or []
    return {"events": rows}


@router.get("/users")
def list_admin_users(admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin")
    rows = repo.raw_table("admin_users").select("id,username,role,active,created_at,updated_at").order("username").execute().data or []
    return {"users": rows}


@router.post("/users")
def create_admin_user(
    payload: AdminUserPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    existing = repo.raw_table("admin_users").select("id").ilike("username", payload.username.strip()).limit(1).execute().data or []
    if existing:
        raise AppError("Esse usuário administrativo já existe.", 409)
    user = repo.insert(
        "admin_users",
        {
            "username": payload.username.strip(),
            "password_hash": hash_password(payload.password),
            "role": payload.role,
            "active": True,
        },
    )
    _audit(repo, admin, "admin_user_created", "admin_user", user["id"], username=user["username"], role=user["role"])
    return {"user": {"id": user["id"], "username": user["username"], "role": user["role"], "active": user["active"]}}


@router.post("/users/{user_id}/toggle")
def toggle_admin_user(
    user_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin")
    rows = repo.select("admin_users", id=user_id)
    if not rows:
        raise AppError("Usuário administrativo não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("admin_users", {"active": active, "updated_at": datetime.utcnow().isoformat() + "Z"}, id=user_id)
    _audit(repo, admin, "admin_user_toggled", "admin_user", user_id, active=active)
    return {"active": active}


@router.post("/blocked-terms")
def create_blocked_term(
    payload: BlockedTermPayload,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    item = repo.insert(
        "blocked_terms",
        {"term": payload.term.strip().lower(), "reason": payload.reason, "active": True},
    )
    _audit(repo, admin, "blocked_term_created", "blocked_term", item["id"], term=item["term"])
    return {"blocked_term": item}


@router.post("/blocked-terms/{term_id}/toggle")
def toggle_blocked_term(
    term_id: str,
    admin: dict = Depends(current_admin),
    repo: SupabaseRepository = Depends(get_repo),
):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("blocked_terms", id=term_id)
    if not rows:
        raise AppError("Termo não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("blocked_terms", {"active": active}, id=term_id)
    _audit(repo, admin, "blocked_term_toggled", "blocked_term", term_id, active=active)
    return {"active": active}
