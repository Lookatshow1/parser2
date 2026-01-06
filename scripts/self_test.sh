#!/usr/bin/env bash
set -euo pipefail

make doctor

make reset-db

docker compose up -d api worker web

echo "Waiting for API..."
for _ in {1..60}; do
  if curl -fsS --max-time 3 "http://localhost:8000/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -fsS --max-time 3 "http://localhost:8000/api/health" >/dev/null; then
  echo "API did not become ready in time." >&2
  exit 1
fi

echo "Waiting for Web..."
for _ in {1..300}; do
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

USER_EMAIL="selftest@example.com"
USER_PASSWORD="secret123"
INVITED_EMAIL="invitee@example.com"
INVITED_PASSWORD="secret123"

curl -fsS --max-time 10 -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${USER_EMAIL}\",\"password\":\"${USER_PASSWORD}\"}" >/dev/null

LOGIN_JSON=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${USER_EMAIL}\",\"password\":\"${USER_PASSWORD}\"}")

TOKEN=$(printf '%s' "${LOGIN_JSON}" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['access_token'])")
REFRESH_TOKEN=$(printf '%s' "${LOGIN_JSON}" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['refresh_token'])")

TOKEN=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

ORG_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/orgs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"name":"Selftest Org"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

AUTH_HEADER="Authorization: Bearer ${TOKEN}"
ORG_HEADER="X-Org-Id: ${ORG_ID}"

INVITE_TOKEN=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/orgs/${ORG_ID}/invites" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "{\"email\":\"${INVITED_EMAIL}\",\"role\":\"member\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['invite_token'])")

curl -fsS --max-time 10 -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${INVITED_EMAIL}\",\"password\":\"${INVITED_PASSWORD}\"}" >/dev/null

INVITED_TOKEN=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${INVITED_EMAIL}\",\"password\":\"${INVITED_PASSWORD}\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -fsS --max-time 10 -X POST "http://localhost:8000/api/orgs/invites/accept" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${INVITED_TOKEN}" \
  -d "{\"token\":\"${INVITE_TOKEN}\"}" >/dev/null

INVITED_AUTH_HEADER="Authorization: Bearer ${INVITED_TOKEN}"
INVITED_ORG_HEADER="X-Org-Id: ${ORG_ID}"

CONN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/connections" \
  -H "Content-Type: application/json" \
  -H "${INVITED_AUTH_HEADER}" \
  -H "${INVITED_ORG_HEADER}" \
  -d '{"platform":"stub","credentials_json":{}}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

RUN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/sync-runs" \
  -H "Content-Type: application/json" \
  -H "${INVITED_AUTH_HEADER}" \
  -H "${INVITED_ORG_HEADER}" \
  -d "{\"connection_id\":${CONN_ID},\"params_json\":{\"date_from\":\"2023-01-01\",\"date_to\":\"2023-01-03\"}}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Waiting for sync run to finish..."
STATUS="queued"
for _ in {1..45}; do
  STATUS=$(curl -fsS --max-time 5 "http://localhost:8000/api/sync-runs/${RUN_ID}" \
    -H "${INVITED_AUTH_HEADER}" \
    -H "${INVITED_ORG_HEADER}" \
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

curl -fsS --max-time 10 "http://localhost:8000/api/metrics?connection_id=${CONN_ID}&date_from=2023-01-01&date_to=2023-01-03" \
  -H "${INVITED_AUTH_HEADER}" -H "${INVITED_ORG_HEADER}" >/dev/null
SUMMARY_JSON=$(curl -fsS --max-time 10 "http://localhost:8000/api/dashboard/summary?connection_id=${CONN_ID}&date_from=2023-01-01&date_to=2023-01-03" \
  -H "${INVITED_AUTH_HEADER}" -H "${INVITED_ORG_HEADER}")

CTR_VAL=$(printf '%s' "${SUMMARY_JSON}" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['totals'].get('ctr'))")
if [ -z "$CTR_VAL" ] || [ "$CTR_VAL" = "None" ]; then
  echo "Dashboard efficiency check failed: ctr is empty" >&2
  exit 1
fi

SECOND_RUN_ID=$(curl -fsS --max-time 10 -X POST "http://localhost:8000/api/sync-runs" \
  -H "Content-Type: application/json" \
  -H "${INVITED_AUTH_HEADER}" \
  -H "${INVITED_ORG_HEADER}" \
  -d "{\"connection_id\":${CONN_ID},\"params_json\":{\"date_from\":\"2023-01-01\",\"date_to\":\"2023-01-03\"}}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Waiting for second sync run to finish..."
SECOND_STATUS="queued"
for _ in {1..45}; do
  SECOND_STATUS=$(curl -fsS --max-time 5 "http://localhost:8000/api/sync-runs/${SECOND_RUN_ID}" \
    -H "${INVITED_AUTH_HEADER}" \
    -H "${INVITED_ORG_HEADER}" \
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
  -H "${INVITED_AUTH_HEADER}" \
  -H "${INVITED_ORG_HEADER}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('result_json', {}).get('inserted', ''))")
if [ "$SECOND_INSERTED" != "0" ]; then
  echo "Idempotency check failed: expected inserted=0, got ${SECOND_INSERTED}" >&2
  exit 1
fi

curl -fsS --max-time 10 "http://localhost:8000/api/sync-runs?connection_id=${CONN_ID}" \
  -H "${INVITED_AUTH_HEADER}" -H "${INVITED_ORG_HEADER}" >/dev/null
curl -fsS --max-time 10 "http://localhost:8000/api/job-runs?connection_id=${CONN_ID}" \
  -H "${INVITED_AUTH_HEADER}" -H "${INVITED_ORG_HEADER}" >/dev/null
