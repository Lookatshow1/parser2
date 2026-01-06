#!/usr/bin/env bash
set -euo pipefail

make doctor

make reset-db

docker compose up -d api worker web

echo "Waiting for API..."
for _ in {1..60}; do
  if curl -fsS --max-time 5 "http://localhost:8000/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -fsS --max-time 5 "http://localhost:8000/api/health" >/dev/null; then
  echo "API did not become ready in time." >&2
  exit 1
fi

echo "Waiting for Web..."
for _ in {1..180}; do
  if curl -fsS --max-time 5 "http://localhost:3000" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -fsS --max-time 5 "http://localhost:3000" >/dev/null; then
  echo "Web did not become ready in time." >&2
  exit 1
fi

docker compose run --rm api pytest -q

CONN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/connections" \
  -H "Content-Type: application/json" \
  -d '{"platform":"stub","credentials_json":{}}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

RUN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/sync-runs" \
  -H "Content-Type: application/json" \
  -d "{\"connection_id\":${CONN_ID},\"params_json\":{\"date_from\":\"2023-01-01\",\"date_to\":\"2023-01-03\"}}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Waiting for sync run to finish..."
STATUS="queued"
for _ in {1..45}; do
  STATUS=$(curl -fsS --max-time 5 "http://localhost:8000/api/sync-runs/${RUN_ID}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" || true)
  if [ -z "$STATUS" ]; then
    sleep 2
    continue
  fi
  if [ "$STATUS" = "success" ]; then
    break
  fi
  if [ "$STATUS" = "failed" ]; then
    echo "Sync run failed." >&2
    exit 1
  fi
  sleep 2
done

if [ "$STATUS" != "success" ]; then
  echo "Sync run did not finish in time (status=${STATUS})." >&2
  exit 1
fi

curl -fsS --max-time 10 "http://localhost:8000/api/metrics?connection_id=${CONN_ID}&date_from=2023-01-01&date_to=2023-01-03" >/dev/null
curl -fsS --max-time 10 "http://localhost:8000/api/dashboard/summary?connection_id=${CONN_ID}&date_from=2023-01-01&date_to=2023-01-03" >/dev/null

SECOND_RUN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/sync-runs" \
  -H "Content-Type: application/json" \
  -d "{\"connection_id\":${CONN_ID},\"params_json\":{\"date_from\":\"2023-01-01\",\"date_to\":\"2023-01-03\"}}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Waiting for second sync run to finish..."
SECOND_STATUS="queued"
for _ in {1..45}; do
  SECOND_STATUS=$(curl -fsS --max-time 5 "http://localhost:8000/api/sync-runs/${SECOND_RUN_ID}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" || true)
  if [ -z "$SECOND_STATUS" ]; then
    sleep 2
    continue
  fi
  if [ "$SECOND_STATUS" = "success" ]; then
    break
  fi
  if [ "$SECOND_STATUS" = "failed" ]; then
    echo "Second sync run failed." >&2
    exit 1
  fi
  sleep 2
done

if [ "$SECOND_STATUS" != "success" ]; then
  echo "Second sync run did not finish in time (status=${SECOND_STATUS})." >&2
  exit 1
fi

SECOND_INSERTED=$(curl -fsS --max-time 5 "http://localhost:8000/api/sync-runs/${SECOND_RUN_ID}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('result_json', {}).get('inserted', ''))")
if [ "$SECOND_INSERTED" != "0" ]; then
  echo "Idempotency check failed: expected inserted=0, got ${SECOND_INSERTED}" >&2
  exit 1
fi

curl -fsS --max-time 10 "http://localhost:8000/api/sync-runs?connection_id=${CONN_ID}" >/dev/null
curl -fsS --max-time 10 "http://localhost:8000/api/job-runs?connection_id=${CONN_ID}" >/dev/null
