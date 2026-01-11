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

## Интерфейс (RU + компоненты)

Интерфейс по умолчанию на русском. Web использует Tailwind + Radix UI и набор общих компонентов в `apps/web/components/ui`.
Базовые стили и цветовая схема описаны в `apps/web/app/globals.css`.
Правило продукта: сервис ориентирован на РФ, поэтому UI и тексты API по умолчанию на русском.

Глобальные стили подключаются в `apps/web/app/layout.tsx` через `./globals.css`, файл лежит в `apps/web/app/globals.css`.

## Демо-дашборд

1) Создайте mock подключение Яндекс (см. smoke flow ниже).
2) Запустите синк за последние 14 дней.
3) Откройте http://localhost:3000/metrics, чтобы увидеть карточки, график и таблицу.
4) Откройте http://localhost:3000/dashboard, если нужен обзор по всем подключениям.

## Демо-режим (готовые данные)

```bash
docker compose up -d --build
make demo-seed
```

Вход в Web: http://localhost:3000  
Демо-учётка берётся из `DEMO_EMAIL`/`DEMO_PASSWORD` (по умолчанию `demo@example.com` / `demo12345`).  
После `make demo-seed` в организации будут подключения и метрики за последние 14 дней.

## Email invites (MailHog)

Local dev uses MailHog to capture outgoing invite emails.

```bash
make up
```

MailHog UI: http://localhost:8025  
SMTP endpoint: localhost:1025

## Smoke flow (API)

```bash
curl -sS -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'

# Register creates a Personal org and sets it active by default.

LOGIN_JSON=$(curl -sS -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}')

TOKEN=$(printf '%s' "${LOGIN_JSON}" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['access_token'])")
REFRESH_TOKEN=$(printf '%s' "${LOGIN_JSON}" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['refresh_token'])")

TOKEN=$(curl -sS -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

ORG_ID=$(curl -sS -X POST http://localhost:8000/api/orgs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"name":"Demo Org"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

curl -sS -X POST http://localhost:8000/api/orgs/${ORG_ID}/activate \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null

INVITE_TOKEN=$(curl -sS -X POST "http://localhost:8000/api/orgs/${ORG_ID}/invites" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"email":"member@example.com","role":"member"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['invite_token'])")

MEMBER_TOKEN=$(curl -sS -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"member@example.com","password":"secret123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -sS -X POST http://localhost:8000/api/orgs/invites/accept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MEMBER_TOKEN}" \
  -d "{\"token\":\"${INVITE_TOKEN}\"}"

curl -sS -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MEMBER_TOKEN}" \
  -H "X-Org-Id: ${ORG_ID}" \
  -d '{"platform":"yandex","credentials_json":{"mock":true}}'

curl -sS -X POST http://localhost:8000/api/sync-runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MEMBER_TOKEN}" \
  -H "X-Org-Id: ${ORG_ID}" \
  -d '{"connection_id":1,"params_json":{"date_from":"2023-01-01","date_to":"2023-01-03"}}'

curl -sS http://localhost:8000/api/sync-runs/1 -H "Authorization: Bearer ${MEMBER_TOKEN}" -H "X-Org-Id: ${ORG_ID}"
curl -sS "http://localhost:8000/api/job-runs?connection_id=1" -H "Authorization: Bearer ${MEMBER_TOKEN}" -H "X-Org-Id: ${ORG_ID}"

curl -sS "http://localhost:8000/api/metrics?connection_id=1&date_from=2023-01-01&date_to=2023-01-03" -H "Authorization: Bearer ${MEMBER_TOKEN}" -H "X-Org-Id: ${ORG_ID}"
curl -sS "http://localhost:8000/api/connections/1/snapshots?date_from=2023-01-01&date_to=2023-01-03" -H "Authorization: Bearer ${MEMBER_TOKEN}" -H "X-Org-Id: ${ORG_ID}"
curl -sS "http://localhost:8000/api/dashboard/summary?connection_id=1&date_from=2023-01-01&date_to=2023-01-03" -H "Authorization: Bearer ${MEMBER_TOKEN}" -H "X-Org-Id: ${ORG_ID}"
```

## Connector credentials (structure)

These are only structural checks now; real API calls are not required for stub/self-test.
Dev demo uses Yandex mock mode with deterministic metrics per connection and date range.

- Yandex: `{"mock":true}` for demo or `{"token":"..."}` (optional `login`) for real keys
- VK Ads: `{"access_token":"...","version":"5.131","account_id":"..."}`
- Ozon Performance: `{"client_id":"...","client_secret":"..."}`

## Credentials encryption (at rest)

Credentials are stored encrypted in `connections.credentials_json` as a wrapper:

```json
{"__enc__":true,"v":1,"kid":"<key-id>","ct":"<ciphertext>"}
```

Configure keys via env:

```
CREDENTIALS_ENC_KEYS="kid1:base64key1,kid2:base64key2"
CREDENTIALS_ENC_ACTIVE_KID="kid1"
```

If keys are missing in dev, plaintext storage is allowed with a warning. In prod, missing keys cause startup failure.
Rotate credentials with `make rotate-credentials` after changing the active key.

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
Теперь self-test также проверяет auth + инвайт + membership.
Connections API не возвращает credentials_json (есть только credentials_present).
Первый прогон self-test после `docker compose down --volumes` может занять больше времени из-за установки npm-зависимостей для web.

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
