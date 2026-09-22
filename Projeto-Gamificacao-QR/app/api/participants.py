from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import current_participant, get_participant_service
from app.core.avatars import DEFAULT_AVATAR_KEY
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.participants import ParticipantService

router = APIRouter(prefix="/api/participants", tags=["participants"])
PIN_PATTERN = r"^\d{4}$"
AVATAR_PATTERN = r"^avatar-(0[1-9]|1[0-2])$"


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    nick: str = Field(min_length=3, max_length=24)
    pin: str = Field(pattern=PIN_PATTERN)
    participant_type: str = Field(pattern="^(student|staff|external)$")
    campus: str | None = Field(default=None, max_length=160)
    course_name: str | None = Field(default=None, max_length=160)
    avatar_key: str = Field(default=DEFAULT_AVATAR_KEY, pattern=AVATAR_PATTERN)


class LoginPayload(BaseModel):
    nick: str = Field(min_length=3, max_length=24)
    pin: str = Field(pattern=PIN_PATTERN)


class RecoverPayload(BaseModel):
    access_code: str = Field(min_length=6, max_length=20)
    new_pin: str = Field(pattern=PIN_PATTERN)


class PinPayload(BaseModel):
    pin: str = Field(pattern=PIN_PATTERN)


class AvatarPayload(BaseModel):
    avatar_key: str = Field(pattern=AVATAR_PATTERN)


def _set_cookie(response: Response, token: str, settings: Settings):
    response.set_cookie(
        key=settings.participant_cookie_name,
        value=token,
        max_age=settings.participant_session_days * 86400,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _public_participant(participant: dict) -> dict:
    return {
        "id": participant["id"],
        "nick": participant["nick"],
        "full_name": participant["full_name"],
        "avatar_key": participant.get("avatar_key") or DEFAULT_AVATAR_KEY,
    }


@router.post("/register")
def register(payload: RegisterPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token, access_code = service.register(payload.model_dump())
    _set_cookie(response, token, settings)
    public = _public_participant(participant)
    public.update({"campus": participant.get("campus"), "course_name": participant.get("course_name")})
    return {"participant": public, "access_code": access_code}


@router.post("/login")
def login(payload: LoginPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token = service.login(payload.nick, payload.pin)
    _set_cookie(response, token, settings)
    return {"participant": _public_participant(participant)}


@router.post("/recover")
def recover(payload: RecoverPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token, new_access_code = service.recover(payload.access_code, payload.new_pin)
    _set_cookie(response, token, settings)
    return {"participant": _public_participant(participant), "access_code": new_access_code}


@router.post("/pin")
def set_pin(payload: PinPayload, participant=Depends(current_participant), service: ParticipantService = Depends(get_participant_service)):
    service.set_pin(participant["id"], payload.pin)
    return {"ok": True}


@router.patch("/avatar")
def update_avatar(payload: AvatarPayload, participant=Depends(current_participant), service: ParticipantService = Depends(get_participant_service)):
    avatar_key = service.update_avatar(participant["id"], payload.avatar_key)
    return {"ok": True, "avatar_key": avatar_key}


@router.post("/logout")
def logout(request: Request, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    token = request.cookies.get(settings.participant_cookie_name)
    service.logout(token)
    response.delete_cookie(key=settings.participant_cookie_name, path="/", secure=settings.session_cookie_secure, httponly=True, samesite="lax")
    return {"ok": True}


@router.get("/me")
def me(request: Request, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    token = request.cookies.get(settings.participant_cookie_name)
    if not token:
        raise AppError("Faça seu cadastro ou entre na sua conta para continuar.", 401)
    state = service.get_home_state_by_session(token)
    participant = state["participant"]
    return {
        "participant": {
            "id": participant["id"],
            "nick": participant["nick"],
            "full_name": participant["full_name"],
            "participant_type": participant["participant_type"],
            "campus": participant.get("campus"),
            "course_name": participant.get("course_name"),
            "avatar_key": participant.get("avatar_key") or DEFAULT_AVATAR_KEY,
            "has_pin": bool(participant.get("has_password")),
            "is_organizer": bool(participant.get("is_organizer")),
        },
        "summary": state["summary"],
    }
