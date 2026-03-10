# FarmWise AI

FarmWise AI is split into three layers:

- `client/` for the frontend
- `server/` for the FastAPI backend
- `Agents/` for the separate reasoning service

The backend only manages authentication, regional data, weather, mandi prices, and chat history. It does not perform AI reasoning.

## Local Ports

- Backend API: `http://localhost:8010`
- Agent service: `http://localhost:8001`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5433`

## PostgreSQL

- URL: `postgresql+asyncpg://user:password@localhost:5433/farmwise`
- Username: `user`
- Password: `password`

## Quick Start

From the repo root:

```bash
docker compose up -d db
```

## Frontend Only

The frontend runs on `http://localhost:5173`.

From [`client/`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/client):

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

The client expects the backend API on `http://localhost:8010` by default via `VITE_API_BASE_URL`.
Authentication is handled fully in the browser with in-memory access and refresh tokens, so refreshing the page clears the current session.

From [`server/`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/server):

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Run backend tests from [`server/`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/server):

```bash
uv run --extra dev pytest -q
```

Seeded demo users use password `pass123`.

High level developer notes:

- `client/` is a small React 18 + TypeScript + Vite app using React Router and Tailwind CSS.
- `server/` is the FastAPI app that owns auth, regional data, weather, mandi prices, and chat persistence.
- `Agents/` is the separate reasoning service. The backend forwards chat context there; it does not generate advice itself.

For backend details, see [`DOCS/backend.md`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/DOCS/backend.md). For frontend details, see [`DOCS/frontend-spec.md`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/DOCS/frontend-spec.md). For Codex-specific repo context, see [`AGENTS.md`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/AGENTS.md).
