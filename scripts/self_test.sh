#!/usr/bin/env bash
set -euo pipefail

# start only db and redis, run migrations and tests
docker compose up -d db redis

docker compose run --rm api alembic upgrade head

docker compose run --rm api pytest -q
