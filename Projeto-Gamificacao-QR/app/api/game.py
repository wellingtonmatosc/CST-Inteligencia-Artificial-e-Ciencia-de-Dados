from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.deps import current_participant, get_gamification_service
from app.services.gamification import GamificationService

router = APIRouter(prefix="/api", tags=["game"])


class AnswerPayload(BaseModel):
    answer: object


class CategoryPayload(BaseModel):
    category_id: str


@router.get("/q/{code}")
def scan(code: str, participant=Depends(current_participant), game: GamificationService = Depends(get_gamification_service)):
    return game.get_qr(participant["id"], code)


@router.post("/activity/{run_id}/answer")
def answer_activity(run_id: str, payload: AnswerPayload, participant=Depends(current_participant), game: GamificationService = Depends(get_gamification_service)):
    return game.answer_normal(participant["id"], run_id, payload.answer)


@router.post("/bonus/{bonus_run_id}/category")
def choose_bonus_category(bonus_run_id: str, payload: CategoryPayload, participant=Depends(current_participant), game: GamificationService = Depends(get_gamification_service)):
    return game.choose_bonus_category(participant["id"], bonus_run_id, payload.category_id)


@router.post("/bonus/{bonus_run_id}/answer")
def answer_bonus(bonus_run_id: str, payload: AnswerPayload, participant=Depends(current_participant), game: GamificationService = Depends(get_gamification_service)):
    return game.answer_bonus(participant["id"], bonus_run_id, payload.answer)


@router.get("/ranking")
def ranking(game: GamificationService = Depends(get_gamification_service)):
    return {"ranking": game.ranking()}
