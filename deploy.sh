#!/bin/bash
# =============================================================================
# Reklai Deployment Script
# Usage: ./deploy.sh [production|staging]
# =============================================================================

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Deploying Reklai ($ENVIRONMENT)"

# Check required environment variables
if [ "$ENVIRONMENT" = "production" ]; then
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "CREDENTIALS_ENC_KEYS"
        "ADMIN_USERNAME"
        "ADMIN_PASSWORD"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Error: $var is not set"
            echo "   Please set it in .env.prod or export it"
            exit 1
        fi
    done
fi

# Pull latest code
echo "📥 Pulling latest changes..."
git pull origin main || true

# Build containers
echo "🔨 Building containers..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f $COMPOSE_FILE run --rm api alembic upgrade head

# Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose -f $COMPOSE_FILE ps

# Show logs
echo "📋 Recent logs:"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Services:"
echo "   - Web: https://reklai.ru"
echo "   - API: https://api.reklai.ru"
echo ""
echo "📊 Commands:"
echo "   - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "   - Stop: docker-compose -f $COMPOSE_FILE down"
echo "   - Restart: docker-compose -f $COMPOSE_FILE restart"
