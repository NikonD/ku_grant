-- ============================================================
-- База данных AI-Ассистента абитуриента
-- Университет Козыбаева, Казахстан
--
-- ВНИМАНИЕ: этот файл содержит ТОЛЬКО структуру таблиц.
-- Данные больше НЕ хранятся здесь — они лежат в:
--   /database/data/specialties.json
--   /database/data/passing_scores.json
--
-- Заполнение пустой БД:
--   python scripts/restore.py
-- Выгрузка текущих данных:
--   python scripts/dump.py
-- ============================================================

-- ============================================================
-- ТАБЛИЦА: Специальности
--
-- Локализованные поля хранятся как JSONB вида:
--   {"ru": "Педагогика", "kk": "Педагогика", "en": "Pedagogy"}
-- Канонический ключ item_comb остаётся обычной строкой на русском —
-- по нему идёт точный лукап в калькуляторе и из чат-бота.
-- ============================================================
CREATE TABLE IF NOT EXISTS specialties (
    id                SERIAL PRIMARY KEY,
    group_code        VARCHAR(20)  NOT NULL,
    code              VARCHAR(200) NOT NULL UNIQUE,
    item_comb         VARCHAR(100),                  -- канонический ключ (русский)
    item_comb_i18n    JSONB        NOT NULL DEFAULT '{}'::jsonb, -- отображение по языкам
    name              JSONB        NOT NULL,         -- {"ru": "...", "kk": "...", "en": "..."}
    description       JSONB        NOT NULL DEFAULT '{}'::jsonb,
    price_paid        INTEGER,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ТАБЛИЦА: Проходные баллы
-- ============================================================
CREATE TABLE IF NOT EXISTS passing_scores (
    id           SERIAL PRIMARY KEY,
    specialty_id INTEGER REFERENCES specialties(id) ON DELETE CASCADE,
    min_score    INTEGER NOT NULL,
    quota        VARCHAR(50) NOT NULL,
    applicants   INTEGER DEFAULT 0,
    enrolled     INTEGER DEFAULT 0
);

-- ============================================================
-- ТАБЛИЦА: Пользователи
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    ent_score  INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ТАБЛИЦА: История расчётов
-- ============================================================
CREATE TABLE IF NOT EXISTS calculation_history (
    id           SERIAL PRIMARY KEY,
    session_id   VARCHAR(100),
    specialty_id INTEGER REFERENCES specialties(id),
    quota        VARCHAR(50),
    ent_score    INTEGER,
    probability  FLOAT,
    created_at   TIMESTAMP DEFAULT NOW()
);

-- Индексы для частых лукапов
CREATE INDEX IF NOT EXISTS idx_specialties_item_comb  ON specialties (item_comb);
CREATE INDEX IF NOT EXISTS idx_specialties_group_code ON specialties (group_code);
CREATE INDEX IF NOT EXISTS idx_scores_specialty_quota ON passing_scores (specialty_id, quota);
