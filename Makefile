.PHONY: up down reset-db migrate heads current history test seed demo-seed selftest db-shell logs ps logs-worker logs-api logs-db logs-web doctor rotate-credentials web-build web-prod-build

up:
	@$(MAKE) doctor
	docker compose up -d db redis api worker web beat mailhog

down:
	@$(MAKE) doctor
	docker compose down --volumes

logs:
	@$(MAKE) doctor
	docker compose logs -f || (echo "No running containers. Run 'make up' first." && exit 0)

logs-worker:
	@$(MAKE) doctor
	docker compose logs -f worker || (echo "Worker not running. Run 'make up' first." && exit 0)

logs-api:
	@$(MAKE) doctor
	docker compose logs -f api || (echo "API not running. Run 'make up' first." && exit 0)

logs-db:
	@$(MAKE) doctor
	docker compose logs -f db || (echo "DB not running. Run 'make up' first." && exit 0)

logs-web:
	@$(MAKE) doctor
	docker compose logs -f web || (echo "Web not running. Run 'make up' first." && exit 0)

web-build:
	@$(MAKE) doctor
	docker compose run --rm web npm run build

web-prod-build:
	@$(MAKE) doctor
	NODE_OPTIONS="--max-old-space-size=4096" NEXT_TELEMETRY_DISABLED=1 docker compose run --rm web npm run build

ps:
	@$(MAKE) doctor
	docker compose ps

reset-db:
	@$(MAKE) doctor
	docker compose down --remove-orphans
	@PROJECT_NAME=$${COMPOSE_PROJECT_NAME:-parser2}; \
	docker volume rm -f "$${PROJECT_NAME}_db_data" >/dev/null 2>&1 || true
	docker compose up -d db redis
	@echo "Waiting for DB..."
	@sleep 5
	docker compose run --rm api alembic upgrade head

migrate:
	@$(MAKE) doctor
	docker compose run --rm api alembic upgrade head

heads:
	@$(MAKE) doctor
	docker compose run --rm api alembic heads

current:
	@$(MAKE) doctor
	docker compose run --rm api alembic current

history:
	@$(MAKE) doctor
	docker compose run --rm api alembic history

test:
	@$(MAKE) doctor
	docker compose run --rm api pytest -q

seed:
	@$(MAKE) doctor
	docker compose run --rm api curl -sS -X POST http://api:8000/api/dev/seed

demo-seed:
	@$(MAKE) doctor
	./scripts/demo_seed.sh

selftest:
	./scripts/self_test.sh

db-shell:
	@$(MAKE) doctor
	docker compose exec db psql -U postgres -d ads

doctor:
	@bash scripts/doctor.sh

rotate-credentials:
	@$(MAKE) doctor
	docker compose run --rm api python -m app.cli rotate-credentials
