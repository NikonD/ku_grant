#!/usr/bin/env python3
"""
scripts/dump.py — выгрузить данные из PostgreSQL в JSON-файлы.

Использование:
    DATABASE_URL=postgresql://postgres:postgres@localhost:5433/kozybayev_db_backup \
        python scripts/dump.py

Если DATABASE_URL не задана, используется значение по умолчанию из docker-compose
(localhost:5433). Файлы записываются в database/data/.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 не установлен. Запустите:  pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "database" / "data"

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5433/kozybayev_db_backup"


def _connect() -> psycopg2.extensions.connection:
    dsn = os.getenv("DATABASE_URL", DEFAULT_DSN)
    print(f"[dump] Подключение к {dsn}")
    return psycopg2.connect(dsn)


def dump_specialties(conn) -> list[dict]:
    """Выгружает все специальности с localized JSONB-полями."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT group_code, code, item_comb, item_comb_i18n,
                   name, description, price_paid
            FROM specialties
            ORDER BY group_code, code
            """
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def dump_passing_scores(conn) -> list[dict]:
    """Выгружает проходные баллы, привязывая их к коду специальности (а не id),
    чтобы файл был стабилен между restore."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT s.code AS specialty_code,
                   ps.quota, ps.min_score, ps.applicants, ps.enrolled
            FROM passing_scores ps
            JOIN specialties s ON s.id = ps.specialty_id
            ORDER BY s.group_code, s.code, ps.quota
            """
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=False)
        fh.write("\n")
    print(f"[dump]   {path.relative_to(REPO_ROOT)}  ({len(payload)} записей)")


def main() -> None:
    conn = _connect()
    try:
        specialties = dump_specialties(conn)
        scores = dump_passing_scores(conn)
    finally:
        conn.close()

    _write_json(DATA_DIR / "specialties.json", specialties)
    _write_json(DATA_DIR / "passing_scores.json", scores)
    print("[dump] Готово.")


if __name__ == "__main__":
    main()
