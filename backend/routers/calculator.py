# ============================================================
# routers/calculator.py — API эндпоинт калькулятора вероятности
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import logging
from database import get_db
from models.schemas import AssessmentChanceRequest , AssessmentChanceResponse
from services.calculator_service import assessment_chances_list 
from logger_config import app_logging
router = APIRouter()

app_logging()
logger = logging.getLogger(__name__)


@router.post("/assessment" , response_model=AssessmentChanceResponse)
def assessment_chance(request : AssessmentChanceRequest, db : Session = Depends(get_db)):
    logger.info("Запрос оценки шанса")
    logger.info("Отправка по AssessmentChanceRequest")
    # Проверяем квоту
    logger.info("Образещение к calculator_service по assessment_chances_list")
    chances_result = assessment_chances_list(
        db=db,
        ent_score=request.ent_score,
        item_comb=request.item_comb,
        quota=request.quota
    )
    logger.info("Получение результата по эндпоинту calculator")
    return chances_result
