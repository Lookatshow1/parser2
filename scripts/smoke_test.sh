#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build
docker compose run --rm api alembic upgrade head

ADVERTISER_ID=$(docker compose exec -T db psql -U postgres -d ads -Atc \
  "INSERT INTO advertisers (name, created_at) VALUES ('Smoke Advertiser', NOW()) RETURNING id;")

PLAN_ID=$(docker compose exec -T db psql -U postgres -d ads -Atc \
  "INSERT INTO campaign_plans (advertiser_id, url, created_at) VALUES (${ADVERTISER_ID}, 'https://example.com', NOW()) RETURNING id;")

curl -sS http://localhost:8000/healthz
curl -sS http://localhost:8000/openapi.json > /dev/null

echo "Smoke test OK: advertiser_id=${ADVERTISER_ID}, plan_id=${PLAN_ID}"
