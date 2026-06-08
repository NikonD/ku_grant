# ============================================================
# routers/calculator.py — API эндпоинт калькулятора вероятности
# ============================================================

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import AssessmentChanceRequest, AssessmentChanceResponse
from services.calculator_service import assessment_chances_list
from logger_config import app_logging

router = APIRouter()
app_logging()
logger = logging.getLogger(__name__)


@router.post("/assessment", response_model=AssessmentChanceResponse)
def assessment_chance(
    request: AssessmentChanceRequest,
    lang: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Расчёт шансов поступления.

    Язык можно передать как query (?lang=kk) или в теле запроса (поле lang).
    """
    effective_lang = request.lang or lang
    logger.info("Запрос оценки шанса, lang=%s", effective_lang)
    return assessment_chances_list(
        db=db,
        ent_score=request.ent_score,
        item_comb=request.item_comb,
        quota=request.quota,
        lang=effective_lang,
    )
