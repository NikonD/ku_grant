#!/usr/bin/env bash
#
# scripts/restore.sh — восстановление БД PostgreSQL из SQL-дампа.
#
# Использование:
#   ./scripts/restore.sh                       # из dumps/latest/<db>.sql
#   ./scripts/restore.sh dumps/2026-06-08_15-58-13
#   ./scripts/restore.sh path/to/file.sql
#
# Что делает:
#   1) Завершает активные подключения к БД (иначе DROP не пройдёт)
#   2) Накатывает SQL-файл (если дамп сделан с --clean, он сам сделает DROP/CREATE)
#
# Переменные окружения (с дефолтами под docker-compose этого проекта):
#   DB_CONTAINER  — имя docker-контейнера postgres (по умолчанию ku_grant-db-1)
#   DB_USER       — пользователь                  (postgres)
#   DB_NAME       — имя БД                        (kozybayev_db_backup)
#   DB_PASSWORD   — пароль                        (postgres)
#

set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-ku_grant-db-1}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-kozybayev_db_backup}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$REPO_ROOT/dumps/latest}"

# Резолвим путь: если папка — берём $DB_NAME.sql внутри, иначе считаем что это файл.
if [ -d "$TARGET" ]; then
    SQL_FILE="$TARGET/$DB_NAME.sql"
elif [ -f "$TARGET" ]; then
    SQL_FILE="$TARGET"
else
    echo "[restore] не найдено: $TARGET" >&2
    echo "Доступные снимки:" >&2
    ls -1 "$REPO_ROOT/dumps" 2>/dev/null | sed 's/^/  /' >&2 || true
    exit 1
fi

if [ ! -f "$SQL_FILE" ]; then
    echo "[restore] нет SQL-файла: $SQL_FILE" >&2
    exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
    echo "[restore] контейнер '$DB_CONTAINER' не запущен. Поднимите его:  docker-compose up -d db" >&2
    exit 1
fi

SIZE=$(du -h "$SQL_FILE" | awk '{print $1}')
echo "[restore] $(date '+%Y-%m-%d %H:%M:%S')"
echo "[restore] контейнер=$DB_CONTAINER  БД=$DB_NAME"
echo "[restore] источник: $SQL_FILE  ($SIZE)"

# 1) Закрываем активные подключения, чтобы DROP в дампе прошёл без EXCEPTION'ов.
docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    psql -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -q -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
       WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();" >/dev/null

# 2) Накатываем дамп. ON_ERROR_STOP=1 — упасть на первой ошибке.
#    Дамп с --clean --if-exists содержит DROP TABLE и пересоздаёт схему.
docker exec -i -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 --quiet < "$SQL_FILE"

# Sanity: посчитаем сколько таблиц и записей в основных таблицах.
SUMMARY=$(docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -At -F' | ' -c "
        SELECT 'specialties     '       , count(*)::text FROM specialties
        UNION ALL SELECT 'passing_scores  ', count(*)::text FROM passing_scores;
    " 2>/dev/null || true)

echo "[restore] Готово."
if [ -n "$SUMMARY" ]; then
    echo "$SUMMARY" | sed 's/^/  /'
fi
