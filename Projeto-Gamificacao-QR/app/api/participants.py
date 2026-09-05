from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from app.api.deps import current_participant, get_participant_service, get_gamification_service
from app.core.config import Settings, get_settings
from app.services.participants import ParticipantService
from app.services.gamification import GamificationService

router = APIRouter(prefix="/api/participants", tags=["participants"])


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    nick: str = Field(min_length=3, max_length=24)
    participant_type: str = Field(pattern="^(student|staff|external)$")
    registration: str | None = Field(default=None, max_length=50)
    course_class: str | None = Field(default=None, max_length=120)
    institution: str | None = Field(default=None, max_length=160)


class RecoverPayload(BaseModel):
    access_code: str = Field(min_length=6, max_length=20)


def _set_cookie(response: Response, token: str, settings: Settings):
    response.set_cookie(
        key=settings.participant_cookie_name, value=token,
        max_age=settings.participant_session_days * 86400,
        httponly=True, secure=settings.session_cookie_secure,
        samesite="lax", path="/",
    )


@router.post("/register")
def register(payload: RegisterPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token, access_code = service.register(payload.model_dump())
    _set_cookie(response, token, settings)
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"]}, "access_code": access_code}


@router.post("/recover")
def recover(payload: RecoverPayload, response: Response, service: ParticipantService = Depends(get_participant_service), settings: Settings = Depends(get_settings)):
    participant, token = service.recover(payload.access_code)
    _set_cookie(response, token, settings)
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"]}}


@router.get("/me")
def me(participant=Depends(current_participant), game: GamificationService = Depends(get_gamification_service)):
    return {"participant": {"id": participant["id"], "nick": participant["nick"], "full_name": participant["full_name"], "participant_type": participant["participant_type"]}, "summary": game.participant_summary(participant["id"])}
