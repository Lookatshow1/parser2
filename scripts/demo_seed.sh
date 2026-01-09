#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null; then
  echo "Docker not available" >&2
  exit 1
fi

response=$(docker compose run --rm api python - <<'PY'
import json
import sys
import urllib.request
import urllib.error

req = urllib.request.Request("http://api:8000/api/dev/demo/seed", method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        sys.stdout.write(resp.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    sys.stderr.write(f"HTTP {exc.code}: {body}\n")
    sys.exit(1)
except Exception as exc:
    sys.stderr.write(f"Request failed: {exc}\n")
    sys.exit(1)
PY
)

python3 - "$response" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
print("Demo seed complete.")
print(f"Demo email: {data.get('demo_user_email')}")
print(f"Demo password: {data.get('demo_password')}")
print(f"Org ID: {data.get('org_id')}")
print(f"Connections: {', '.join(str(x) for x in data.get('connection_ids', []))}")
print(f"Period: {data.get('period_from')} -> {data.get('period_to')}")
print("Open http://localhost:3000 and log in with the demo account.")
PY
