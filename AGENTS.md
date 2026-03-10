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

## Frontend Scope

The frontend in `client/` is intentionally small.
It owns:

- login and registration UI
- protected routing for `/dashboard` and `/chat`
- in-memory token handling in the browser
- data fetching from the backend API
- dashboard presentation for weather, mandi prices, and region crops
- chat session browsing and chat message rendering
- fallback rendering for plain-text assistant responses

The frontend does not own:

- persistence of auth tokens beyond the current page lifetime
- direct calls to the agent service
- business logic that belongs in FastAPI services
- AI reasoning or prompt logic

If a future change starts duplicating backend rules or embedding agent orchestration in React, that is a design regression.

## Current Frontend Structure

```text
client/
├── src/
│   ├── App.tsx
│   ├── index.css
│   ├── main.tsx
│   ├── pages/
│   │   ├── Chat.tsx
│   │   ├── Dashboard.tsx
│   │   └── Login.tsx
│   ├── components/
│   │   ├── Spinner.tsx
│   │   ├── cards/
│   │   │   ├── CropAdvisoryCard.tsx
│   │   │   ├── IrrigationCard.tsx
│   │   │   ├── MarketTimingCard.tsx
│   │   │   └── PestDiagnosisCard.tsx
│   │   ├── chat/
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── SessionSidebar.tsx
│   │   └── dashboard/
│   │       ├── PriceWidget.tsx
│   │       ├── RegionCropsWidget.tsx
│   │       └── WeatherWidget.tsx
│   └── lib/
│       ├── api.ts
│       └── auth.ts
├── .env.example
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── vite.config.ts
```

## Frontend Routing

The current routes are:

- `/`
  redirects to `/dashboard` when authenticated, otherwise `/login`
- `/login`
  public route for login and registration
- `/dashboard`
  protected route for the regional overview
- `/chat`
  protected route for chat sessions and agent interaction

Protection is implemented in `client/src/App.tsx` using `isAuthenticated()` from `client/src/lib/auth.ts`.
Because tokens are memory-only, a full browser reload returns the user to `/login`.

## Frontend Auth Model

The auth store is module-local state in `client/src/lib/auth.ts`.

What exists now:

- `setTokens(access, refresh)`
- `getAccessToken()`
- `getRefreshToken()`
- `clearTokens()`
- `isAuthenticated()`

Important constraints:

- no `localStorage`
- no `sessionStorage`
- no cookie-based session handling in the client

`client/src/lib/api.ts` attaches the access token on every request.
On a `401`, it attempts `POST /api/auth/refresh` once using the in-memory refresh token.
If refresh fails, tokens are cleared and the browser is redirected to `/login`.

## Frontend API Integration

All client-side API calls go through `client/src/lib/api.ts`.
Do not introduce direct `fetch()` or standalone `axios` calls inside pages or components.

The frontend assumes the backend response envelope:

```json
{
  "success": true,
  "message": "Human readable message",
  "data": {}
}
```

Actual payloads are read from `response.data.data`.
User-facing errors are derived from `response.data.message`.

Typed helper functions currently exported from `client/src/lib/api.ts` include:

- `login`
- `register`
- `logout`
- `getMe`
- `getRegions`
- `getWeather`
- `getPrices`
- `getRegionCrops`
- `sendMessage`
- `getSessions`
- `getSessionMessages`
- `getApiErrorMessage`

## Current Frontend Behavior

### Login Page

`client/src/pages/Login.tsx` supports both login and registration in one card.

Current behavior:

- registration preloads regions from `GET /api/data/regions`
- successful login or registration stores the returned access and refresh tokens in memory
- success redirects to `/dashboard`
- backend envelope errors are shown inline

### Dashboard Page

`client/src/pages/Dashboard.tsx` loads:

- `GET /api/users/me`
- `GET /api/data/regions/{region_id}/weather`
- `GET /api/data/regions/{region_id}/prices`
- `GET /api/data/regions/{region_id}/crops`

The page currently includes:

- welcome header with user and region info
- logout action
- CTA to `/chat`
- `WeatherWidget`
- `PriceWidget`
- `RegionCropsWidget`
- CSS-only looping mandi ticker at the bottom

The ticker is implemented in `client/src/index.css` and duplicates the text content to create a seamless loop.

### Chat Page

`client/src/pages/Chat.tsx` currently:

- loads existing sessions with `GET /api/chat/sessions`
- auto-loads the first session if one exists
- loads session detail with `GET /api/chat/sessions/{session_id}`
- starts a blank conversation when `New Chat` is pressed
- sends messages with `POST /api/chat/message`
- refreshes the session history after each successful send
- scrolls to the bottom when content changes
- shows spinner-based loading states for history fetches and message sends

The page is intentionally simple state-wise and uses only local React state.
Do not introduce Redux, Zustand, React Query, or other client state infrastructure unless there is a clear new requirement.

## Chat Rendering Contract

`client/src/components/chat/ChatMessage.tsx` handles assistant messages defensively.

Current logic:

- user messages always render as right-aligned bubbles
- assistant messages render as plain text by default
- if `message_metadata.structured === true` and `message_metadata.intent` is known, the relevant card component is used

Supported structured intents:

- `crop_recommendation`
- `pest_diagnosis`
- `market_timing`
- `irrigation_schedule`

Current backend reality:

- the backend presently stores assistant messages with minimal metadata like `{"source": "agent_service"}`
- this means the frontend mostly renders plain assistant bubbles today
- the structured cards are implemented and ready, but they depend on richer `message_metadata`

If that metadata contract changes, update `client/src/lib/api.ts`, `client/src/components/chat/ChatMessage.tsx`, and the card prop types together.

## Frontend Developer Commands

From [`client/`](/home/think41/WEEK_4_PROJECT/FarmWise_AI/client):

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
npm run build
npm run lint
```

## Guidance For Future Codex Work

- Keep API types and API calls in `client/src/lib/api.ts`.
- Keep token logic in `client/src/lib/auth.ts`.
- Keep route-level data loading inside page components.
- Keep presentational widgets and cards in `client/src/components/`.
- Preserve the memory-only auth behavior unless the product requirement explicitly changes.
- Do not add direct client calls to `http://localhost:8001`; the frontend should only talk to the backend API.
- If you change the visual system, preserve the current minimal Tailwind setup instead of reintroducing MUI or another UI framework without a requirement.
- If you add new structured chat cards, update both the intent switch and the typed card data shapes.

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
