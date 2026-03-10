# FarmWise AI Frontend Spec

## Overview

The frontend lives in `client/` and is a small React 18 + TypeScript application built with Vite.
It is intentionally light on architecture and uses local component state, React Router, Axios, and Tailwind CSS.

The frontend talks only to the backend API on `http://localhost:8010`.
It does not call the agent service directly.

## Runtime

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8010`
- Agent service: `http://localhost:8001`

The frontend reads `VITE_API_BASE_URL` from `client/.env` or `client/.env.example`.
The current example value is:

```env
VITE_API_BASE_URL=http://localhost:8010
```

## Tech Stack

- React 18
- TypeScript
- Vite
- React Router v6
- Axios
- Tailwind CSS

## Current Structure

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

## Routing

Current routes:

- `/`
  redirects to `/dashboard` if authenticated, otherwise `/login`
- `/login`
  login and registration page
- `/dashboard`
  protected dashboard
- `/chat`
  protected chat experience

Route protection is implemented in `src/App.tsx` using `isAuthenticated()` from `src/lib/auth.ts`.

## Auth Model

Authentication tokens are stored in memory only.
They are not persisted in `localStorage`, `sessionStorage`, or cookies.

The auth module in `src/lib/auth.ts` exposes:

- `setTokens`
- `getAccessToken`
- `getRefreshToken`
- `clearTokens`
- `isAuthenticated`

Implications:

- a full page reload clears the session
- route guards depend on the current in-memory access token
- redirect-to-login on session loss is expected behavior

## API Layer

All frontend API access goes through `src/lib/api.ts`.
Components and pages should not create their own Axios instances or call `fetch()` directly.

The file currently provides:

- typed API response interfaces
- typed models for user, region, weather, mandi prices, crops, chat sessions, chat messages, and structured card data
- a shared Axios client
- request interceptor for `Authorization: Bearer <access_token>`
- response interceptor for one-time refresh on `401`
- redirect to `/login` if refresh fails

The backend response envelope is assumed to be:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Error messaging is derived from `response.data.message`.
Actual payloads are taken from `response.data.data`.

## Pages

### Login

`src/pages/Login.tsx`

Responsibilities:

- toggles between login and register modes
- loads regions for the register form
- stores access and refresh tokens in memory after success
- redirects to `/dashboard`
- shows inline backend error messages

Register form fields currently include:

- name
- email
- phone optional
- password
- region select

### Dashboard

`src/pages/Dashboard.tsx`

Responsibilities:

- loads the authenticated user with `getMe()`
- loads weather, mandi prices, and region crops for the user’s region
- shows logout action
- links to `/chat`
- displays the mandi ticker

Rendered sections:

- header with user and region
- weather widget
- mandi price widget
- region crop suitability widget
- continuously scrolling CSS ticker

### Chat

`src/pages/Chat.tsx`

Responsibilities:

- loads chat sessions
- auto-loads the latest session when one exists
- loads a selected session’s message history
- starts new blank chats
- sends messages to `POST /api/chat/message`
- reloads session history after successful replies
- auto-scrolls to the bottom
- shows spinner-based waiting states

The chat page uses only local state.
No external state library is currently involved.

## Components

### Chat Components

- `SessionSidebar`
  renders session list and active session selection
- `ChatInput`
  expanding textarea, enter-to-send, shift-enter for newline
- `ChatMessage`
  handles user bubbles, assistant bubbles, and structured card selection
- `Spinner`
  shared loading indicator used in chat send/history states

### Dashboard Components

- `WeatherWidget`
  7-day forecast list with rainfall icon when rain is above threshold
- `PriceWidget`
  mandi price list with recorded date
- `RegionCropsWidget`
  suitability bars for regional crops

### Structured Assistant Cards

- `CropAdvisoryCard`
- `PestDiagnosisCard`
- `MarketTimingCard`
- `IrrigationCard`

These are rendered only when assistant `message_metadata` is explicitly structured and the `intent` matches a supported type.

## Chat Metadata Handling

The frontend is built to support rich assistant card rendering, but it is defensive by default.

Current behavior in `ChatMessage.tsx`:

- user message: right-aligned green bubble
- assistant message without structured metadata: plain text bubble
- assistant message with structured metadata: intent-specific card

Supported intents:

- `crop_recommendation`
- `pest_diagnosis`
- `market_timing`
- `irrigation_schedule`

Important current limitation:

- the backend currently stores assistant messages with minimal metadata, typically just source information
- because of that, most assistant responses render as plain text today
- the card UI is ready for future richer metadata from the backend or agent layer

## Styling

Styling is done with Tailwind CSS and a small amount of global CSS in `src/index.css`.

Important current styling choices:

- dark stone/emerald visual palette
- simple rounded card surfaces
- no MUI usage in the implemented app
- no separate CSS modules or component CSS files

The mandi ticker animation is defined in `src/index.css`.
It is CSS-only and duplicates the ticker content to create a seamless loop.

## Developer Commands

From `client/`:

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
npm run build
npm run lint
```

## Change Guidance

When extending the frontend:

- keep API concerns in `src/lib/api.ts`
- keep token concerns in `src/lib/auth.ts`
- keep pages responsible for route-level data loading
- keep components mostly presentational
- do not add persistence for auth tokens unless the requirement changes
- do not add direct calls to the agent service from the client
- if structured chat metadata changes, update the typed interfaces and `ChatMessage.tsx` together
