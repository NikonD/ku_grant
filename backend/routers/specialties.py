# ============================================================
# routers/specialties.py — API эндпоинты для специальностей
# ============================================================

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Specialty
from models.schemas import (
    SpecialtySchema,
    SpecialtyShortSchema,
    SUPPORTED_LANGS,
    DEFAULT_LANG,
    pick_lang,
)
from logger_config import app_logging

router = APIRouter()
app_logging()
logger = logging.getLogger(__name__)


def _resolve_lang(lang: Optional[str]) -> str:
    """Нормализует входной язык: приводит к нижнему регистру, фильтрует."""
    if lang and lang.lower() in SUPPORTED_LANGS:
        return lang.lower()
    return DEFAULT_LANG


def _to_short(spec: Specialty, lang: str) -> dict:
    return {
        "id":                spec.id,
        "code":              spec.code,
        "name":              pick_lang(spec.name, lang),
        "item_comb":         spec.item_comb,
        "item_comb_display": pick_lang(spec.item_comb_i18n, lang) or (spec.item_comb or ""),
    }


def _to_full(spec: Specialty, lang: str) -> dict:
    return {
        "id":                spec.id,
        "group_code":        spec.group_code,
        "code":              spec.code,
        "name":              pick_lang(spec.name, lang),
        "item_comb":         spec.item_comb,
        "item_comb_display": pick_lang(spec.item_comb_i18n, lang) or (spec.item_comb or ""),
        "description":       pick_lang(spec.description, lang),
        "price_paid":        spec.price_paid or 0,
    }


@router.get("/", response_model=List[SpecialtyShortSchema])
def get_all_specialties(
    lang: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Список всех специальностей (кратко) на выбранном языке."""
    lang = _resolve_lang(lang)
    logger.info("Запрос всех специальностей, lang=%s", lang)
    specialties = db.query(Specialty).all()
    payload = [_to_short(s, lang) for s in specialties]
    payload.sort(key=lambda r: r["name"])
    return payload


@router.get("/{specialty_id}", response_model=SpecialtySchema)
def get_specialty(
    specialty_id: int,
    lang: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Полная инфа о специальности."""
    lang = _resolve_lang(lang)
    logger.info("Запрос специальности id=%s, lang=%s", specialty_id, lang)
    specialty = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    if not specialty:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    return _to_full(specialty, lang)


@router.get("/faculty/{item_comb}", response_model=List[SpecialtyShortSchema])
def get_by_item(
    item_comb: str,
    lang: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Список специальностей по канонической комбинации предметов (RU)."""
    lang = _resolve_lang(lang)
    logger.info("Запрос специальностей по item_comb=%r, lang=%s", item_comb, lang)
    specialties = (
        db.query(Specialty)
        .filter(Specialty.item_comb.ilike(f"%{item_comb}%"))
        .all()
    )
    return [_to_short(s, lang) for s in specialties]
