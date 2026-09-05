from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from app.api.deps import current_admin, get_repo
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import sign_admin_session, verify_password
from app.repositories.supabase_repo import SupabaseRepository
from app.services.questions import validate_accessibility_metadata

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginPayload(BaseModel):
    password: str


class QuestionPayload(BaseModel):
    category_id: str
    kind: str = Field(pattern="^(multiple_choice|true_false|short_text|association|ordering)$")
    prompt: str = Field(min_length=5, max_length=2000)
    options: list = Field(default_factory=list)
    correct_answer: dict
    explanation: str | None = None
    difficulty: int = Field(default=1, ge=1, le=5)
    media_type: str | None = Field(default=None, pattern="^(image|audio|video)$")
    media_url: str | None = None
    accessibility: dict
    active: bool = True


class QrPayload(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=160)
    zone_id: str
    kind: str = Field(pattern="^(normal|daily_bonus|dynamic_bonus)$")
    active: bool = True


@router.post("/login")
def login(payload: LoginPayload, response: Response, settings: Settings = Depends(get_settings)):
    if not verify_password(settings.admin_password_hash, payload.password):
        raise AppError("Credenciais inválidas.", 401)
    token = sign_admin_session(settings.admin_session_secret)
    response.set_cookie(settings.admin_cookie_name, token, max_age=settings.admin_session_hours * 3600, httponly=True, secure=settings.session_cookie_secure, samesite="lax", path="/")
    return {"ok": True}


@router.get("/overview")
def overview(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    participants = repo.raw_table("participants").select("id", count="exact").execute()
    questions = repo.raw_table("questions").select("id", count="exact").execute()
    qrs = repo.raw_table("qr_points").select("id", count="exact").execute()
    attempts = repo.raw_table("attempts").select("id,correct").execute().data or []
    return {"participants": participants.count or 0, "questions": questions.count or 0, "qr_points": qrs.count or 0, "attempts": len(attempts), "correct_attempts": sum(1 for a in attempts if a.get("correct"))}


@router.get("/questions")
def list_questions(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"questions": repo.raw_table("questions").select("id,prompt,kind,difficulty,active,category_id").order("created_at", desc=True).execute().data or []}


@router.post("/questions")
def create_question(payload: QuestionPayload, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    data = payload.model_dump()
    issues = validate_accessibility_metadata(data)
    if issues and data["active"]:
        raise AppError("Questão não pode ser ativada: " + " ".join(issues), 422)
    return {"question": repo.insert("questions", data)}


@router.get("/qrs")
def list_qrs(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"qrs": repo.raw_table("qr_points").select("*,zones(name)").order("created_at").execute().data or []}


@router.post("/qrs")
def create_qr(payload: QrPayload, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"qr": repo.insert("qr_points", payload.model_dump())}


@router.post("/qrs/{qr_id}/toggle")
def toggle_qr(qr_id: str, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.select("qr_points", id=qr_id)
    if not rows:
        raise AppError("QR não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("qr_points", {"active": active}, id=qr_id)
    return {"active": active}


@router.get("/catalog")
def catalog(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"categories": repo.raw_table("categories").select("id,slug,name,active").order("name").execute().data or [], "zones": repo.raw_table("zones").select("id,slug,name,active").order("name").execute().data or [], "blocked_terms": repo.raw_table("blocked_terms").select("id,term,reason,active").order("term").execute().data or []}


class BlockedTermPayload(BaseModel):
    term: str = Field(min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=200)


@router.post("/blocked-terms")
def create_blocked_term(payload: BlockedTermPayload, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    return {"blocked_term": repo.insert("blocked_terms", {"term": payload.term.strip().lower(), "reason": payload.reason, "active": True})}


@router.post("/blocked-terms/{term_id}/toggle")
def toggle_blocked_term(term_id: str, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.select("blocked_terms", id=term_id)
    if not rows:
        raise AppError("Termo não encontrado.", 404)
    active = not rows[0]["active"]
    repo.update("blocked_terms", {"active": active}, id=term_id)
    return {"active": active}


@router.post("/questions/{question_id}/toggle")
def toggle_question(question_id: str, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    rows = repo.select("questions", id=question_id)
    if not rows:
        raise AppError("Questão não encontrada.", 404)
    if not rows[0]["active"]:
        issues = validate_accessibility_metadata(rows[0])
        if issues:
            raise AppError("Questão não pode ser ativada: " + " ".join(issues), 422)
    active = not rows[0]["active"]
    repo.update("questions", {"active": active}, id=question_id)
    return {"active": active}


@router.post("/qrs/{qr_id}/questions/{question_id}")
def link_question(qr_id: str, question_id: str, _: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    if not repo.select("qr_points", id=qr_id):
        raise AppError("QR não encontrado.", 404)
    if not repo.select("questions", id=question_id):
        raise AppError("Questão não encontrada.", 404)
    if repo.select("qr_question_pool", qr_point_id=qr_id, question_id=question_id):
        return {"ok": True, "already_linked": True}
    repo.insert("qr_question_pool", {"qr_point_id": qr_id, "question_id": question_id})
    return {"ok": True, "already_linked": False}


@router.get("/bonus")
def list_bonus(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    campaigns = repo.raw_table("bonus_campaigns").select("*").order("event_date", desc=True).execute().data or []
    locations = repo.raw_table("bonus_locations").select("*,qr_points(code,name),zones(name)").order("starts_at", desc=True).execute().data or []
    return {"campaigns": campaigns, "locations": locations}


@router.get("/analytics")
def analytics(_: bool = Depends(current_admin), repo: SupabaseRepository = Depends(get_repo)):
    participants = repo.raw_table("participants").select("participant_type").execute().data or []
    questions = repo.raw_table("questions").select("id,category_id").execute().data or []
    categories = {row["id"]: row["name"] for row in repo.raw_table("categories").select("id,name").execute().data or []}
    attempts = repo.raw_table("attempts").select("question_id,correct,answered_at").execute().data or []
    question_categories = {question["id"]: question["category_id"] for question in questions}
    by_type: dict[str, int] = {}
    for row in participants:
        participant_type = row["participant_type"]
        by_type[participant_type] = by_type.get(participant_type, 0) + 1
    by_category: dict[str, dict[str, int]] = {}
    by_hour: dict[str, int] = {}
    for attempt in attempts:
        category = categories.get(question_categories.get(attempt["question_id"]), "Sem categoria")
        item = by_category.setdefault(category, {"attempts": 0, "correct": 0})
        item["attempts"] += 1
        item["correct"] += int(bool(attempt["correct"]))
        hour = (attempt.get("answered_at") or "")[11:13]
        if hour:
            by_hour[hour] = by_hour.get(hour, 0) + 1
    return {"participants_by_type": by_type, "questions_by_category": by_category, "attempts_by_hour": by_hour}
