.PHONY: up down logs db-migrate build clean

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

db-migrate:
	docker compose exec api alembic upgrade head

build:
	docker compose build

test:
	cd apps/api && pytest -v

test-docker:
	docker compose build api && docker compose run --rm api sh -c "alembic upgrade head && python -m pytest -v"

clean:
	docker compose down -v
