#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import subprocess
import sys

try:
    subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=10,
    )
except Exception:
    print("Docker daemon is not available. Start Docker Desktop and retry.", file=sys.stderr)
    sys.exit(1)
PY

make reset-db

docker compose up -d api

echo "Waiting for API..."
for _ in {1..30}; do
  if curl -sS "http://localhost:8000/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

CONN_ID=$(curl -sS -X POST "http://localhost:8000/api/connections" \
  -H "Content-Type: application/json" \
  -d '{"platform":"stub","credentials_json":{}}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

RUN_ID=$(curl -sS -X POST "http://localhost:8000/api/sync-runs" \
  -H "Content-Type: application/json" \
  -d "{\"connection_id\":${CONN_ID},\"params_json\":{\"date_from\":\"2023-01-01\",\"date_to\":\"2023-01-03\"}}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

docker compose run --rm api \
  python -c "from app.workers.sync_tasks import execute_sync_run; execute_sync_run(${RUN_ID})"

curl -sS "http://localhost:8000/api/sync-runs/${RUN_ID}" >/dev/null
curl -sS "http://localhost:8000/api/metrics?connection_id=${CONN_ID}&date_from=2023-01-01&date_to=2023-01-03" >/dev/null

docker compose run --rm api pytest -q
