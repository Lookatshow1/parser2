# parser2

## Quick start

```bash
cp .env.example .env
make up
make migrate
```

## Frontend (Next.js)

```bash
make up
```

Frontend reads `NEXT_PUBLIC_API_BASE_URL` for backend base URL.
Open http://localhost:3000 after `make up`.

## Smoke flow (API)

```bash
curl -sS -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{"platform":"stub","credentials_json":{}}'

curl -sS -X POST http://localhost:8000/api/sync-runs \
  -H "Content-Type: application/json" \
  -d '{"connection_id":1,"params_json":{"date_from":"2023-01-01","date_to":"2023-01-03"}}'

curl -sS http://localhost:8000/api/sync-runs/1
curl -sS "http://localhost:8000/api/job-runs?connection_id=1"

curl -sS "http://localhost:8000/api/metrics?connection_id=1&date_from=2023-01-01&date_to=2023-01-03"
curl -sS "http://localhost:8000/api/dashboard/summary?connection_id=1&date_from=2023-01-01&date_to=2023-01-03"
```

## Health checks

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/healthz
curl http://localhost:8000/openapi.json
```

## Tests

```bash
make test
```

## Самопроверка

Запустите быстрый набор самопроверок (поднимет БД и Redis, применит миграции и запустит тесты):

```bash
./scripts/self_test.sh
```

Self-test также проверяет web, smoke синк и идемпотентность (повторный sync не увеличивает число snapshot).

Перед проверками можно выполнить быструю диагностику Docker:

```bash
make doctor
```

## Helper scripts

```bash
./scripts/self_test.sh
./scripts/smoke_test.sh
./scripts/seed_dev.sh
```

## Event endpoints examples

Lead:

```bash
curl -X POST http://localhost:8000/api/events/lead \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_id": "11111111-1111-1111-1111-111111111111",
    "occurred_at": "2024-01-01T12:00:00Z",
    "landing_url": "https://example.com/landing",
    "utm_source": "yandex",
    "utm_medium": "cpc",
    "utm_campaign": "campaign-123",
    "utm_content": "banner",
    "utm_term": "ads",
    "contact": {
      "email": "lead@example.com"
    }
  }'
```

Purchase:

```bash
curl -X POST http://localhost:8000/api/events/purchase \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_id": "22222222-2222-2222-2222-222222222222",
    "occurred_at": "2024-01-01T12:05:00Z",
    "landing_url": "https://example.com/landing",
    "utm_source": "vk",
    "utm_medium": "cpc",
    "utm_campaign": "campaign-123",
    "value": 1500,
    "contact": {
      "phone": "+79990000000"
    }
  }'
```
