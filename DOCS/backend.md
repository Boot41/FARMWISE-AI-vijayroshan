# Backend Documentation

## Overview

The FarmWise backend is a FastAPI service that manages authentication, regional agricultural data, weather, mandi prices, and chat persistence. It forwards structured context to the external agent service and stores the resulting assistant response.

Base URL in local development: `http://localhost:8010`

API prefix: `/api`

## Local Dependencies

- PostgreSQL: `localhost:5433`
- Agent service: `http://localhost:8001`

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/farmwise
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
AGENT_SERVICE_URL=http://localhost:8001
```

## Response Shape

### Success

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

### Error

```json
{
  "success": false,
  "message": "Something failed",
  "data": null
}
```

## Authentication

- Access tokens use JWT with `HS256`
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days
- Refresh tokens are stored in `refresh_tokens`
- Logout revokes the stored refresh token

Protected routes require `Authorization: Bearer <access_token>`.

## Endpoints

### Health

`GET /api/health`

Returns service health.

### Auth

`POST /api/auth/register`

Request:

```json
{
  "name": "Farmer Name",
  "email": "farmer@example.com",
  "password": "pass123",
  "phone_number": "9999999999",
  "region_id": "uuid"
}
```

Behavior:

- validates that the region exists
- ensures email uniqueness
- hashes the password
- creates the user
- issues access and refresh tokens
- stores refresh token in DB

`POST /api/auth/login`

Request:

```json
{
  "email": "farmer@example.com",
  "password": "pass123"
}
```

Behavior:

- validates email and password
- issues new access and refresh tokens
- stores refresh token in DB

`POST /api/auth/refresh`

Request:

```json
{
  "refresh_token": "jwt"
}
```

Behavior:

- validates JWT signature
- checks token is stored, not revoked, and not expired
- returns a new access token

`POST /api/auth/logout`

Request:

```json
{
  "refresh_token": "jwt"
}
```

Behavior:

- marks the stored refresh token as revoked

### User

`GET /api/users/me`

Returns the authenticated user profile plus nested region details.

`PATCH /api/users/me`

Request:

```json
{
  "water_availability": "Moderate",
  "irrigation_type": "Drip",
  "current_crop": "Groundnut"
}
```

Behavior:

- updates only the editable profile farming fields

### Data

`GET /api/data/regions`

Returns all regions.

`GET /api/data/regions/{region_id}/weather`

Returns the latest 7 weather forecast rows for that region.

`GET /api/data/regions/{region_id}/prices`

Returns the latest mandi price row per crop for that region.

`GET /api/data/regions/{region_id}/crops`

Returns crop suitability rows for the region.

### Chat

`POST /api/chat/message`

Protected route.

Request:

```json
{
  "session_id": "optional-uuid",
  "message": "Should I irrigate this week?"
}
```

Behavior:

- creates a new `chat_session` if `session_id` is missing
- loads the current user and region
- loads latest weather, mandi prices, and regional crop suitability
- loads prior chat history if the session already exists
- builds a structured context payload
- sends it to `AGENT_SERVICE_URL/agent/chat`
- saves the user message and assistant reply to `chat_messages`

Agent payload shape:

```json
{
  "message": "Should I irrigate this week?",
  "session_history": [
    {
      "role": "user",
      "message_text": "Earlier message"
    }
  ],
  "context": {
    "state": "Tamil Nadu",
    "district": "Chennai",
    "dominant_soil_type": "Red Laterite",
    "water_availability": "Tank irrigation",
    "irrigation_type": "Flood",
    "current_crop": "Paddy",
    "season_crops": [],
    "weather": [],
    "mandi_prices": []
  }
}
```

If the agent service is unreachable, the backend returns `503`.

`GET /api/chat/sessions`

Protected route.

Returns all sessions for the authenticated user ordered by recent activity.

`GET /api/chat/sessions/{session_id}`

Protected route.

Returns the session plus full stored message history.

## Database Tables

The backend currently manages these main tables:

- `users`
- `regions`
- `region_crops`
- `weather_forecasts`
- `mandi_prices`
- `chat_sessions`
- `chat_messages`
- `refresh_tokens`

The current SQLAlchemy models live in [`server/app/db/models.py`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/server/app/db/models.py).

## Seed Data

Seed command:

```bash
cd server
uv run python -m app.db.seed
```

What it seeds:

- Tamil Nadu / Chennai / Cauvery Delta
- Maharashtra / Nashik / Deccan Plateau
- Punjab / Ludhiana / Punjab Plains
- Kerala / Thrissur / Malabar Coast
- Rajasthan / Jaipur / Thar Desert

Also included:

- crop suitability records
- 7 weather forecast rows per region
- mandi prices per region
- demo users

Demo password for seeded users: `pass123`

## Developer Workflow

### Start PostgreSQL

```bash
docker compose up -d db
```

### Apply Migrations

```bash
cd server
uv run alembic upgrade head
```

### Seed Data

```bash
cd server
uv run python -m app.db.seed
```

### Run Backend

```bash
cd server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### Run Tests

```bash
cd server
uv run --extra dev pytest -q
```

## Verified State

Verified during this update:

- backend tests pass
- seed command completes against the local PostgreSQL compose database
