# ============================================================
# services/calculator_service.py — логика расчёта вероятности
# Использует sigmoid-функцию и исторические данные из БД
# ============================================================

import math
import logging
from typing import Optional
from sqlalchemy.orm import Session
from models.db_models import Specialty, PassingScore 
from logger_config import app_logging

app_logging()
logger = logging.getLogger(__name__)

def assessment_chances_list(
    db : Session,
    ent_score : int,
    item_comb : str,
    quota : str
) -> dict: # Создание функций 
    logger.info("Вызвана функция assessment_chances_list") # Логирование консоли
    
    Specialties_list_item = db.query(Specialty).filter(Specialty.item_comb == item_comb).all()
    # Запрашивание БД для сверки комбинаций предметов и достать специальности
    logger.info("Запрошена информация по БД : assessment_chances_list")

    score_item_ids = [s.id for s in Specialties_list_item] # Парсинг строк на id ключей этих специальностей

    item_scores = db.query(PassingScore).filter(PassingScore.specialty_id.in_(score_item_ids) , PassingScore.quota == quota).all()  
    # Запрашивание другой таблицы с баллами через внешний ключ специальностей чтобы получить баллы по нужным специальностям

    scores_map = {item.specialty_id : item for item in item_scores}
    # создаем переменную чтобы не терять баллы и их id
    
    results = [] # Создаем массив для помещение конечных результатов
    k = 0.15
    for spec in Specialties_list_item:
        current_id = scores_map.get(spec.id)
        if current_id is None:
            continue
        current_min_score = current_id.min_score
        current_enrolled = current_id.enrolled
        current_applicants = current_id.applicants

        if current_min_score is None:
            continue
        logger.info(f"Расчет шансов на специальность {spec.name}")
        
    
        sigmoid_chance = 1 / (1 + math.exp(-k * (ent_score - current_min_score)))
        competition_ratio = current_enrolled / current_applicants if current_applicants > 0 else 1 
        competition_weight = math.pow(competition_ratio , 0.1)
        final_chance = sigmoid_chance * competition_weight

        results.append({
            "id" : spec.id,
            "name" : spec.name,
            "min_score" : current_min_score,
            "current_enrolled" : current_enrolled,
            "current_applicants" : current_applicants,
            "chance" : round(final_chance * 100 , 2)
        })
        logger.info("Отправление ответа по AssessmentChanceResponse")
    return {"assessments" : results}
    



