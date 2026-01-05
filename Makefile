.PHONY: up down reset-db migrate heads current history test seed selftest db-shell

up:
	docker compose up -d db redis api worker

down:
	docker compose down --volumes

reset-db:
	docker compose down --volumes
	docker compose up -d db redis
	@echo "Waiting for DB..."
	@sleep 5
	docker compose run --rm api alembic upgrade head

migrate:
	docker compose run --rm api alembic upgrade head

heads:
	docker compose run --rm api alembic heads

current:
	docker compose run --rm api alembic current

history:
	docker compose run --rm api alembic history

test:
	docker compose run --rm api pytest -q

seed:
	docker compose run --rm api curl -sS -X POST http://api:8000/api/dev/seed

selftest:
	./scripts/self_test.sh

db-shell:
	docker compose exec db psql -U postgres -d ads
