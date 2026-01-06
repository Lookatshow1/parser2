# parser2 — TODO для вертикального среза (стадии 0–4)
Источник: создан, так как `docs/TODO.md` отсутствовал; старый список в `TODO.md` оставлен как архив.

Правило: каждый пункт закрывается проверкой (команда или тест). Без этого статус не меняем.

## 0) База проекта и окружение

0.1 Docker compose поднимает db + redis, api/worker видят код через volumes  
Статус: next  
Проверка: `docker compose up -d db redis api worker`

0.2 Alembic работает, миграции применяются до head внутри контейнера  
Статус: next  
Проверка: `docker compose run --rm api alembic upgrade head`

0.3 self_test не вызывает alembic на хосте  
Статус: done  
Проверка: `rg -n "alembic" scripts/self_test.sh`

## 1) Миграции и база (блок А)

1.1 История миграций линейная, reset-db поднимает схему с нуля  
Статус: next  
Проверка: `make reset-db` и `make heads`

1.2 DATABASE_URL читается из env; локально default=localhost, в контейнере host=db  
Статус: next  
Проверка: `docker compose run --rm api python -c "from app.core.config import get_settings; print(get_settings().database_url)"`

1.3 Есть команда `make db-shell`  
Статус: next  
Проверка: `make db-shell`

## 2) JobRun/SyncRun и трассировка прогонов (блок B)

2.1 JobRun хранит job_type/status/started_at/finished_at/updated_at/context/result/error + связи  
Статус: next  
Проверка: `make reset-db` и `docker compose run --rm api python -c "from app.db.models import JobRun"`

2.2 SyncRun создаётся для connection и хранит статусы + result_json  
Статус: next  
Проверка: `curl -sS -X POST http://localhost:8000/api/sync-runs -d ...`

## 3) Синк и MetricSnapshot (блоки C–D)

3.1 Celery worker выполняет run_sync(connection_id, date_from, date_to)  
Статус: next  
Проверка: `make logs-worker` (или `docker compose logs -f worker`)

3.2 После синка создаются metric_snapshots по connection_id  
Статус: next  
Проверка: SQL через `make db-shell`

## 4) API и Web (блоки E–F) + минимальные тесты (блок G)

4.1 API: connections/create/list/check, sync-runs/create/get, metrics/get, dashboard/summary (connection_id)  
Статус: next  
Проверка: набор curl-команд (см. лог в конце работы)

4.2 Web: экран connections + sync runs + metrics  
Статус: next  
Проверка: открыть web UI и пройти путь создания/синка/просмотра метрик

4.3 self_test обновлён и есть базовые тесты  
Статус: next  
Проверка: `make selftest` и `docker compose run --rm api pytest -q`

## Notes

- DATABASE_URL теперь по умолчанию localhost; для контейнеров зафиксирован override в docker-compose.
- SyncRun для connections использует `connection_id`, а `job_run_id` хранится в `params_json`.
- Проверки с docker compose сейчас блокируются зависанием команд (`docker compose run --rm api alembic ...`); требуется повторить на рабочем Docker.
- self_test теперь быстро падает с понятным сообщением, если Docker daemon недоступен.
