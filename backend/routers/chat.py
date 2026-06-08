# ============================================================
# routers/chat.py — API эндпоинт чат-бота
# ============================================================

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import ChatRequest, ChatResponse
from services.chat_service import get_chat_response
from logger_config import app_logging

app_logging()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    lang: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Отправляет сообщение AI-ассистенту и получает ответ.

    Язык можно передать как query (?lang=kk) или в теле (поле lang).
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    effective_lang = request.lang or lang
    logger.info("Запрос чат-бота, lang=%s", effective_lang)

    try:
        reply = get_chat_response(
            message=request.message,
            history=request.history,
            ent_score=request.ent_score,
            db=db,
            lang=effective_lang,
        )
        return ChatResponse(reply=reply, role="assistant")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ошибка AI-сервиса: {str(e)}")
