up:
	docker compose up --build

migrate:
	docker compose run --rm api alembic upgrade head

test:
	pytest
