#!/usr/bin/env python3
"""
scripts/restore.py — залить данные из JSON-файлов в PostgreSQL.

Использование:
    DATABASE_URL=postgresql://postgres:postgres@localhost:5433/kozybayev_db_backup \
        python scripts/restore.py

По умолчанию выполняет TRUNCATE специальностей и проходных баллов перед
загрузкой, чтобы получить идемпотентный результат. Передайте --append чтобы
дописать без очистки.

Структура файлов лежит в database/data/. См. dump.py для обратной операции.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import Json, execute_values
except ImportError:
    print("psycopg2 не установлен. Запустите:  pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "database" / "data"

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5433/kozybayev_db_backup"


def _connect() -> psycopg2.extensions.connection:
    dsn = os.getenv("DATABASE_URL", DEFAULT_DSN)
    print(f"[restore] Подключение к {dsn}")
    return psycopg2.connect(dsn)


def _load(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл данных: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"{path} должен быть JSON-массивом")
    return data


def _truncate(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE passing_scores, specialties RESTART IDENTITY CASCADE")
    print("[restore] passing_scores + specialties очищены")


def insert_specialties(conn, rows: list[dict]) -> dict[str, int]:
    """Вставляет специальности и возвращает map code → id."""
    values = [
        (
            r["group_code"],
            r["code"],
            r.get("item_comb"),
            Json(r.get("item_comb_i18n") or {}),
            Json(r["name"]),
            Json(r.get("description") or {}),
            r.get("price_paid"),
        )
        for r in rows
    ]
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO specialties
                (group_code, code, item_comb, item_comb_i18n,
                 name, description, price_paid)
            VALUES %s
            RETURNING id, code
            """,
            values,
        )
        returned = cur.fetchall()
    code_to_id = {code: pk for pk, code in returned}
    print(f"[restore] specialties: вставлено {len(returned)}")
    return code_to_id


def insert_passing_scores(conn, rows: list[dict], code_to_id: dict[str, int]) -> None:
    values = []
    skipped = 0
    for r in rows:
        sid = code_to_id.get(r["specialty_code"])
        if sid is None:
            skipped += 1
            continue
        values.append(
            (
                sid,
                r["min_score"],
                r["quota"],
                r.get("applicants", 0) or 0,
                r.get("enrolled", 0) or 0,
            )
        )
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO passing_scores
                (specialty_id, min_score, quota, applicants, enrolled)
            VALUES %s
            """,
            values,
        )
    print(f"[restore] passing_scores: вставлено {len(values)}"
          + (f", пропущено {skipped} (нет такой специальности)" if skipped else ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore DB from JSON")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Не делать TRUNCATE — просто вставить (могут быть конфликты по code)",
    )
    args = parser.parse_args()

    specialties = _load("specialties.json")
    scores = _load("passing_scores.json")

    conn = _connect()
    try:
        if not args.append:
            _truncate(conn)
        code_to_id = insert_specialties(conn, specialties)
        insert_passing_scores(conn, scores, code_to_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print("[restore] Готово.")


if __name__ == "__main__":
    main()
