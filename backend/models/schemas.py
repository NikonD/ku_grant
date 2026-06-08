# ============================================================
# models/schemas.py — Pydantic схемы (валидация данных API)
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


# Поддерживаемые языки. fallback всегда RU (исходный язык данных).
Lang = Literal["ru", "kk", "en"]
SUPPORTED_LANGS: tuple[str, ...] = ("ru", "kk", "en")
DEFAULT_LANG: str = "ru"


def pick_lang(value, lang: str) -> str:
    """Достать строку из JSONB-словаря {lang: text} с fallback на RU.

    Терпимо относится к строкам (если кто-то ещё не перевёл — возвращает как есть)
    и к пустым словарям.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if lang in value and value[lang]:
            return value[lang]
        if DEFAULT_LANG in value and value[DEFAULT_LANG]:
            return value[DEFAULT_LANG]
        # вернём что-нибудь, чтобы не падать
        for v in value.values():
            if v:
                return v
    return ""


# ============================================================
# Схемы для специальностей
# ============================================================

class SpecialtySchema(BaseModel):
    """Специальность (без проходных баллов)."""
    id:          int
    group_code:  str
    name:        str
    code:        str
    item_comb:   Optional[str] = None  # каноническая (RU) — иногда нужна фронту
    item_comb_display: str = ""        # отображаемая на выбранном языке
    description: str
    price_paid:  int

    class Config:
        from_attributes = True


class SpecialtyShortSchema(BaseModel):
    """Краткая инфа о специальности (для выпадающего списка)."""
    id:                 int
    code:               str
    name:               str
    item_comb:          Optional[str] = None
    item_comb_display:  str = ""

    class Config:
        from_attributes = True


# ============================================================
# Схемы для калькулятора
# ============================================================

class AssessmentChanceRequest(BaseModel):
    ent_score: int = Field(..., ge=0, le=140, description="Балл ЕНТ")
    item_comb: str = Field(..., description="Каноническая (RU) комбинация предметов")
    quota:     str = Field(description="Квота")
    lang:      Optional[Lang] = Field(default=None, description="Язык ответа")


class AssessmentItem(BaseModel):
    id:          int
    name:        str
    code:        Optional[str] = None
    min_score:   int
    chance:      float
    is_fallback: bool = False


class AssessmentChanceResponse(BaseModel):
    assessments: List[AssessmentItem]
    # Сколько специальностей скрыто из-за порога допуска МНВО РК
    excluded_by_threshold: int = 0


# ============================================================
# Схемы для чат-бота
# ============================================================

class ChatMessage(BaseModel):
    role:    str
    content: str


class ChatRequest(BaseModel):
    message:   str
    history:   List[ChatMessage] = []
    ent_score: Optional[int] = None
    lang:      Optional[Lang] = None


class ChatResponse(BaseModel):
    reply: str
    role:  str = "assistant"
