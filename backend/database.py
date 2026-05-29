# ============================================================
# database.py — подключение к PostgreSQL через SQLAlchemy
# ============================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============================================================
# URL подключения к базе данных
# Берётся из переменной окружения DATABASE_URL
# Если не задана — используется значение по умолчанию
# ============================================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/kozybayev_db_backup"
)

# Создаём движок SQLAlchemy (он управляет соединением с БД)
engine = create_engine(DATABASE_URL)

# Фабрика сессий — каждый запрос получает свою сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# ============================================================
# Dependency (зависимость) для FastAPI
# Используется в роутерах: def endpoint(db: Session = Depends(get_db))
# ============================================================
def get_db():
    db = SessionLocal()
    try:
        yield db        # Отдаём сессию обработчику запроса
    finally:
        db.close()      # Всегда закрываем сессию после запроса