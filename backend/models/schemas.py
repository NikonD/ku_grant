# ============================================================
# models/schemas.py — Pydantic схемы (валидация данных API)
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List

# ============================================================
# Схемы для специальностей
# ============================================================

class PassingScoreSchema(BaseModel):
    """Проходной балл за год"""
    year:        int
    quota:       str
    min_score:   int
    applicants:  int
    enrolled:    int

    class Config:
        from_attributes = True   # Позволяет создавать из SQLAlchemy объектов


class SpecialtySchema(BaseModel):
    """Специальность с проходными баллами"""
    id:           int
    group_code:   str
    name:         str
    code:         str
    item_comb:    Optional[str]
    description:  str
    price_paid:   int
    

    class Config:
        from_attributes = True


class SpecialtyShortSchema(BaseModel):
    """Краткая информация о специальности (для выпадающего списка)"""
    id:   int
    code: str
    name: str
    item_comb : str

    class Config:
        from_attributes = True


# ============================================================
# Схемы для калькулятора
# ============================================================

class AssessmentChanceRequest(BaseModel):
    ent_score : int = Field(..., ge=0 ,le=140, description = "Балл ЕНТ") 
    item_comb : str = Field(..., description = "Комбинация предметов")
    quota : str = Field(description="Квота и привилегий")

class AssessmentItem(BaseModel):
    id: int
    name: str
    min_score: int
    chance: float
    # True — если по этой программе для выбранной квоты данных нет,
    # и расчёт сделан по общему конкурсу (фронт покажет пометку).
    is_fallback: bool = False

class AssessmentChanceResponse(BaseModel):
    assessments : List[AssessmentItem]
# ============================================================
# Схемы для чат-бота
# ============================================================

class ChatMessage(BaseModel):
    """Одно сообщение в истории чата"""
    role:    str   # "user" или "assistant"
    content: str

class ChatRequest(BaseModel):
    """Запрос к чат-боту"""
    message:   str                          # Текущее сообщение пользователя
    history:   List[ChatMessage] = []       # История предыдущих сообщений
    ent_score: Optional[int] = None         # Балл ЕНТ (если пользователь указал)

class ChatResponse(BaseModel):
    """Ответ чат-бота"""
    reply:   str   # Ответ от AI
    role:    str = "assistant"