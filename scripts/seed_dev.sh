#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build
docker compose run --rm api alembic upgrade head

ADVERTISER_ID=$(docker compose exec -T db psql -U postgres -d ads -Atc \
  "INSERT INTO advertisers (name, created_at) VALUES ('Dev Advertiser', NOW()) RETURNING id;")

PROJECT_ID=$(docker compose exec -T db psql -U postgres -d ads -Atc \
  "INSERT INTO projects (advertiser_id, name, created_at) VALUES (${ADVERTISER_ID}, 'Dev Project', NOW()) RETURNING id;")

PLAN_ID=$(docker compose exec -T db psql -U postgres -d ads -Atc \
  "INSERT INTO campaign_plans (advertiser_id, url, created_at) VALUES (${ADVERTISER_ID}, 'https://example.com', NOW()) RETURNING id;")

EXPERIMENT_ID=$(curl -sS -X POST http://localhost:8000/experiments/create \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": ${PROJECT_ID},
    \"total_budget\": 10000,
    \"platforms\": [\"yandex\", \"ozon\", \"vk\"]
  }" | python -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -sS -X POST "http://localhost:8000/experiments/${EXPERIMENT_ID}/start"

echo "Seeded advertiser_id=${ADVERTISER_ID}, project_id=${PROJECT_ID}, plan_id=${PLAN_ID}"
