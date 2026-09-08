from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import current_participant, get_participant_service
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.participants import ParticipantService

router = APIRouter(prefix="/api/participants", tags=["participants"])
PIN_PATTERN = r"^\d{4}$"


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    nick: str = Field(min_length=3, max_length=24)
    pin: str = Field(pattern=PIN_PATTERN)
    participant_type: str = Field(pattern="^(student|staff|external)$")
    registration: str | None = Field(default=None, max_length=50)
    course_class: str | None = Field(default=None, max_length=120)
    institution: str | None = Field(default=None, max_length=160)


class LoginPayload(BaseModel):
    nick: str = Field(min_length=3, max_length=24)
    pin: str = Field(pattern=PIN_PATTERN)


class RecoverPayload(BaseModel):
    access_code: str = Field(min_length=6, max_length=20)
    new_pin: str = Field(pattern=PIN_PATTERN)


class PinPayload(BaseModel):
    pin: str = Field(pattern=PIN_PATTERN)


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


@router.post("/register")
def register(payload: RegisterPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token, access_code = service.register(payload.model_dump())
    _set_cookie(response, token, settings)
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"]}, "access_code": access_code}


@router.post("/login")
def login(payload: LoginPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token = service.login(payload.nick, payload.pin)
    _set_cookie(response, token, settings)
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"]}}


@router.post("/recover")
def recover(payload: RecoverPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token, new_access_code = service.recover(payload.access_code, payload.new_pin)
    _set_cookie(response, token, settings)
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"]}, "access_code": new_access_code}


@router.post("/pin")
def set_pin(payload: PinPayload, participant=Depends(current_participant), service: ParticipantService = Depends(get_participant_service)):
    service.set_pin(participant["id"], payload.pin)
    return {"ok": True}


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
        raise AppError("Faça seu cadastro ou recupere sua sessão para continuar.", 401)
    state = service.get_home_state_by_session(token)
    participant = state["participant"]
    return {
        "participant": {
            "id": participant["id"],
            "nick": participant["nick"],
            "full_name": participant["full_name"],
            "participant_type": participant["participant_type"],
            "has_pin": bool(participant.get("has_password")),
            "is_organizer": bool(participant.get("is_organizer")),
        },
        "summary": state["summary"],
    }
