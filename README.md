# RAG Assistant

Work in progress! A monorepo with FastAPI, Next.js, and Postgres (pgvector).

## Quick start

```bash
make up
```

Then:
- **Web:** http://localhost:3000
- **API:** http://localhost:8000
- **pgAdmin:** http://localhost:5050

## Migrations

After `make up`:
```bash
make db-migrate
```
Or locally: `cd apps/api && alembic upgrade head`

## First-time setup

Copy root `.env.example` to `.env` and set `PGADMIN_EMAIL` / `PGADMIN_PASSWORD` (required for deployment).
