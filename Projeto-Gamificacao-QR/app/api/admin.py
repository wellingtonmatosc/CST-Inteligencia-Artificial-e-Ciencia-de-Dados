"""API administrativa do Trilhas Poéticas.

O navegador nunca acessa o Supabase diretamente. Operações administrativas
passam pelo FastAPI, sessão assinada, validação de papel e auditoria.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

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
ACTION_TYPES = {"recitation", "original_work", "poem_suggestion", "selected_suggestion", "artistic_production", "social_post", "event_participation", "other"}


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class QuestionPayload(BaseModel):
    category_id: str
    kind: str = Field(default="multiple_choice", pattern="^multiple_choice$")
    prompt: str = Field(min_length=5, max_length=2000)
    options: list = Field(min_length=4, max_length=4)
    correct_answer: dict
    explanation: str | None = None
    difficulty: int = Field(default=1, ge=1, le=5)
    media_type: str | None = Field(default=None, pattern="^(image|audio|video)$")
    media_url: str | None = None
    accessibility: dict = Field(default_factory=dict)
    active: bool = True


class StationPayload(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=160)
    zone_id: str
    station_type: str = Field(pattern="^(permanent|sequential|temporary|special)$")
    base_points: int = Field(default=10, ge=10, le=10)
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_admin_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(settings.admin_cookie_name, token, max_age=settings.admin_session_hours * 3600, httponly=True, secure=settings.session_cookie_secure, samesite="lax", path="/")


def _audit(repo: SupabaseRepository, admin: dict, action: str, entity_type: str, entity_id=None, **metadata) -> None:
    repo.insert("audit_log", {"actor_username": admin["username"], "actor_role": admin["role"], "action": action, "entity_type": entity_type, "entity_id": str(entity_id) if entity_id is not None else None, "metadata": metadata})


def _count(repo: SupabaseRepository, table: str) -> int:
    result = repo.raw_table(table).select("id", count="exact").execute()
    return result.count or 0


def _question_rows(repo: SupabaseRepository) -> list[dict]:
    rows = (
        repo.raw_table("questions")
        .select("id,category_id,kind,prompt,options,correct_answer,explanation,difficulty,media_type,media_url,accessibility,active,created_at,updated_at")
        .order("id")
        .execute().data
        or []
    )
    for number, row in enumerate(rows, start=1):
        row["review_code"] = f"Q{number:03d}"
    return rows


def _question_review_code(repo: SupabaseRepository, question_id: str) -> str | None:
    for row in _question_rows(repo):
        if str(row.get("id")) == str(question_id):
            return row["review_code"]
    return None


def _validate_question(payload: QuestionPayload) -> dict:
    data = payload.model_dump()
    options = data["options"]
    values: list[str] = []
    for option in options:
        if not isinstance(option, dict):
            raise AppError("Cada alternativa precisa ter valor e rótulo.", 422)
        value = str(option.get("value") or "").strip()
        label = str(option.get("label") or "").strip()
        if not value or not label:
            raise AppError("As quatro alternativas precisam estar preenchidas.", 422)
        values.append(value)
    if len(set(values)) != 4:
        raise AppError("As quatro alternativas precisam ser diferentes.", 422)
    correct = str((data.get("correct_answer") or {}).get("value") or "").strip()
    if correct not in values:
        raise AppError("A resposta correta precisa ser uma das quatro alternativas.", 422)
    issues = validate_accessibility_metadata(data)
    if issues and data["active"]:
        raise AppError("Questão não pode ser ativada: " + " ".join(issues), 422)
    return data


def _pending_question_visits(repo: SupabaseRepository, question_id: str) -> int:
    result = repo.raw_table("station_visits").select("id", count="exact").eq("question_id", question_id).eq("status", "validated").execute()
    return result.count or 0


def _station_data(payload: StationPayload, *, keep_hash: str | None = None) -> dict:
    if payload.active_from and payload.active_until and payload.active_until <= payload.active_from:
        raise AppError("O fim da janela precisa ser posterior ao início.", 422)
    physical = (payload.physical_code or "").strip().upper()
    return {"code": payload.code.strip().upper(), "name": payload.name.strip(), "zone_id": payload.zone_id, "station_type": payload.station_type, "base_points": 10, "validation_code_hash": sha256_hex(physical) if physical else keep_hash, "active_from": payload.active_from.isoformat() if payload.active_from else None, "active_until": payload.active_until.isoformat() if payload.active_until else None, "location_hint": (payload.location_hint or "").strip() or None, "active": payload.active, "updated_at": _now_iso()}


@router.post("/login")
def login(payload: LoginPayload, response: Response, repo: SupabaseRepository = Depends(get_repo), settings: Settings = Depends(get_settings)):
    username = payload.username.strip()
    rows = repo.raw_table("admin_users").select("id,username,password_hash,role,active").ilike("username", username).eq("active", True).limit(1).execute().data or []
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
    token = sign_admin_session(settings.admin_session_secret, username=canonical_username, role=role, source=source)
    _set_admin_cookie(response, token, settings)
    return {"ok": True, "username": canonical_username, "role": role}


@router.post("/logout")
def logout(response: Response, settings: Settings = Depends(get_settings)):
    response.delete_cookie(settings.admin_cookie_name, path="/", secure=settings.session_cookie_secure, httponly=True, samesite="lax")
    return {"ok": True}


@router.get("/session")
def session(admin: dict = Depends(current_admin)):
    return admin


@router.get("/overview")
def overview(admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"session": admin, "participants": _count(repo, "participants"), "questions": _count(repo, "questions"), "stations": _count(repo, "qr_points"), "trails": _count(repo, "trails"), "visits": _count(repo, "station_visits"), "manual_actions": _count(repo, "manual_point_actions")}


@router.get("/catalog")
def catalog(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"categories": repo.raw_table("categories").select("id,slug,name,active").order("name").execute().data or [], "zones": repo.raw_table("zones").select("id,slug,name,active").order("name").execute().data or [], "blocked_terms": repo.raw_table("blocked_terms").select("id,term,reason,active").order("term").execute().data or []}


@router.get("/questions")
def list_questions(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"questions": _question_rows(repo)}


@router.post("/questions")
def create_question(payload: QuestionPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    if _count(repo, "questions") >= 300:
        raise AppError("O banco homologado já possui 300 questões. Edite ou desative uma questão existente em vez de criar a Q301.", 409)
    data = _validate_question(payload)
    question = repo.insert("questions", data)
    _audit(repo, admin, "question_created", "question", question["id"], prompt=question["prompt"])
    return {"question": question}


@router.put("/questions/{question_id}")
def update_question(question_id: str, payload: QuestionPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("questions", id=question_id)
    if not rows:
        raise AppError("Questão não encontrada.", 404)
    if _pending_question_visits(repo, question_id) > 0:
        raise AppError("Há participante com esta questão em andamento. Aguarde a conclusão antes de editar.", 409)
    data = _validate_question(payload)
    data["updated_at"] = _now_iso()
    updated = repo.update("questions", data, id=question_id)
    review_code = _question_review_code(repo, question_id)
    _audit(repo, admin, "question_updated", "question", question_id, review_code=review_code, prompt=data["prompt"], active=data["active"])
    return {"question": updated[0] if updated else {"id": question_id, **data}, "review_code": review_code}


@router.post("/questions/{question_id}/toggle")
def toggle_question(question_id: str, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("questions", id=question_id)
    if not rows:
        raise AppError("Questão não encontrada.", 404)
    row = rows[0]
    if row.get("kind") != "multiple_choice":
        raise AppError("A versão final aceita apenas questões de múltipla escolha.", 422)
    active = not row["active"]
    if not active and _pending_question_visits(repo, question_id) > 0:
        raise AppError("Há participante com esta questão em andamento. Aguarde a conclusão antes de desativar.", 409)
    if active:
        payload = QuestionPayload(**row)
        _validate_question(payload)
    repo.update("questions", {"active": active, "updated_at": _now_iso()}, id=question_id)
    review_code = _question_review_code(repo, question_id)
    _audit(repo, admin, "question_toggled", "question", question_id, review_code=review_code, active=active)
    return {"active": active, "review_code": review_code}


@router.get("/participants")
def list_participants(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.raw_table("participants").select("id,full_name,nick,participant_type,campus,course_name,avatar_key,active,is_organizer,created_at").order("full_name").limit(1000).execute().data or []
    return {"participants": rows}


@router.post("/participants/{participant_id}/organizer")
def set_organizer(participant_id: str, payload: OrganizerPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin")
    if not repo.select("participants", id=participant_id):
        raise AppError("Participante não encontrado.", 404)
    repo.update("participants", {"is_organizer": payload.is_organizer, "updated_at": _now_iso()}, id=participant_id)
    _audit(repo, admin, "participant_organizer_changed", "participant", participant_id, is_organizer=payload.is_organizer)
    return {"ok": True, "is_organizer": payload.is_organizer}


@router.get("/stations")
def list_stations(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.raw_table("qr_points").select("id,code,name,zone_id,station_type,base_points,active,active_from,active_until,location_hint,validation_code_hash,zones(name)").order("code").execute().data or []
    for row in rows:
        row["has_physical_code"] = bool(row.pop("validation_code_hash", None))
    return {"stations": rows}


@router.post("/stations")
def create_station(payload: StationPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    if _count(repo, "qr_points") >= 15:
        raise AppError("O evento utiliza exatamente 15 QRs. Edite um QR existente em vez de criar um QR adicional.", 409)
    data = _station_data(payload)
    data.pop("updated_at", None)
    station = repo.insert("qr_points", data)
    _audit(repo, admin, "station_created", "station", station["id"], code=station["code"], station_type=station["station_type"])
    return {"station": station}


@router.put("/stations/{station_id}")
def update_station(station_id: str, payload: StationPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("qr_points", id=station_id)
    if not rows:
        raise AppError("QR não encontrado.", 404)
    data = _station_data(payload, keep_hash=rows[0].get("validation_code_hash"))
    data["station_type"] = "permanent"
    data["base_points"] = 10
    data["active_from"] = None
    data["active_until"] = None
    updated = repo.update("qr_points", data, id=station_id)
    _audit(repo, admin, "station_updated", "station", station_id, code=data["code"], active=data["active"], location_hint=data["location_hint"])
    return {"station": updated[0] if updated else data}


@router.post("/stations/{station_id}/toggle")
def toggle_station(station_id: str, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("qr_points", id=station_id)
    if not rows:
        raise AppError("QR não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("qr_points", {"active": active, "updated_at": _now_iso()}, id=station_id)
    _audit(repo, admin, "station_toggled", "station", station_id, code=rows[0].get("code"), active=active)
    return {"active": active}


@router.put("/stations/{station_id}/content")
def upsert_station_content(station_id: str, payload: StationContentPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    if not repo.select("qr_points", id=station_id):
        raise AppError("Estação não encontrada.", 404)
    a11y = payload.accessibility or {}
    if payload.media_type == "image" and not a11y.get("alt_text"):
        raise AppError("Imagem essencial precisa de descrição textual equivalente.", 422)
    if payload.media_type in {"audio", "video"} and not a11y.get("transcript"):
        raise AppError("Áudio/vídeo essencial precisa de transcrição ou legenda equivalente.", 422)
    data = payload.model_dump()
    data["updated_at"] = _now_iso()
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
def create_trail(payload: TrailPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    trail = repo.insert("trails", payload.model_dump())
    _audit(repo, admin, "trail_created", "trail", trail["id"], name=trail["name"])
    return {"trail": trail}


@router.put("/trails/{trail_id}/steps")
def set_trail_steps(trail_id: str, payload: TrailStepsPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
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
            repo.update("qr_points", {"station_type": "sequential", "updated_at": _now_iso()}, id=qr_id)
    repo.delete("trail_steps", trail_id=trail_id)
    for number, qr_id in enumerate(payload.qr_point_ids, start=1):
        repo.insert("trail_steps", {"trail_id": trail_id, "qr_point_id": qr_id, "step_number": number})
    _audit(repo, admin, "trail_steps_saved", "trail", trail_id, steps=len(payload.qr_point_ids))
    return {"ok": True, "steps": len(payload.qr_point_ids)}


@router.get("/manual-actions")
def list_manual_actions(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.raw_table("manual_point_actions").select("*,participants(nick,full_name)").order("approved_at", desc=True).limit(500).execute().data or []
    return {"actions": rows}


@router.post("/manual-actions")
def grant_manual_points(payload: ManualPointsPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator", "validator")
    if payload.action_type not in ACTION_TYPES:
        raise AppError("Tipo de ação extra inválido.", 422)
    result = repo.rpc("trilhas_admin_grant_manual_points", {"p_participant_id": payload.participant_id, "p_action_type": payload.action_type, "p_description": payload.description, "p_evidence": payload.evidence, "p_points": payload.points, "p_actor": admin["username"], "p_actor_role": admin["role"]})
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível registrar a correção de pontos.", 422)
    return result


@router.post("/manual-actions/{action_id}/reverse")
def reverse_manual_points(action_id: str, payload: ReversePayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator", "validator")
    result = repo.rpc("trilhas_admin_reverse_manual_points", {"p_action_id": action_id, "p_reason": payload.reason, "p_actor": admin["username"], "p_actor_role": admin["role"]})
    if not isinstance(result, dict) or not result.get("ok"):
        raise AppError("Não foi possível estornar os pontos.", 422)
    return result


@router.get("/audit")
def audit(_: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.raw_table("audit_log").select("*").order("created_at", desc=True).limit(500).execute().data or []
    participants = {str(x["id"]): x.get("nick") or x.get("full_name") for x in (repo.raw_table("participants").select("id,nick,full_name").execute().data or [])}
    stations = {str(x["id"]): x.get("code") for x in (repo.raw_table("qr_points").select("id,code").execute().data or [])}
    questions = {str(x["id"]): x.get("review_code") for x in _question_rows(repo)}
    for row in rows:
        entity_id = str(row.get("entity_id") or "")
        entity_type = row.get("entity_type")
        if entity_type == "question":
            row["entity_label"] = questions.get(entity_id) or (row.get("metadata") or {}).get("review_code") or entity_id
        elif entity_type in {"station", "qr_point"}:
            row["entity_label"] = stations.get(entity_id) or entity_id
        elif entity_type == "participant":
            row["entity_label"] = participants.get(entity_id) or entity_id
        elif entity_type in {"event", "event_control"}:
            row["entity_label"] = "Evento"
        elif entity_type == "manual_point_action":
            row["entity_label"] = "Correção de pontuação"
    return {"events": rows}


@router.get("/users")
def list_admin_users(admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin")
    rows = repo.raw_table("admin_users").select("id,username,role,active,created_at,updated_at").order("username").execute().data or []
    return {"users": rows}


@router.post("/users")
def create_admin_user(payload: AdminUserPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin")
    existing = repo.raw_table("admin_users").select("id").ilike("username", payload.username.strip()).limit(1).execute().data or []
    if existing:
        raise AppError("Esse usuário administrativo já existe.", 409)
    user = repo.insert("admin_users", {"username": payload.username.strip(), "password_hash": hash_password(payload.password), "role": payload.role, "active": True})
    _audit(repo, admin, "admin_user_created", "admin_user", user["id"], username=user["username"], role=user["role"])
    return {"user": {"id": user["id"], "username": user["username"], "role": user["role"], "active": user["active"]}}


@router.post("/users/{user_id}/toggle")
def toggle_admin_user(user_id: str, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin")
    rows = repo.select("admin_users", id=user_id)
    if not rows:
        raise AppError("Usuário administrativo não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("admin_users", {"active": active, "updated_at": _now_iso()}, id=user_id)
    _audit(repo, admin, "admin_user_toggled", "admin_user", user_id, active=active)
    return {"active": active}


@router.post("/blocked-terms")
def create_blocked_term(payload: BlockedTermPayload, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    item = repo.insert("blocked_terms", {"term": payload.term.strip().lower(), "reason": payload.reason, "active": True})
    _audit(repo, admin, "blocked_term_created", "blocked_term", item["id"], term=item["term"])
    return {"blocked_term": item}


@router.post("/blocked-terms/{term_id}/toggle")
def toggle_blocked_term(term_id: str, admin: dict = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    require_admin_role(admin, "admin", "operator")
    rows = repo.select("blocked_terms", id=term_id)
    if not rows:
        raise AppError("Termo não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("blocked_terms", {"active": active}, id=term_id)
    _audit(repo, admin, "blocked_term_toggled", "blocked_term", term_id, active=active)
    return {"active": active}
