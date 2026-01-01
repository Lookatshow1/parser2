#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build
docker compose run --rm api alembic upgrade head

PLAN_ID=$(curl -sS -X POST http://localhost:8000/plans \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "internal_code": "campaign-123",
    "business_description": "Demo",
    "kpi": "leads"
  }' | python -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -sS -X POST "http://localhost:8000/api/plans/${PLAN_ID}/start_test" \
  -H "Content-Type: application/json" \
  -d '{"budget": 10000}'

docker compose exec -T db psql -U postgres -d ads -c \
  "SELECT COUNT(*) AS experiments FROM experiments;"
docker compose exec -T db psql -U postgres -d ads -c \
  "SELECT COUNT(*) AS creatives FROM creative_variants;"
docker compose exec -T db psql -U postgres -d ads -c \
  "SELECT COUNT(*) AS allocations FROM budget_allocations;"
