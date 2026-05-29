# routers/chat.py — API эндпоинт чат-бота

from database import get_db
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.chat_service import get_chat_response
from logger_config import app_logging
from fastapi import Depends , APIRouter
from sqlalchemy.orm import Session
import logging
app_logging()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db : Session = Depends(get_db)
):
    logger.info("Запрос чат-бота")
    logger.info("Отправка по схеме ChatRequest")
    """
    Отправляет сообщение AI-ассистенту и получает ответ.
    
    Принимает:
        - message:   текущее сообщение пользователя
        - history:   история предыдущих сообщений
        - ent_score: балл ЕНТ (опционально, для более точных советов)
    
    Возвращает:
        - reply: ответ AI-ассистента
        - role:  "assistant"
    """
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    
    try:
        # Получаем ответ от Groq API
        logger.info("Обращение за API Groq")
        reply = get_chat_response(
            message=request.message,
            history=request.history,
            ent_score=request.ent_score,
            db=db
        )
        logger.info("Получение ответа на эндпоинт по схеме ChatResponce")
        return ChatResponse(reply=reply, role="assistant")
    
    except Exception as e:
        # Обрабатываем ошибки API
        raise HTTPException(
            status_code=503,
            detail=f"Ошибка AI-сервиса: {str(e)}"
        )