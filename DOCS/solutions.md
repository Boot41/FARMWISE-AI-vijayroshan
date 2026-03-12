\# FarmWise AI — Agent Service Roadmap

This document describes what the `Agents/` service is being built to do,
how it is structured, and what each agent and its tools are responsible for.
It is written for a reviewer who wants to understand the full intended system
before looking at any code.

---

## What the Agent Service Does

The agent service is the reasoning layer of FarmWise AI. It receives a
farmer's `user_id` and their message from the backend, fetches its own
data via tools, and returns farming advice as plain text.

The service is built on Google ADK with Gemini 2.0 Flash. It runs as a
FastAPI app on port 8000. The backend calls `POST /agent/chat` and reads a
`reply` string from the response. That is the only contract.

**Key design principle:** The backend sends only `user_id`, `message`, and
`session_history`. The agent service fetches all other data — farmer profile,
weather, prices, documents — itself via tools. This means `adk web` and the
backend use an identical message format, which eliminates an entire class of
integration bugs.

---

## Overall Structure

The service has one orchestrator and five specialist agents. The orchestrator
receives every message, calls `get_user_context` to load the farmer's profile,
and routes to the correct specialist. Each specialist has its own tools that
fetch the data it needs to answer well.

```
POST /agent/chat
      │
      ▼
 Orchestrator  ──▶ get_user_context (always called first)
      │
      ├──▶ pest_agent        "My leaves have spots"
      ├──▶ irrigation_agent  "When should I water?"
      ├──▶ market_agent      "Should I sell now?"
      ├──▶ crop_agent        "What should I plant?"
      └──▶ advisory_agent    "What fertilizer should I use?"
```

The orchestrator also handles two things directly without routing:
- Non-farming questions (blocks them and redirects)
- Greetings and ambiguous messages (asks one clarifying question)

---

## Build Order

Each agent is built and tested fully before the next one starts.

```
Step 1 — Orchestrator + get_user_context tool
Step 2 — pest_agent          (first specialist, validates the pattern)
Step 3 — irrigation_agent
Step 4 — market_agent
Step 5 — crop_agent
Step 6 — advisory_agent
```

Each specialist is wired into the orchestrator's `sub_agents` as it is
completed. There is no separate wiring step — the orchestrator grows
incrementally.

---

## Orchestrator

**File:** `Agents/orchestrator/agent.py`

**What it does:**
Receives `user_id` and `message` from the backend, calls `get_user_context`
to load the farmer's profile, detects the intent, and routes to the correct
specialist.

**Sub-agents it routes to:**
`pest_agent`, `irrigation_agent`, `market_agent`, `crop_agent`, `advisory_agent`

**Handles directly:**
- Non-farming questions (politely blocked)
- Greetings and farewells
- Ambiguous messages (asks one clarifying question)

**Tools:**

| Tool | What it fetches |
|---|---|
| `get_user_context(user_id)` | Farmer profile from DB — name, crop, sowing date, irrigation type, water availability, region, soil type, climate zone |

**System prompt responsibilities:**
- Call `get_user_context` on every turn before doing anything else
- Detect intent from the message and conversation history
- Route to the right specialist with full farmer context
- Never generate specialist advice itself

---

## pest_agent

**File:** `Agents/pest_agent/agent.py`

**What it does:**
Diagnoses pest and disease problems from symptom descriptions. Returns the
pest name, treatment, dosage, spray frequency, an organic alternative, and a
weather-aware spray warning.

**Why it needs its own agent:**
Pest diagnosis requires matching natural language symptoms against a pest
guide, then cross-referencing an approved pesticide catalog, then checking
the weather before recommending spray timing. No other agent does this.

**Tools:**

| Tool | What it fetches |
|---|---|
| `get_pest_guide(crop)` | Reads `docs/pest_guides/{crop}.md` — symptoms, treatments, organic options |
| `get_pesticide_reference()` | Reads `docs/pesticide_reference/approved_pesticides.md` — dosages, waiting periods |
| `get_weather_forecast(region_id)` | 7-day forecast from DB — used to warn against spraying before rain |

**Key behaviours the LLM must produce:**
- Always check weather before recommending spray timing
- Always include an organic alternative even if not asked
- Give a date-specific spray warning if rain is forecast within 48 hours
- Never diagnose human health conditions

---

## irrigation_agent

**File:** `Agents/irrigation_agent/agent.py`

**What it does:**
Advises on when and how much to water based on the crop's current growth
stage, the farmer's irrigation type, and the upcoming weather forecast.

**Why it needs its own agent:**
Irrigation advice requires knowing the crop's growth stage, derived from
the sowing date in the farmer's profile. A tomato at 28 days needs different
water than the same crop at 65 days. This calculation is specific to
irrigation and does not belong in a general agent.

**Tools:**

| Tool | What it fetches |
|---|---|
| `get_crop_calendar(state)` | Reads `docs/crop_calendars/{state}.md` — growth stages, water requirements per stage |
| `get_weather_forecast(region_id)` | 7-day forecast from DB — used to skip irrigation on rain days |

**Key behaviours the LLM must produce:**
- Calculate days since sowing from `sowing_date` in the farmer's profile
- Map days since sowing to the correct growth stage from the crop calendar
- Adapt advice to `irrigation_type`: drip → litres per plant, flood → days between irrigation
- Skip irrigation on days with significant rainfall forecast
- Give specific dates, not generic intervals

---

## market_agent

**File:** `Agents/market_agent/agent.py`

**What it does:**
Advises on whether now is a good time to sell based on the current mandi
price, a 7-day price trend, and the seasonal advisory's market outlook.

**Why it needs its own agent:**
Market timing is independent of all other farming operations. The key insight
is trend over spot price — ₹1,200 today means something completely different
if prices were ₹900 a week ago versus ₹1,800. No other agent needs this
reasoning.

**Tools:**

| Tool | What it fetches |
|---|---|
| `get_mandi_prices(region_id, crop_name)` | Last 7 days of prices from DB — used to calculate trend |
| `get_advisory(season, year)` | Reads `docs/advisories/{season}_{year}.md` — seasonal market outlook |

**Key behaviours the LLM must produce:**
- Always calculate and report the 7-day price trend, not just today's price
- Mention MSP if the crop has one — farmers should not sell below it
- Combine trend data with the advisory's seasonal outlook for a forward-looking recommendation
- Never give crop planning or pest advice

---

## crop_agent

**File:** `Agents/crop_agent/agent.py`

**What it does:**
Recommends what crop to plant next based on the region's suitability scores,
the crop calendar's sowing windows, current mandi prices, and the seasonal
advisory. Returns crop name, sowing window, harvest window, water requirement,
cost estimate, expected yield, and expected revenue.

**Why it needs its own agent:**
Crop planning draws on more data sources than any other agent — suitability
scores, calendar documents, live prices, and seasonal advisory all at once.
Isolating it keeps that complexity contained and independently improvable.

**Tools:**

| Tool | What it fetches |
|---|---|
| `get_region_crops(region_id)` | Suitability scores from DB — what grows well in this region |
| `get_crop_calendar(state)` | Reads `docs/crop_calendars/{state}.md` — sowing windows, harvest windows |
| `get_mandi_prices(region_id)` | Current prices from DB — economic filter on top of agronomic fit |
| `get_advisory(season, year)` | Reads `docs/advisories/{season}_{year}.md` — seasonal crop outlook |

**Key behaviours the LLM must produce:**
- Recommend crops that are both agronomically suitable AND economically sensible
- Use the crop calendar for state-specific sowing windows, not generic dates
- Include cost and revenue estimates — farmers need to know if it pencils out
- Never give irrigation or pest advice

---

## advisory_agent

**File:** `Agents/advisory_agent/agent.py`

**What it does:**
Answers questions about fertilizers, NPK schedules, government schemes,
subsidies, organic farming, water conservation, and general seasonal guidance.
Searches FarmWise's curated document library to ground every answer in actual
document content rather than model memory.

**Why it needs its own agent:**
The four specialist agents cover specific farming operations. A large category
of farming knowledge — NPK ratios, PM-KISAN, PMKSY subsidies, soil amendments,
organic practices, seasonal outlooks — does not fit any of them. Rather than
expanding every specialist's scope, advisory_agent handles this with dynamic
document search. The documents contain specific curated figures (exact subsidy
percentages, scheme deadlines, fertilizer split schedules) that the model
cannot reliably recall.

**Tools:**

| Tool | What it fetches |
|---|---|
| `search_docs(query)` | Scores `docs/index.json` chunks against the query by keyword overlap, returns top 5 matching chunks |
| `get_advisory(season, year)` | Reads `docs/advisories/{season}_{year}.md` — full seasonal advisory for scheme and outlook questions |

**Key behaviours the LLM must produce:**
- Always call `search_docs` before answering — never answer from model memory alone
- For fertilizer questions: return NPK ratio, split application schedule, and key micronutrient
- For scheme questions: return scheme name, benefit, eligibility, and how to apply
- If the question belongs to a specialist (e.g. "when should I water?"), redirect cleanly
- If documents don't cover something, say so and suggest the nearest KVK

---

## Document Library

All documents live in `Agents/docs/`. Every agent that reads documents uses
the markdown version. `index.json` is the retrieval manifest used by
`advisory_agent`'s `search_docs` tool.

```
docs/
├── index.json                          ← chunk index for advisory_agent search
├── crop_calendars/
│   ├── kerala.md + kerala.pdf
│   ├── maharashtra.md + maharashtra.pdf
│   ├── punjab.md + punjab.pdf
│   ├── rajasthan.md + rajasthan.pdf
│   └── tamil_nadu.md + tamil_nadu.pdf
├── pest_guides/                        ← MD only
│   └── bajra, coconut, groundnut, maize, mustard,
│       onion, pepper, rice, tomato, wheat
├── pesticide_reference/
│   └── approved_pesticides.md + approved_pesticides.pdf
└── advisories/
    ├── kharif_2024.md + kharif_2024.pdf
    └── rabi_2024.md + rabi_2024.pdf
```

---

## What the Reviewer Should See When It Is Complete

1. `POST /agent/chat` accepts `user_id`, `message`, and `session_history` — nothing else — and returns `{"reply": "..."}` within 15 seconds
2. The same message format works identically in `adk web` and from the backend
3. Each specialist fetches its own data via tools — the backend sends no context payload
4. Farming questions are routed to the correct specialist
5. Each specialist grounds its answer in real data returned by its tools — not LLM memory
6. Non-farming questions are blocked at the orchestrator
7. Session history is used to resolve follow-up messages correctly
8. Guardrails hold: system prompt is never revealed, prompt injection is refused
