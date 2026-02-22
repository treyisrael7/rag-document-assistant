.PHONY: up down logs db-migrate build clean

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

db-migrate:
	docker compose exec api python -c "print('DB migrations placeholder - add alembic or similar')"

build:
	docker compose build

clean:
	docker compose down -v
