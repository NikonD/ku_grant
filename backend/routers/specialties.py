
# routers/specialties.py — API эндпоинты для специальностей


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from models.db_models import Specialty
from models.schemas import SpecialtySchema, SpecialtyShortSchema
from logger_config import app_logging
router = APIRouter()
app_logging()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[SpecialtyShortSchema])
def get_all_specialties(db: Session = Depends(get_db)):
    logger.info("Запрос всех специальностей")
    """
    Возвращает список всех специальностей (кратко).
    Используется для заполнения выпадающего списка на фронтенде.
    """
    logger.info("Отправка модели запроса Specialty")
    specialties = db.query(Specialty).order_by(Specialty.name).all()
    logger.info("Получение результата и отправка списком по схеме SpecialtyShortSchema")
    return specialties


@router.get("/{specialty_id}", response_model=SpecialtySchema)
def get_specialty(specialty_id: int, db: Session = Depends(get_db)):
    logger.info("Запрос конкретной специальности по ID")
    """
    Возвращает полную информацию о специальности включая проходные баллы.
    """
    logger.info("Отправка модели запроса Specialty")
    specialty = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    
    if not specialty:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    logger.info("Получение результата по эндпоинту и отправка по схеме SpecialtySchema")
    return specialty


@router.get("/faculty/{item_comb}", response_model=List[SpecialtyShortSchema])
def get_by_item(item_comb: str, db: Session = Depends(get_db)):
    logger.info("Запрос специальностей по предмету")
    """
    Возвращает список специальностей предмета.
    """
    logger.info("Отправка модели запроса Specialty")
    specialties = (
        db.query(Specialty)
        .filter(Specialty.item_comb.ilike(f"%{item_comb}%"))
        .all()
    )
    logger.info("Получение результата по эндпоинту и отправка по схеме SpecialtyShortSchema")
    parsed_by_item = [SpecialtyShortSchema.model_validate(s).model_dump() for s in specialties]
    logger.info(f"Пропарсено {len(parsed_by_item)}")
    return parsed_by_item 