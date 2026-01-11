# HANDOFF.md — Передача контекста разработки

**Дата:** 2026-01-04  
**Ветка:** codex/create-monorepo-for-ads-aggregator-service  
**Последняя миграция:** 0022_change_plans

---

## Краткий статус проекта

Проект parser2 — сервис агрегации рекламных метрик с поддержкой экспериментов. Работает: health endpoint `/api/health`, эндпоинт синхронизации метрик Yandex `/api/integrations/yandex/sync-metrics`, Celery-воркер `sync_yandex_metrics`, таблица `metric_snapshots` с уникальным constraint для идемпотентного синка, отчёты по `plan_id` с фильтрацией по датам, исправлен enum статусов экспериментов (draft, running, stopped, completed). Проект активно развивается: добавлены каталог объявлений, рекомендации, планы изменений, UTM builder.

---

## Что сделано по шагам 1–6

### Шаг 1: Исправление падения API (health endpoint)

**Цель:** API не отвечал на запросы, контейнер падал при старте.

**Изменённые файлы:**
- `app/db/models.py` — исправлен `ExperimentStatus.planned` → `ExperimentStatus.draft`
- `app/api/integrations.py` — удалён дублирующий `return` statement
- `app/api/schemas.py` — удалены дублирующие импорты `datetime` и `BaseModel`
- `app/main.py` — добавлен endpoint `GET /api/health` (возвращает `{"status":"ok"}`)
- `README.md` — обновлена секция Health checks

**Ключевые правки:**
- В модели `Experiment` поле `status` использовало несуществующий enum value `planned`, заменено на `draft`
- Добавлен простой health endpoint без зависимости от БД

**Команды проверки:**
```bash
docker compose ps api
docker compose logs api --tail=200
curl -sS http://localhost:8000/api/health
```

**Результат:** API запускается без ошибок, health endpoint возвращает `{"status":"ok"}`.

---

### Шаг 2: Обновление эндпоинта sync-metrics

**Цель:** Привести эндпоинт `POST /api/integrations/yandex/sync-metrics` к актуальной схеме запроса.

**Изменённые файлы:**
- `app/api/integrations.py` — добавлена валидация `date_from <= date_to`, корректный вызов задачи

**Ключевые правки:**
- Добавлена проверка валидности дат с HTTP 400 при некорректных значениях
- Использование `sync_yandex_metrics.delay(connection_id, plan_id, date_from_iso, date_to_iso)`

**Команды проверки:**
```bash
curl -sS -X POST http://localhost:8000/api/integrations/yandex/sync-metrics \
  -H "Content-Type: application/json" \
  -d '{"connection_id":1,"plan_id":4,"date_from":"2026-01-01T00:00:00","date_to":"2026-01-04T00:00:00"}' | python3 -m json.tool
```

**Результат:** Эндпоинт возвращает `job_id`, валидация работает корректно.

---

### Шаг 3: Исправление Celery-задачи sync_yandex_metrics

**Цель:** Воркер должен корректно выполнять задачу и сохранять `MetricSnapshot` с заполненными `plan_id` и `connection_id`.

**Изменённые файлы:**
- `app/workers/yandex_tasks.py` — добавлено логирование, корректная обработка ошибок, гарантирован `created_at`
- `app/workers/__init__.py` — добавлены импорты для регистрации задач

**Ключевые правки:**
- Добавлено логирование в начале, после получения данных, в конце
- Обработка отсутствия connection: возврат словаря с ошибкой вместо исключения
- Явная установка `created_at = datetime.utcnow()` для всех метрик
- Использование upsert через `on_conflict_do_update` с constraint `uq_metric_snapshots_conn_plan_date_campaign`

**Команды проверки:**
```bash
docker compose logs worker --tail=200
docker compose exec db psql -U postgres -d ads -c "select plan_id, connection_id, count(*) from metric_snapshots group by 1,2 order by 3 desc;"
```

**Результат:** Worker не падает, задача выполняется, метрики сохраняются с правильными `plan_id` и `connection_id`.

---

### Шаг 4: Гарантия идемпотентности metric_snapshots

**Цель:** Таблица `metric_snapshots` должна поддерживать идемпотентный синк через unique constraint.

**Изменённые файлы:**
- `alembic/versions/0006_add_plan_connection_to_metrics.py` — добавлена дедупликация перед созданием constraint

**Ключевые правки:**
- Дедупликация существующих данных через SQL с `ROW_NUMBER()` перед созданием constraint
- Создание unique constraint `uq_metric_snapshots_conn_plan_date_campaign` на `(connection_id, plan_id, date, campaign_external_id)`
- Внешние ключи на `campaign_plans.id` и `connections.id` с `ondelete="SET NULL"`

**SQL для дедупликации:**
```sql
DELETE FROM metric_snapshots
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY connection_id, plan_id, date, campaign_external_id
            ORDER BY id DESC
        ) as rn
        FROM metric_snapshots
        WHERE connection_id IS NOT NULL AND plan_id IS NOT NULL
    ) t WHERE rn > 1
)
```

**Команды проверки:**
```bash
docker compose run --rm api alembic upgrade head
docker compose exec db psql -U postgres -d ads -c "\d metric_snapshots"
docker compose exec db psql -U postgres -d ads -c "select connection_id, plan_id, date, campaign_external_id, count(*) c from metric_snapshots where connection_id is not null and plan_id is not null group by 1,2,3,4 having count(*) > 1 limit 20;"
```

**Результат:** Миграция применена, constraint создан, дубликатов нет, повторный синк не увеличивает число строк.

**Миграция:** `0006_add_plan_connection` (revision: `0006_add_plan_connection`, down_revision: `991e7971e174`)

---

### Шаг 5: Исправление enum статусов экспериментов

**Цель:** Синхронизировать допустимые статусы между Python и базой данных (добавить 'planned' если нужно, или привести к единому стандарту).

**Статус:** **ТРЕБУЕТ УТОЧНЕНИЯ**

**Текущее состояние:**
- Python enum `ExperimentStatus`: `draft`, `running`, `stopped`, `completed` (4 значения)
- Postgres enum `experiment_status_enum`: `draft`, `running`, `stopped`, `completed` (4 значения)
- В базе данных есть записи со статусом `'planned'`, которого нет в enum (ошибка при чтении)

**Проблема:** В базе данных есть эксперименты со статусом `'planned'`, но этот статус не существует в enum. При попытке загрузить такой эксперимент возникает ошибка `LookupError: 'planned' is not among the defined enum values`.

**Требуется:** Либо добавить `'planned'` в enum (миграция), либо обновить записи в базе на допустимое значение (например, `'draft'`).

**Изменённые файлы:** Пока не исправлено (требуется действие).

---

### Шаг 6: Отчёты по plan_id с фильтрацией

**Цель:** Отчёты должны считать метрики только для конкретного `plan_id` и выбранного периода, а не суммировать все `metric_snapshots`.

**Изменённые файлы:**
- `app/api/metrics.py` — обновлён `/api/metrics/summary`: обязательный `plan_id`, опциональные `date_from`/`date_to` (дефолт: последние 7 дней)
- `app/api/experiments.py` — обновлён `/api/experiments/{experiment_id}/report`: фильтрация по `experiment.plan_id` и датам
- `app/api/schemas.py` — обновлены `MetricsSummaryResponse` и `ExperimentReportResponse`

**Ключевые правки:**
- Добавлены фильтры `.filter(MetricSnapshot.plan_id == plan_id)` и `.filter(MetricSnapshot.date >= date_from).filter(MetricSnapshot.date <= date_to)`
- Добавлены производные показатели CPC, CPL, CPA с безопасным делением на ноль (возвращают `None`)
- Дефолтные даты: последние 7 дней до текущей даты (UTC)

**Команды проверки:**
```bash
curl -sS "http://localhost:8000/api/metrics/summary?plan_id=4" | python3 -m json.tool
curl -sS "http://localhost:8000/api/metrics/summary?plan_id=4&date_from=2026-01-01&date_to=2026-01-04" | python3 -m json.tool
curl -sS "http://localhost:8000/api/experiments/3/report" | python3 -m json.tool
```

**Результат:** Оба эндпоинта фильтруют по `plan_id` и датам, возвращают нули при отсутствии данных.

---

## Текущее состояние базы/схемы

### metric_snapshots

**Колонки:**
- `plan_id` (Integer, nullable=True, FK на `campaign_plans.id`)
- `connection_id` (Integer, nullable=True, FK на `connections.id`)

**Unique constraints:**
- `uq_metric_snapshots_conn_plan_date_campaign` на `(connection_id, plan_id, date, campaign_external_id)` — **НОТА:** Судя по `\d metric_snapshots`, текущая схема использует другие constraints (по organization_id, experiment_id, level). Возможно, структура изменилась после шага 4.

**Индексы:** Множество индексов по `connection_id`, `date`, `level`, уникальные constraints по уровням (campaign/ad_group/ad) с условиями.

### experiments.status enum

**Postgres enum тип:** `experiment_status_enum`

**Текущие значения в enum:**
- `draft`
- `running`
- `stopped`
- `completed`

**Python enum (`ExperimentStatus`):**
- `draft = "draft"`
- `running = "running"`
- `stopped = "stopped"`
- `completed = "completed"`

**Проблема:** В базе данных есть записи со статусом `'planned'`, которого нет в enum.

**Расположение:** `app/db/models.py:28-32`

---

## Известные проблемы/риски

1. **Enum статусов экспериментов:** В базе данных есть эксперименты со статусом `'planned'`, но этот статус не существует в enum. При попытке загрузить такой эксперимент возникает ошибка. Требуется либо миграция для добавления `'planned'`, либо обновление записей.

2. **Структура metric_snapshots:** Судя по текущему `\d metric_snapshots`, структура таблицы отличается от той, что была создана в шаге 4. Возможно, были применены дополнительные миграции. Текущая схема использует `organization_id`, `experiment_id`, `level`, множественные unique constraints по уровням.

3. **Эндпоинт `/api/experiments/{id}/report`:** Может падать из-за проблемы с enum (см. выше).

---

## Что НЕ выполнено

### Шаг 7: Привязка кампаний к эксперименту (управляемый эксперимент)

**Требуется сделать:**

1. **Модель ExperimentCampaign:**
   - Таблица `experiment_campaigns`
   - Поля: `id`, `experiment_id` (FK на `experiments.id`, cascade delete), `platform` (enum), `campaign_external_id` (varchar), `created_at`
   - Unique constraint: `(experiment_id, platform, campaign_external_id)`

2. **Миграция Alembic:**
   - Создание таблицы `experiment_campaigns`
   - Создание unique constraint
   - Downgrade должен удалять таблицу

3. **API эндпоинты:**
   - `GET /api/experiments/{experiment_id}/campaigns` — возвращает список кампаний
   - `PUT /api/experiments/{experiment_id}/campaigns` — принимает `{"items":[{"platform":"yandex","campaign_external_id":"123"}, ...]}` и заменяет список полностью
   - Валидация: platform должен быть корректным enum, `campaign_external_id` непустой

4. **Обновление отчёта эксперимента:**
   - В `GET /api/experiments/{experiment_id}/report`: если для эксперимента задан хотя бы один `ExperimentCampaign`, фильтровать метрики по `MetricSnapshot.plan_id == experiment.plan_id` И `MetricSnapshot.campaign_external_id IN (список campaign_external_id для соответствующей платформы)`
   - Если список кампаний пуст, оставить текущее поведение (фильтр только по `plan_id`)

5. **Обновление перераспределения бюджета:**
   - В `ExperimentService._reallocate_budget`: если у эксперимента есть список кампаний, считать агрегаты `clicks`/`spend` только по этим `campaign_external_id` (и по `plan_id`)
   - Если кампаний нет, оставить fallback на `plan_id`

**Файлы для создания/изменения:**
- `app/db/models.py` — модель `ExperimentCampaign`
- `alembic/versions/00XX_add_experiment_campaigns.py` — миграция
- `app/api/experiments.py` — эндпоинты campaigns
- `app/api/schemas.py` — схемы для запросов/ответов campaigns
- `app/services/experiment_service.py` — обновление `_reallocate_budget`

---

## Следующие действия

1. **Исправить enum статусов экспериментов:**
   - Создать миграцию для добавления `'planned'` в `experiment_status_enum` (или обновить записи на `'draft'`)
   - Протестировать чтение экспериментов со статусом `'planned'`

2. **Реализовать шаг 7 (привязка кампаний к эксперименту):**
   - Создать модель и миграцию для `experiment_campaigns`
   - Реализовать API эндпоинты
   - Обновить отчёт и перераспределение бюджета

3. **Протестировать интеграцию:**
   - Проверить работу эндпоинтов campaigns
   - Проверить фильтрацию в отчёте
   - Проверить перераспределение бюджета

---

## Проверочные команды

### Базовая проверка работоспособности:
```bash
# Проверка контейнеров
docker compose ps

# Health endpoint
curl -sS http://localhost:8000/api/health | python3 -m json.tool

# Проверка миграций
docker compose run --rm api alembic upgrade head
docker compose exec db psql -U postgres -d ads -c "SELECT version_num FROM alembic_version;"

# Структура metric_snapshots
docker compose exec db psql -U postgres -d ads -c "\d metric_snapshots"

# Enum статусов экспериментов
docker compose exec db psql -U postgres -d ads -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'experiment_status_enum'::regtype ORDER BY enumsortorder;"

# Эксперименты в базе
docker compose exec db psql -U postgres -d ads -c "SELECT id, plan_id, status::text FROM experiments ORDER BY id LIMIT 5;"
```

### Проверка эндпоинтов:
```bash
# Metrics summary
curl -sS "http://localhost:8000/api/metrics/summary?plan_id=4" | python3 -m json.tool
curl -sS "http://localhost:8000/api/metrics/summary?plan_id=4&date_from=2026-01-01&date_to=2026-01-04" | python3 -m json.tool

# Experiment report (может падать из-за enum)
curl -sS "http://localhost:8000/api/experiments/3/report" | python3 -m json.tool

# Yandex sync
curl -sS -X POST http://localhost:8000/api/integrations/yandex/sync-metrics \
  -H "Content-Type: application/json" \
  -d '{"connection_id":1,"plan_id":4,"date_from":"2026-01-01T00:00:00","date_to":"2026-01-04T00:00:00"}' | python3 -m json.tool

# Логи worker
docker compose logs worker --tail=200 | grep -E "(sync_yandex_metrics|Starting|Fetched|Sync completed)"
```

### Проверка данных:
```bash
# Метрики по plan_id и connection_id
docker compose exec db psql -U postgres -d ads -c "select plan_id, connection_id, count(*) from metric_snapshots group by 1,2 order by 3 desc;"

# Дубликаты (не должно быть)
docker compose exec db psql -U postgres -d ads -c "select connection_id, plan_id, date, campaign_external_id, count(*) c from metric_snapshots where connection_id is not null and plan_id is not null group by 1,2,3,4 having count(*) > 1 limit 20;"
```

---

## Diff Summary

### Git Status:
```
Текущая ветка: codex/create-monorepo-for-ads-aggregator-service
Ваша ветка опережает «origin/codex/create-monorepo-for-ads-aggregator-service» на 44 коммита.

Изменения, которые будут включены в коммит:
	новый файл:    .gemini_backup/settings.json
	изменено:      README.md
	новый файл:    alembic/versions/0017_add_builder_tables.py
	новый файл:    alembic/versions/0018_ad_catalog_tables.py
	новый файл:    alembic/versions/0019_add_correlation_id.py
	новый файл:    alembic/versions/0020_org_recommendations.py
	новый файл:    alembic/versions/0021_org_recommendations.py
	новый файл:    alembic/versions/0022_change_plans.py
	... (много других файлов)
```

### Git Diff Stat:
```
 .gemini/settings.json                  |   9 +-
 Makefile                               |  10 +-
 README.md                              |  21 ++
 TODO.md                                |  38 ++++
 alembic/versions/0022_change_plans.py  |   4 +-
 app/api/dashboard.py                   | 192 +++--------------
 app/api/health.py                      | 106 +++++-----
 app/api/metrics.py                     | 296 +++++++++++++++++++++++++-
 app/api/schemas.py                     | 286 ++++++++++++++++++++++++++
 app/api/sync_runs.py                   |   6 +
 app/core/logging.py                    |  32 ++-
 app/db/models.py                       | 225 +++++++++++++++++++-
 app/dev/demo_seed.py                   | 165 +++++++++++++++
 app/jobs/service.py                    |   4 +-
 app/main.py                            |  15 +-
 app/services/sync_run_service.py       |  8 +-
 app/services/sync_service.py           |  6 +
 app/workers/sync_tasks.py              |  7 +-
 apps/web/app/connections/[id]/page.tsx |   2 +-
 apps/web/app/connections/page.tsx      |   2 +-
 apps/web/app/dashboard/page.tsx        | 320 ++++++++++++++++-------------
 apps/web/app/experiments/[id]/page.tsx |   2 +-
 apps/web/app/experiments/page.tsx      |   2 +-
 apps/web/app/invite/[token]/page.tsx   |   2 +-
 apps/web/app/invite/page.tsx           |  2 +-
 apps/web/app/metrics/page.tsx          | 205 +++++++++++++-----
 apps/web/app/orgs/audit/page.tsx       |   2 +-
 apps/web/app/orgs/members/page.tsx     |   2 +-
 apps/web/app/orgs/page.tsx             |   2 +-
 apps/web/app/sync-runs/page.tsx        |   2 +-
 apps/web/components/app-shell.tsx      |  1 +
 apps/web/lib/api.ts                    | 365 +++++++++++++++++++++++++++++++++
 apps/web/next.config.js                |  11 +-
 docker-compose.yml                     |  2 +
 requirements.txt                       |  31 ++-
 scripts/self_test.sh                   |  32 +++
 36 files changed, 1957 insertions(+), 460 deletions(-)
```

**Примечание:** Проект значительно продвинулся за пределы шагов 1-6. Добавлены каталог объявлений, рекомендации, планы изменений, UTM builder. Текущая структура `metric_snapshots` отличается от той, что была в шаге 4 (используются `organization_id`, `experiment_id`, `level`).

---

## Дополнительная информация

### Ключевые файлы:

**Модели:**
- `app/db/models.py` — модели данных (Experiment, MetricSnapshot, ExperimentCampaign уже существует!)

**API:**
- `app/api/health.py` — health endpoint
- `app/api/metrics.py` — метрики и отчёты
- `app/api/experiments.py` — эксперименты
- `app/api/integrations.py` — синхронизация метрик

**Workers:**
- `app/workers/yandex_tasks.py` — задача синхронизации метрик Yandex
- `app/workers/__init__.py` — регистрация задач

**Миграции:**
- `alembic/versions/0006_add_plan_connection_to_metrics.py` — добавление plan_id/connection_id (если существует)
- `alembic/versions/0022_change_plans.py` — последняя применённая миграция

**Схемы:**
- `app/api/schemas.py` — Pydantic схемы для API

### Важные замечания:

1. **ExperimentCampaign уже существует!** Судя по поиску в коде, модель `ExperimentCampaign` уже создана в `app/db/models.py:312-326`. Возможно, шаг 7 частично выполнен, но API эндпоинты для управления кампаниями могут отсутствовать.

2. **Структура проекта изменилась:** Добавлены организации, аудит, каталог, рекомендации. Текущая структура более сложная, чем описывалось в шагах 1-6.

3. **Миграции:** Последняя применённая миграция — `0022_change_plans`. Миграция `0006_add_plan_connection_to_metrics.py` может не существовать в текущем состоянии (судя по deleted_files, она была удалена).
