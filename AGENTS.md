# FarmWise AI

## Overview

FarmWise AI is an agricultural advisory platform split across three services:

- `client/` provides the frontend experience.
- `server/` is the backend API and persistence layer.
- `Agents/` is the separate reasoning service.

The backend exists to manage structured data and session state. It should never implement AI reasoning. Its job is to collect authenticated user context, regional agricultural data, weather, mandi prices, and chat history, then forward that context to the agent service.

## Local Runtime

- Backend API runs on `http://localhost:8010`
- PostgreSQL runs on `localhost:5433`
- Agent service is expected on `http://localhost:8001`
- Frontend runs on `http://localhost:5173`

## PostgreSQL Access

- URL: `postgresql+asyncpg://user:password@localhost:5433/farmwise`
- Username: `user`
- Password: `password`

## Backend Scope

The backend in `server/` owns:

- users and authentication
- regional metadata
- region-specific crops
- weather forecast records
- mandi price records
- chat sessions and chat messages
- refresh token persistence
- outbound HTTP calls to `AGENT_SERVICE_URL/agent/chat`

The backend does not own:

- agricultural reasoning
- prompt engineering logic
- retrieval logic over agricultural documents
- LLM or ADK orchestration

If a future change starts embedding reasoning in FastAPI, that is a design regression.

## Current Backend Structure

```text
server/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── data.py
│   │   ├── farms.py
│   │   ├── health.py
│   │   └── router.py
│   ├── auth/
│   │   └── jwt.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/
│   │   ├── models.py
│   │   ├── seed.py
│   │   └── session.py
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── error_handler.py
│   │   └── request_logging.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── common.py
│   │   ├── data.py
│   │   └── farm.py
│   ├── services/
│   │   ├── agent_client.py
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   ├── data_service.py
│   │   └── user_service.py
│   └── main.py
├── alembic/
├── tests/
├── .env
├── .env.example
└── pyproject.toml
```

## Data Model Summary

The main tables are:

- `users`
- `regions`
- `region_crops`
- `weather_forecasts`
- `mandi_prices`
- `chat_sessions`
- `chat_messages`
- `refresh_tokens`

All core IDs are UUIDs. Async SQLAlchemy is used throughout.

## Response Contract

Successful responses use a consistent envelope:

```json
{
  "success": true,
  "message": "Human readable message",
  "data": {}
}
```

Errors are normalized to:

```json
{
  "success": false,
  "message": "Error message",
  "data": null
}
```

## API Inventory

All backend routes are mounted under `/api`.

### Health Endpoint

- `GET /api/health`
  Returns a simple health payload used for service checks.

### Auth Endpoints

- `POST /api/auth/register`
  Creates a new user linked to a region and returns access plus refresh tokens.
- `POST /api/auth/login`
  Authenticates by email and password and returns fresh tokens.
- `POST /api/auth/refresh`
  Validates a stored refresh token and returns a new access token.
- `POST /api/auth/logout`
  Revokes the submitted refresh token.

### User Endpoints

- `GET /api/users/me`
  Returns the authenticated user profile with nested region data.
- `PATCH /api/users/me`
  Updates `water_availability`, `irrigation_type`, and `current_crop`.

### Data Endpoints

- `GET /api/data/regions`
  Returns all regions.
- `GET /api/data/regions/{region_id}/weather`
  Returns the latest 7 weather forecast rows for the region.
- `GET /api/data/regions/{region_id}/prices`
  Returns the latest mandi price per crop for the region.
- `GET /api/data/regions/{region_id}/crops`
  Returns crop suitability rows for the region.

### Chat Endpoints

- `POST /api/chat/message`
  Accepts a user message, creates a session if needed, builds backend context, forwards it to the agent service, and stores both the user and assistant messages.
- `GET /api/chat/sessions`
  Returns all chat sessions owned by the authenticated user.
- `GET /api/chat/sessions/{session_id}`
  Returns the selected session and full message history.

## Chat Request Flow

`POST /api/chat/message` is the most important backend endpoint.

What it does:

- validates the authenticated user
- creates a new chat session if `session_id` is absent
- loads the user’s region
- loads latest weather rows for that region
- loads latest mandi prices per crop
- loads regional crop suitability rows
- loads prior session history if the session already exists
- builds the structured payload for `AGENT_SERVICE_URL/agent/chat`
- stores the user message and assistant reply in `chat_messages`

The backend only forwards context. It does not decide the answer itself.

## Developer Commands

From [`server/`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/server):

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
uv run --extra dev pytest -q
```

From the repo root:

```bash
docker compose up -d db
```

## Seed Data Notes

The seed script inserts:

- 5 regions with realistic crop, weather, and mandi price data
- demo users for each region
- demo password: `pass123`

## Guidance For Future Codex Work

- Keep business logic in `app/services/`, not inside route handlers.
- Keep auth logic in `app/auth/jwt.py`.
- Keep schemas in `app/schemas/`.
- Do not add reasoning logic to the backend.
- If the agent payload contract changes, update `app/services/agent_client.py` and `app/services/chat_service.py`, not the DB schema unless the stored chat model also changes.
- Keep documentation free of sensitive environment values.
- Run the configured pre-commit hooks before creating a commit.
- When creating a commit, use a proper title that clearly describes the change scope and intent.
- When creating a pull request, use a proper title and description that summarize what changed, why it changed, and any important verification notes.
