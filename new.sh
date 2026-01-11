docker compose up -d --build
docker compose run --rm api alembic upgrade head
make test
make selftest
docker compose run --rm web npm run build