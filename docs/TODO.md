# parser2 — TODO для вертикального среза (стадии 0–4)
Источник: создан, так как `docs/TODO.md` отсутствовал; старый список в `TODO.md` оставлен как архив.

Правило: каждый пункт закрывается проверкой (команда или тест). Без этого статус не меняем.

## 0) База проекта и окружение

0.1 Docker compose поднимает db + redis, api/worker видят код через volumes  
Статус: done  
Проверка: `docker compose up -d db redis api worker`

0.2 Alembic работает, миграции применяются до head внутри контейнера  
Статус: done  
Проверка: `docker compose run --rm api alembic upgrade head`

0.3 self_test не вызывает alembic на хосте  
Статус: done  
Проверка: `rg -n "alembic" scripts/self_test.sh`

0.4 make doctor проверяет Docker и docker compose  
Статус: done  
Проверка: `make doctor`

## 1) Миграции и база (блок А)

1.1 История миграций линейная, reset-db поднимает схему с нуля  
Статус: done  
Проверка: `make reset-db` и `make heads`

1.2 DATABASE_URL читается из env; локально default=localhost, в контейнере host=db  
Статус: done  
Проверка: `docker compose run --rm api python -c "from app.core.config import get_settings; print(get_settings().database_url)"`

1.3 Есть команда `make db-shell`  
Статус: done  
Проверка: `make db-shell`

## 2) JobRun/SyncRun и трассировка прогонов (блок B)

2.1 JobRun хранит job_type/status/started_at/finished_at/updated_at/context/result/error + связи  
Статус: done  
Проверка: `make reset-db` и `docker compose run --rm api python -c "from app.db.models import JobRun"`

2.2 SyncRun создаётся для connection и хранит статусы + result_json  
Статус: done  
Проверка: `curl -sS -X POST http://localhost:8000/api/sync-runs -d ...`

## 3) Синк и MetricSnapshot (блоки C–D)

3.1 Celery worker выполняет run_sync(connection_id, date_from, date_to)  
Статус: done  
Проверка: `make logs-worker` (или `docker compose logs -f worker`)

3.2 После синка создаются metric_snapshots по connection_id  
Статус: done  
Проверка: SQL через `make db-shell`

3.3 Синк идемпотентен (повтор не плодит дубли)  
Статус: done  
Проверка: `pytest -q tests/test_connections_sync.py`

## 4) API и Web (блоки E–F) + минимальные тесты (блок G)

4.1 API: connections/create/list/check, sync-runs/create/get, metrics/get, dashboard/summary (connection_id)  
Статус: done  
Проверка: набор curl-команд (см. лог в конце работы)

4.2 Web: экран connections + sync runs + metrics  
Статус: done  
Проверка: открыть web UI и пройти путь создания/синка/просмотра метрик

4.3 self_test обновлён и есть базовые тесты  
Статус: done  
Проверка: `make selftest` и `docker compose run --rm api pytest -q`

4.4 Dashboard summary включает эффективность (CTR/CPC/CPM/CPA)  
Статус: done  
Проверка: `pytest -q tests/test_dashboard_efficiency.py`

4.5 Connections не возвращают credentials_json, есть credentials_present  
Статус: done  
Проверка: `pytest -q tests/test_credentials_security.py`

4.6 Dashboard summary включает ROAS и может агрегировать по всем connection_id  
Статус: done  
Проверка: `pytest -q tests/test_dashboard_efficiency.py` и `curl -sS /api/dashboard/summary?...`

4.7 Автосинк по расписанию (beat + авто-поля у connections)  
Статус: done  
Проверка: `pytest -q tests/test_auto_sync_scheduler.py`

4.8 Mock-коннектор генерирует стабильные метрики без ключей (yandex mock через credentials_json)  
Статус: done  
Проверка: `pytest -q tests/test_connections_sync.py`

4.9 Запуск sync блокируется при уже running/queued  
Статус: done  
Проверка: `pytest -q tests/test_connections_sync.py`

## 5) Auth + Organizations (стадия 0–1)

5.1 Auth (JWT + refresh + /me)  
Статус: done  
Проверка: `pytest -q tests/test_auth_and_orgs.py`

5.2 Organizations + membership + active org  
Статус: done  
Проверка: `pytest -q tests/test_auth_and_orgs.py`

5.3 Org scoping для connections/sync_runs/job_runs/metrics/dashboard/erir  
Статус: done  
Проверка: `pytest -q tests/test_connections_sync.py` и `pytest -q tests/test_erir_dev.py`

5.4 Org invites + роли + управление участниками  
Статус: done  
Проверка: `pytest -q tests/test_org_invites.py`

5.5 Регистрация создаёт Personal org + membership и выставляет active org  
Статус: done  
Проверка: `pytest -q tests/test_auth_and_orgs.py`

5.6 Email инвайты + resend + наблюдаемость (MailHog)  
Статус: done  
Проверка: `pytest -q tests/test_org_invites.py`

## 5) ЕРИР dev (шаг к стадии 4)

5.1 Dev endpoint /api/erir/dev/register создаёт JobRun + ErirEvent  
Статус: done  
Проверка: `pytest -q tests/test_erir_dev.py`

## Notes

- DATABASE_URL теперь по умолчанию localhost; для контейнеров зафиксирован override в docker-compose.
- SyncRun для connections использует `connection_id`, а `job_run_id` хранится в `params_json`.
- self_test теперь быстро падает с понятным сообщением, если Docker daemon недоступен.
- docker-compose включает web сервис; Makefile `make up` поднимает web вместе с api/worker.
- self_test использует smoke-путь через API и ждёт завершения sync-run по статусу.
- Добавлены connection-level индексы и уникальные ключи для metric_snapshots (campaign/ad_group/ad).
- Web запускается в dev-режиме через Next.js; добавлен Babel-конфиг для стабильного старта без SWC.
- Celery worker слушает `main-queue` и `celery`, а таски явно импортируются.
- Добавлены auth endpoints + membership; UI хранит токен и X-Org-Id.
- Добавлен Celery beat для планового автосинка; connections получили auto_sync_* поля.
- Dashboard summary расширен до ROAS и агрегатов по всем подключениям.
- Регистрация создаёт Personal org и membership, active_org_id выставляется сразу.
- /api/dev/seed создаёт пользователя + две организации + connections в разных org.
- /api/orgs/{org_id}/switch добавлен как alias к activate.
- Dev-коннектор — это stub с детерминированными данными по connection_id + датам.
- Один активный sync на connection обеспечивается проверкой queued/running при создании run.
- active org резолвится через X-Org-Id, иначе берётся active_organization_id, иначе первая membership и сохраняется в user.
- Инвайты: токены хранятся только как sha256, accept требует совпадения email; revoke помечает invite как revoked.
- Роли: owner/admin могут приглашать, только owner меняет роли; последний owner не может уйти или удалить себя.
- Audit log: org_audit_events пишет invite_created/accepted/revoked и member_* события с meta без токенов.
- Invite signup: /api/invites/{token}/preview + регистрация с invite_token, проверка email обязательна.
- Invite flow: preview -> signup with invite_token or login -> /invite/[token] -> accept.
- Инвайты отправляются по email (MailHog), есть resend, поля sent_at/send_count/last_error и audit invite_sent/invite_resent.
- Mock-режим для Yandex включается через `{"mock": true}` или отсутствие token в credentials_json; данные детерминированы по connection_id и датам.
- Добавлен API `/api/connections/{id}/snapshots` для выдачи дневных снапшотов по connection_id.
- Credentials encryption at-rest: wrapper `__enc__` + Fernet keys, data migration и ротация через CLI.

## Next (после MVP)

- Реальные коннекторы: минимальные fetch для Yandex/Ozon/VK (таймауты/429/5xx, ретраи).
- Idempotency ключи и retry-политика для коннекторов (429/5xx).
- Автосинк: доп. ограничения по лимитам и окна, настройка через UI.
- Расширение observability: correlation id для job/sync + structured logs.
- ЕРИР: хранение токенов, повторная отправка событий, отдельный статус-поток.
- Инвайты: шаблоны писем и реальный SMTP/провайдер для prod.
- Роли: аудит изменений и журнал событий.
- Приглашения без регистрации (invite signup).
- Экран ошибок и метрики конверсии invite signup.
- Расширение аудита: добавить события для connections/sync_runs и UI фильтры.
- Structured logs + correlation_id для запросов/sync/jobs.
- Dashboard charts (spend/clicks) и фильтры по платформам.
- Первая реальная площадка: подключить один коннектор с валидным fetch без токенов (через мок-режим).
