#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import subprocess
import sys

def run_check(cmd, error_message):
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=20,
        )
    except Exception:
        print(error_message, file=sys.stderr)
        sys.exit(1)

run_check(["docker", "info"], "Docker daemon is not available. Start Docker Desktop and retry.")
run_check(["docker", "compose", "version"], "docker compose is not available. Install Docker Compose v2.")
PY
