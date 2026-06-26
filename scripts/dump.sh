#!/usr/bin/env bash
#
# scripts/dump.sh — снимок БД PostgreSQL в dumps/<timestamp>/.
#
# Пишет два файла:
#   <db>.sql        — полный дамп (схема + данные, с DROP IF EXISTS)
#   <db>__data.sql  — только данные с column-inserts (читаемо, диффабельно)
#
# Использование:
#   ./scripts/dump.sh                    # снимок текущей БД
#   DB_CONTAINER=other-db ./scripts/dump.sh
#
# Переменные окружения (с дефолтами под docker-compose этого проекта):
#   DB_CONTAINER  — имя docker-контейнера postgres (по умолчанию определяется
#                   автоматически: docker compose service "db", иначе известные
#                   имена ku_grant_db / ku_grant-db-1)
#   DB_USER       — пользователь                  (postgres)
#   DB_NAME       — имя БД                        (kozybayev_db_backup)
#   DB_PASSWORD   — пароль                        (postgres)
#

set -euo pipefail

DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-kozybayev_db_backup}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y-%m-%d_%H-%M-%S)"
OUT="$REPO_ROOT/dumps/$TS"

# Имя/ID контейнера postgres. Имя зависит от окружения (локально ku_grant-db-1,
# на сервере с override — ku_grant_db), поэтому определяем автоматически.
# Явное значение DB_CONTAINER имеет приоритет.
resolve_db_container() {
    if [ -n "${DB_CONTAINER:-}" ]; then
        echo "$DB_CONTAINER"; return
    fi
    local cid
    cid="$(docker compose -f "$REPO_ROOT/docker-compose.yml" ps -q db 2>/dev/null | head -n1)"
    if [ -n "$cid" ]; then echo "$cid"; return; fi
    local name
    for name in ku_grant_db ku_grant-db-1 ku-grant-db-1; do
        if docker ps --format '{{.Names}}' | grep -qx "$name"; then
            echo "$name"; return
        fi
    done
    echo ""
}

DB_CONTAINER="$(resolve_db_container)"

if [ -z "$DB_CONTAINER" ] || \
   [ "$(docker inspect -f '{{.State.Running}}' "$DB_CONTAINER" 2>/dev/null)" != "true" ]; then
    echo "[dump] не найден запущенный контейнер postgres." >&2
    echo "       Проверьте 'docker ps' или укажите вручную:  DB_CONTAINER=<имя> $0" >&2
    exit 1
fi

mkdir -p "$OUT"

echo "[dump] $(date '+%Y-%m-%d %H:%M:%S')"
echo "[dump] контейнер=$DB_CONTAINER  БД=$DB_NAME  ->  $OUT"

# 1) Полный дамп со встроенным DROP — restore.sh применит его как есть.
docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges --clean --if-exists \
    > "$OUT/$DB_NAME.sql"

# 2) Data-only, по одному INSERT на строку — удобно для git-diff и ручных правок.
docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges --data-only --column-inserts \
    > "$OUT/${DB_NAME}__data.sql"

# Симлинк на последний снимок
ln -sfn "$TS" "$REPO_ROOT/dumps/latest"

SP=$(grep -c '^CREATE TABLE'  "$OUT/$DB_NAME.sql" || true)
INS=$(grep -c '^INSERT INTO' "$OUT/${DB_NAME}__data.sql" || true)
SIZE_FULL=$(du -h "$OUT/$DB_NAME.sql"        | awk '{print $1}')
SIZE_DATA=$(du -h "$OUT/${DB_NAME}__data.sql" | awk '{print $1}')

echo "[dump] $DB_NAME.sql           $SIZE_FULL  ($SP таблиц)"
echo "[dump] ${DB_NAME}__data.sql   $SIZE_DATA  ($INS INSERT-ов)"
echo "[dump] latest -> dumps/$TS"
