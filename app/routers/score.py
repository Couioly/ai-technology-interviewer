from fastapi import APIRouter

from app.schemas import ScoreRequest, ScoreCard
from app.services.score_service import make_score_card

router = APIRouter(prefix="/api", tags=["score"])


@router.post("/score", response_model=ScoreCard)
def score(req: ScoreRequest):
    return make_score_card(req.question, req.answer)