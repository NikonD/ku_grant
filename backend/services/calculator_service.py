# ============================================================
# services/calculator_service.py — логика расчёта вероятности
# Использует sigmoid-функцию и исторические данные из БД
# ============================================================

import math
import logging
from sqlalchemy.orm import Session
from models.db_models import Specialty, PassingScore
from logger_config import app_logging

app_logging()
logger = logging.getLogger(__name__)

# Квоты, по которым МНВО РК не публикует отдельную статистику для
# Kozybayev University. Для них используем данные общего конкурса.
QUOTAS_WITHOUT_DATA = {"kazakh_diaspora", "conscript", "veteran"}

# Крутизна сигмоиды: при ent_score = min_score даёт 50 %,
# +10 баллов от минимума → ~82 %, −10 → ~18 %.
SIGMOID_K = 0.15


def _load_scores(db: Session, specialty_ids: list[int], quota: str) -> dict[int, PassingScore]:
    """Достаёт passing_scores по списку специальностей и одной квоте."""
    rows = (
        db.query(PassingScore)
        .filter(PassingScore.specialty_id.in_(specialty_ids), PassingScore.quota == quota)
        .all()
    )
    return {r.specialty_id: r for r in rows}


def assessment_chances_list(
    db: Session,
    ent_score: int,
    item_comb: str,
    quota: str,
) -> dict:
    logger.info("Вызвана функция assessment_chances_list")

    specialties = db.query(Specialty).filter(Specialty.item_comb == item_comb).all()
    specialty_ids = [s.id for s in specialties]

    if not specialty_ids:
        return {"assessments": []}

    # Для квот, по которым МНВО не публикует данные по KU,
    # сразу работаем с общим конкурсом и помечаем результат как ориентировочный.
    effective_quota = "общий" if quota in QUOTAS_WITHOUT_DATA else quota
    quota_was_substituted = effective_quota != quota

    scores_map = _load_scores(db, specialty_ids, effective_quota)

    # Fallback: если для запрошенной квоты в конкретной программе нет
    # данных за прошлый год — используем общий конкурс. Это случается,
    # когда в группе в 2025 г. вообще не было заявок по этой квоте.
    fallback_map: dict[int, PassingScore] = {}
    missing_ids = [sid for sid in specialty_ids if sid not in scores_map]
    if missing_ids and effective_quota != "общий":
        fallback_map = _load_scores(db, missing_ids, "общий")

    results = []
    used_fallback_for_some = False

    for spec in specialties:
        score_row = scores_map.get(spec.id) or fallback_map.get(spec.id)
        if score_row is None or score_row.min_score is None:
            # По этой программе нет данных ни по выбранной квоте,
            # ни по общему конкурсу — пропускаем (в 2025 г. грантов не было)
            continue

        # Помечаем результат как fallback в двух случаях:
        # 1) квота вообще без отдельных данных по KU (veteran/conscript/kazakh_diaspora)
        # 2) по этой конкретной программе для запрошенной квоты нет данных,
        #    подставили общий конкурс
        is_fallback = quota_was_substituted or (spec.id not in scores_map)
        if is_fallback:
            used_fallback_for_some = True

        min_score = score_row.min_score
        grants_count = score_row.enrolled or 0

        # Чистая сигмоида от разницы (ent_score − min_score).
        # Раньше был ещё competition_weight на основе applicants/enrolled,
        # но applicants — выдуманные данные, поэтому формулу упростили.
        chance = 1 / (1 + math.exp(-SIGMOID_K * (ent_score - min_score)))

        results.append({
            "id":                  spec.id,
            "name":                spec.name,
            "min_score":           min_score,
            "current_enrolled":    grants_count,
            "current_applicants":  0,
            "chance":              round(chance * 100, 2),
            "is_fallback":         is_fallback,
        })

    if quota_was_substituted:
        logger.info(
            "Квота %r не имеет отдельных данных для KU — расчёт по общему конкурсу",
            quota,
        )
    if used_fallback_for_some:
        logger.info(
            "Часть программ по квоте %r без данных за 2025 — fallback на общий конкурс",
            effective_quota,
        )

    return {"assessments": results}
