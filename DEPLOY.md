# Reklai Deployment Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Domain pointed to server IP
- SSL certificates (auto with Traefik)

### 1. Clone and Configure

```bash
git clone https://github.com/Lookatshow1/parser2.git /opt/reklai
cd /opt/reklai

# Copy and edit environment
cp .env.example .env.prod
nano .env.prod
```

### 2. Required Environment Variables

```bash
# Database
POSTGRES_PASSWORD=your-secure-db-password-32-chars
REDIS_PASSWORD=your-secure-redis-password

# Security
SECRET_KEY=your-64-char-secret-key-here
CREDENTIALS_ENC_KEYS=prod:base64-encoded-32-byte-key
CREDENTIALS_ENC_ACTIVE_KID=prod

# Admin Panel
ADMIN_USERNAME=admin
ADMIN_PASSWORD=minimum-16-characters-admin-password

# Domain
WEB_BASE_URL=https://reklai.ru
NEXT_PUBLIC_API_URL=https://api.reklai.ru
CORS_ORIGINS=https://reklai.ru,https://www.reklai.ru

# SSL
ACME_EMAIL=admin@reklai.ru
```

### 3. Deploy

```bash
chmod +x deploy.sh
./deploy.sh production
```

Or manually:

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                          │
└─────────────────────────┬───────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  Traefik  │ :80/:443
                    │  (HTTPS)  │
                    └─────┬─────┘
          ┌───────────────┼───────────────┐
          │               │               │
    ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐
    │    Web    │  │     API     │  │  Traefik  │
    │ (Next.js) │  │  (FastAPI)  │  │ Dashboard │
    │   :3000   │  │    :8000    │  │   :8080   │
    └───────────┘  └──────┬──────┘  └───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐
    │  Worker   │  │    Beat     │  │   Redis   │
    │ (Celery)  │  │ (Scheduler) │  │   :6379   │
    └─────┬─────┘  └─────────────┘  └───────────┘
          │
    ┌─────▼─────┐
    │ PostgreSQL│
    │   :5432   │
    └───────────┘
```

## Management Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f web

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop all
docker-compose -f docker-compose.prod.yml down

# Database backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U reklai reklai > backup.sql

# Database restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U reklai reklai < backup.sql

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create new migration
docker-compose -f docker-compose.prod.yml exec api alembic revision --autogenerate -m "description"

# Access shell
docker-compose -f docker-compose.prod.yml exec api bash
docker-compose -f docker-compose.prod.yml exec web sh
```

## SSL Certificates

Traefik automatically obtains and renews Let's Encrypt certificates.

Certificates are stored in `traefik_certs` volume.

## Scaling

```bash
# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

## Monitoring

### Health Checks

- API: `https://api.reklai.ru/health`
- API (k8s): `https://api.reklai.ru/readyz`

### Logs

```bash
# All logs
docker-compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

## CI/CD with GitHub Actions

The repository includes GitHub Actions workflows:

1. **ci.yml** - Runs on every PR and push to main
   - Lints backend (ruff)
   - Lints frontend (eslint)
   - Builds frontend
   - Runs backend tests

2. **deploy.yml** - Runs on push to main
   - Builds Docker images
   - Pushes to GitHub Container Registry
   - Deploys to production server via SSH

### Required Secrets

Set these in GitHub repository settings:

- `DEPLOY_HOST` - Server IP or hostname
- `DEPLOY_USER` - SSH username
- `DEPLOY_KEY` - SSH private key

## Troubleshooting

### API not starting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check database connection
docker-compose -f docker-compose.prod.yml exec api python -c "from app.db.session import engine; print(engine.execute('SELECT 1').scalar())"
```

### Frontend build fails
```bash
# Check memory
free -h

# Increase Node memory
export NODE_OPTIONS="--max-old-space-size=4096"
```

### SSL certificate issues
```bash
# Check Traefik logs
docker-compose -f docker-compose.prod.yml logs traefik

# Verify DNS
dig reklai.ru
dig api.reklai.ru
```

## Security Checklist

- [ ] Strong passwords in .env.prod (32+ chars)
- [ ] CORS_ORIGINS set to actual domains
- [ ] ENABLE_DEV_ENDPOINTS=false
- [ ] Firewall configured (only 80, 443 open)
- [ ] SSH key-only authentication
- [ ] Regular database backups
- [ ] Log monitoring configured
