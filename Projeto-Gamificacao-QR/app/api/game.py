from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import current_participant, get_trilhas_service
from app.services.trilhas import TrilhasService

router = APIRouter(prefix="/api", tags=["trilhas-poeticas"])


class ValidateStationPayload(BaseModel):
    physical_code: str | None = Field(default=None, max_length=80)


class AnswerPayload(BaseModel):
    answer: object


@router.get("/q/{code}")
def station(code: str, participant=Depends(current_participant), game: TrilhasService = Depends(get_trilhas_service)):
    return game.get_station(participant["id"], code)


@router.post("/station/{code}/validate")
def validate_station(code: str, payload: ValidateStationPayload, participant=Depends(current_participant), game: TrilhasService = Depends(get_trilhas_service)):
    return game.validate_station(participant["id"], code, payload.physical_code)


@router.post("/station/{code}/answer")
def answer_station(code: str, payload: AnswerPayload, participant=Depends(current_participant), game: TrilhasService = Depends(get_trilhas_service)):
    return game.answer_challenge(participant["id"], code, payload.answer)


@router.get("/ranking")
def ranking(game: TrilhasService = Depends(get_trilhas_service)):
    return {"ranking": game.ranking(), "ranking_type": "teams"}
