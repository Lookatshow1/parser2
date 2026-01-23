#!/bin/bash
set -e

REMOTE_USER="root"
REMOTE_HOST="77.232.128.173"
REMOTE_PATH="/root/parser2"

echo "🚀 Deploying to ${REMOTE_USER}@${REMOTE_HOST}..."

# Sync code excluding node_modules, .venv, etc.
echo "📦 Syncing code..."
rsync -avz --exclude '.git' --exclude '.venv' --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

# Run commands on the server
echo "⚙️ Restarting services and running migrations..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
  cd /root/parser2
  docker compose up -d --build
  # Use exec instead of run to use the existing network and environment
  docker compose exec -T api alembic upgrade head
  docker compose restart api worker
EOF

echo "✅ Deployment successful!"
