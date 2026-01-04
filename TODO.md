# parser2 — TODO и статусы
Актуально на: 2026-01-04  
Правило: каждый пункт закрывается проверкой (команда или тест). Без этого статус не меняем.

## 0) База проекта и окружение

0.1 Docker compose поднимает db + redis  
Статус: done  
Проверка: `docker compose up -d db redis`

0.2 Alembic работает, миграции применяются до head  
Статус: done  
Проверка: `alembic upgrade head`

0.3 Dev seed и базовые ручки живы  
Статус: done  
Проверка:
- `curl -sS -X POST "http://localhost:8000/api/dev/seed" | python3 -m json.tool`
- `curl -sS "http://localhost:8000/api/plans" | python3 -m json.tool`

## 1) Тестовая инфраструктура (Postgres, без SQLite)

1.1 pytest использует Postgres из docker compose, dependency override на get_db  
Статус: done  
Проверка: `pytest -q` (внутри `./scripts/self_test.sh`)

1.2 Удалены SQLite engine и Base.metadata.create_all из тестов  
Статус: done  
Проверка: поиск по репо: `sqlite`, `create_all(`, `Base.metadata.create_all`

## 2) Модели и миграции домена экспериментов

2.1 ExperimentCampaign модель + таблица experiment_campaigns (campaign_external_id, platform, FK)  
Статус: done  
Проверка: `alembic upgrade head` и `pytest -q`

## 3) Трекинг фоновых задач (job_runs)

3.1 Модель JobRun + миграция job_runs (JSONB поля, индексы, updated_at авто-обновление)  
Статус: done  
Проверка: `alembic upgrade head`, затем `psql` и `\d job_runs`

3.2 Сервис job_runs: sanitize_payload + create/mark_running/mark_succeeded/mark_failed (внутри commit)  
Статус: done  
Проверка: unit/API тест ниже + ручной вызов demo

3.3 API /api/jobs: список и карточка по id  
Статус: done  
Проверка:
- `curl -sS "http://localhost:8000/api/jobs?limit=5" | python3 -m json.tool`
- `curl -sS "http://localhost:8000/api/jobs/1" | python3 -m json.tool` (если есть id)

3.4 Dev endpoint POST /api/dev/jobs/demo (полный цикл queued→running→succeeded)  
Статус: done  
Проверка: `curl -sS -X POST "http://localhost:8000/api/dev/jobs/demo" | python3 -m json.tool`

3.5 Тест jobs API  
Статус: done  
Проверка: `pytest -q tests/test_jobs_api.py`

## 4) Самопроверка репозитория

4.1 scripts/self_test.sh поднимает db/redis → alembic upgrade head → pytest -q  
Статус: done  
Проверка: `./scripts/self_test.sh`

4.2 self_test.sh исполняемый и это зафиксировано в git  
Статус: next  
Проверка:
- `chmod +x scripts/self_test.sh`
- `git update-index --chmod=+x scripts/self_test.sh`
- `git status` должен показать изменения
- `git commit -m "Make self_test.sh executable"`

## 5) Шаг 8. Healthcheck уровня продакшена

5.1 Обновить GET /api/health: проверка Postgres и ревизии alembic  
Статус: next  
Суть ответа:
- `status`: ok/degraded (HTTP всегда 200)
- `db.ok`: SELECT 1 через SQLAlchemy
- `migrations.ok/current/head`: current из alembic_version, head из ScriptDirectory, сравнить

Проверка:
- `curl -sS "http://localhost:8000/api/health" | python3 -m json.tool`
- В ответе db.ok=true и migrations.ok=true после `alembic upgrade head`

5.2 Тест health db+migrations  
Статус: next  
Файл: `tests/test_health_db_and_migrations.py`  
Проверка: `pytest -q tests/test_health_db_and_migrations.py`

## 6) Дальше по продукту (после закрытия шага 8)

6.1 Реальный запуск эксперимента: ExperimentEngine вызывает connector.create_campaign_bundle(...)  
Статус: backlog  
Проверка: интеграционный тест или dev endpoint “start experiment” + запись campaign_external_id в experiment_campaigns

6.2 Коннектор VK Ads: создать кампанию/объявления/креативы (без секретов в логах и БД)  
Статус: backlog  
Проверка: запуск в dev окружении с тестовым кабинетом + запись в job_runs

6.3 Коннектор Yandex Direct: создание кампаний + получение статистики  
Статус: backlog  
Проверка: то же

6.4 Сбор метрик в Postgres (metric_snapshots) и синхронизация по плану/эксперименту  
Статус: backlog  
Проверка: job_runs + API, которое показывает, что появились snapshots

6.5 Отчёт по эксперименту (агрегации, сравнение вариантов, базовые метрики)  
Статус: backlog  
Проверка: API отдаёт отчёт, тест проверяет идемпотентность и отсутствие дублей

6.6 ЕРИР/маркировка интернет-рекламы (минимальная интеграция)  
Статус: backlog  
Проверка: отдельный dev endpoint + запись результата в job_runs, без секретов
