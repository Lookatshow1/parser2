# parser2

## Quick start

```bash
cp .env.example .env
docker compose up --build
docker compose run --rm api alembic upgrade head
```

## Frontend (Next.js)

```bash
cd apps/web
cp .env.example .env
npm install
npm run generate:types
npm run dev
```

Frontend reads `NEXT_PUBLIC_API_BASE_URL` for backend base URL.

## Health checks

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/healthz
curl http://localhost:8000/openapi.json
```

## Tests

```bash
pytest
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
