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

## Demo gate & API access

When `DEMO_KEY` is set, all non-public routes require an `x-demo-key` header. `/health` stays public.

**Set DEMO_KEY** (in `apps/api/.env` or docker-compose `environment`):
```
DEMO_KEY=your-secret-key
```

**Test with curl:**
```bash
# Public (no key needed)
curl http://localhost:8000/health

# Protected (requires key)
curl -X POST http://localhost:8000/ask \
  -H "x-demo-key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query":"hello"}'
```

## Rate limits

| Route | Limit |
|-------|-------|
| POST /ask | 10/hour |
| POST /documents/ingest | 3/day |
| POST /documents/presign | 10/day |

429 responses include `retry_after_seconds`. Pass `x-user-id` for per-user limits.
