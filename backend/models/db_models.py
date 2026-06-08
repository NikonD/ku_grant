# ============================================================
# models/db_models.py — SQLAlchemy модели (таблицы БД)
# ============================================================

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Specialty(Base):
    """Специальность. Текстовые поля локализованы через JSONB."""
    __tablename__ = "specialties"

    id              = Column(Integer, primary_key=True, index=True)
    group_code      = Column(String(20),  nullable=False)
    code            = Column(String(200), nullable=False, unique=True)
    item_comb       = Column(String(100))                          # канонический ключ (RU)
    item_comb_i18n  = Column(JSONB, nullable=False, default=dict)  # {"ru":..,"kk":..,"en":..}
    name            = Column(JSONB, nullable=False)
    description     = Column(JSONB, nullable=False, default=dict)
    price_paid      = Column(Integer)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    passing_scores = relationship("PassingScore", back_populates="specialty")


class PassingScore(Base):
    """Проходной балл по специальности за конкретный год."""
    __tablename__ = "passing_scores"

    id           = Column(Integer, primary_key=True, index=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    min_score    = Column(Integer, nullable=False)
    quota        = Column(String(50), nullable=False)
    applicants   = Column(Integer, default=0)
    enrolled     = Column(Integer, default=0)

    specialty = relationship("Specialty", back_populates="passing_scores")


class CalculationHistory(Base):
    """История расчётов для аналитики"""
    __tablename__ = "calculation_history"

    id           = Column(Integer, primary_key=True, index=True)
    session_id   = Column(String(100))
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    quota        = Column(String(50))
    ent_score    = Column(Integer)
    probability  = Column(Float)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
