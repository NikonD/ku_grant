# ============================================================
# services/calculator_service.py — логика расчёта вероятности
# Использует sigmoid-функцию и исторические данные из БД
# ============================================================

import math
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.db_models import Specialty, PassingScore
from models.schemas import pick_lang, DEFAULT_LANG, SUPPORTED_LANGS
from logger_config import app_logging

app_logging()
logger = logging.getLogger(__name__)

# Квоты, по которым МНВО РК не публикует отдельную статистику для
# Kozybayev University. Для них используем данные общего конкурса.
# (conscript убран совсем: эти абитуриенты приходят с готовыми сертификатами
#  и попадают в министерский приказ напрямую, к публичному конкурсу не идут.)
QUOTAS_WITHOUT_DATA = {"kazakh_diaspora", "veteran"}

# Минимальные пороги участия в конкурсе грантов МНВО РК (приказ МНВО):
#   педагогические (6B01xxx)       — 75
#   юриспруденция  (6B04201)       — 75
#   медицинские    (6B101xx)       — 70
#   остальные (технические/агро…)  — 50
# Если балл абитуриента ниже порога — он вообще не допускается к конкурсу,
# такие специальности из выдачи отфильтровываются.
THRESHOLD_PED  = 75
THRESHOLD_LAW  = 75
THRESHOLD_MED  = 70
THRESHOLD_OTHER = 50


def eligibility_threshold(code: str) -> int:
    """Минимальный балл ЕНТ для участия в конкурсе грантов по группе ОП."""
    if code.startswith("6B01"):     # 6B01xxx — педагогические
        return THRESHOLD_PED
    if code == "6B04201":           # юриспруденция
        return THRESHOLD_LAW
    if code.startswith("6B101"):    # медицинские (фармация/медицина/стоматология)
        return THRESHOLD_MED
    return THRESHOLD_OTHER


# Крутизна сигмоиды: при ent_score = min_score даёт 50 %,
# +10 баллов от минимума → ~82 %, −10 → ~18 %.
SIGMOID_K = 0.15


def _resolve_lang(lang: Optional[str]) -> str:
    if lang and lang.lower() in SUPPORTED_LANGS:
        return lang.lower()
    return DEFAULT_LANG


def _load_scores(db: Session, specialty_ids: list[int], quota: str) -> dict[int, PassingScore]:
    """Достаёт passing_scores по списку специальностей и одной квоте."""
    rows = (
        db.query(PassingScore)
        .filter(PassingScore.specialty_id.in_(specialty_ids), PassingScore.quota == quota)
        .all()
    )
    return {r.specialty_id: r for r in rows}


def _load_estimates(db: Session, specialty_ids: list[int]) -> dict[int, int]:
    """Оценка проходного балла для программ без данных по нужной квоте и без общего.

    У части ОП (особенно педагогических 6B01xxx) гранты в 2025 распределялись
    только по льготным квотам, поэтому строки общего конкурса в данных нет.
    Чтобы такие программы не пропадали из выдачи, оцениваем порог по максимуму
    из всех доступных квот: общий конкурс по нашим данным в среднем на ~6 баллов
    выше льготных, так что max — разумная (слегка консервативная) оценка.
    Возвращаем {specialty_id: estimated_min_score}.
    """
    rows = (
        db.query(PassingScore)
        .filter(PassingScore.specialty_id.in_(specialty_ids))
        .all()
    )
    estimates: dict[int, int] = {}
    for r in rows:
        if r.min_score is None:
            continue
        cur = estimates.get(r.specialty_id)
        if cur is None or r.min_score > cur:
            estimates[r.specialty_id] = r.min_score
    return estimates


def assessment_chances_list(
    db: Session,
    ent_score: int,
    item_comb: str,
    quota: str,
    lang: Optional[str] = None,
) -> dict:
    lang = _resolve_lang(lang)
    logger.info("assessment_chances_list lang=%s quota=%s item=%r", lang, quota, item_comb)

    specialties = db.query(Specialty).filter(Specialty.item_comb == item_comb).all()
    specialty_ids = [s.id for s in specialties]

    if not specialty_ids:
        return {"assessments": []}

    # Квоты без данных по KU → сразу работаем с общим конкурсом.
    effective_quota = "общий" if quota in QUOTAS_WITHOUT_DATA else quota
    quota_was_substituted = effective_quota != quota

    scores_map = _load_scores(db, specialty_ids, effective_quota)

    # Tier-1 fallback: программа без данных по выбранной квоте → общий конкурс.
    fallback_map: dict[int, PassingScore] = {}
    missing_ids = [sid for sid in specialty_ids if sid not in scores_map]
    if missing_ids and effective_quota != "общий":
        fallback_map = _load_scores(db, missing_ids, "общий")

    # Tier-2 fallback: нет ни выбранной квоты, ни общего конкурса (типично для
    # педагогических ОП) → оцениваем порог по максимуму из доступных квот, чтобы
    # программа всё-таки попала в выдачу (помечаем как fallback ⇒ ∗ на фронте).
    still_missing = [sid for sid in missing_ids if sid not in fallback_map]
    estimate_map: dict[int, int] = _load_estimates(db, still_missing) if still_missing else {}

    results = []
    used_fallback_for_some = False
    excluded_by_threshold = 0

    for spec in specialties:
        # Порог участия в конкурсе грантов МНВО РК — если балла не хватает,
        # абитуриент к этой специальности вообще не допускается, скрываем.
        if ent_score < eligibility_threshold(spec.code):
            excluded_by_threshold += 1
            continue

        score_row = scores_map.get(spec.id) or fallback_map.get(spec.id)
        if score_row is not None and score_row.min_score is not None:
            min_score = score_row.min_score
        else:
            # последний резерв — оценка по доступным квотам
            min_score = estimate_map.get(spec.id)
            if min_score is None:
                continue

        is_fallback = quota_was_substituted or (spec.id not in scores_map)
        if is_fallback:
            used_fallback_for_some = True

        chance = 1 / (1 + math.exp(-SIGMOID_K * (ent_score - min_score)))

        results.append({
            "id":          spec.id,
            "name":        pick_lang(spec.name, lang),
            "code":        spec.code,
            "min_score":   min_score,
            "chance":      round(chance * 100, 2),
            "is_fallback": is_fallback,
        })

    if quota_was_substituted:
        logger.info("Квота %r без данных для KU — расчёт по общему конкурсу", quota)
    if used_fallback_for_some:
        logger.info("Часть программ квоты %r без данных за 2025 — fallback на общий", effective_quota)
    if excluded_by_threshold:
        logger.info("Отфильтровано %d программ — балл ниже порога допуска", excluded_by_threshold)

    return {
        "assessments":            results,
        "excluded_by_threshold":  excluded_by_threshold,
    }
