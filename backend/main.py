# ============================================================
# main.py — точка входа FastAPI приложения
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Импортируем роутеры (каждый отвечает за свой раздел API)
from routers import specialties, calculator, chat

# Создаём приложение
app = FastAPI(
    title="AI-Ассистент абитуриента — Козыбаев",
    description="API для расчёта вероятности гранта и AI-консультации",
    version="1.0.0"
)

# ============================================================
# CORS — разрешаем запросы с фронтенда (React на порту 5173)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Подключаем роутеры с префиксами
# ============================================================
app.include_router(specialties.router, prefix="/api/specialties", tags=["Специальности"])
app.include_router(calculator.router, prefix="/api/calculator",  tags=["Калькулятор"])
app.include_router(chat.router,       prefix="/api/chat",        tags=["Чат-бот"])

# Главная страница (проверка что сервер работает)
@app.get("/")
def root():
    return {"status": "ok", "message": "AI-Ассистент абитуриента Козыбаева работает!"}

# ============================================================
# Запуск (только при прямом запуске файла, не через uvicorn)
# ============================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)