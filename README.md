---
title: MarketMate
emoji: 🥦
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# MarketMate

AI ordering assistant for a Melbourne fresh produce retailer.

**Live demo:** https://marketmate.up.railway.app

---

## Problem

Ordering decisions at a Melbourne produce shop are locked inside one experienced manager's head. When that manager is unavailable, untrained staff over-order causing spoilage or under-order causing stockouts.

The shop does **$85,000 AUD per week** total, with **$50,000 from produce**. A 5% ordering error on produce costs $2,500 per week - $130,000 annualised in avoidable waste or lost sales.

MarketMate learns from a full year of daily sales data across 28 produce items and replicates the manager's ordering instincts for any staff member, any day of the week. It answers natural language queries in the voice of an experienced produce manager, grounded in your actual historical numbers.

---

## Architecture

```
Browser (React + Vite)
    |
    | SSE stream / POST
    v
FastAPI (Python 3.11)
    |
    | LangGraph StateGraph (7 nodes)
    v
+-------------------+------------------+------------------+
| sales_retriever   | holiday_checker  | spoilage_scorer  |
| ChromaDB RAG      | Hardcoded VIC    | CSV velocity +   |
| 51-week history   | holidays 2026    | spoilage ratio   |
| ~1,428 documents  | + event impacts  |                  |
+-------------------+------------------+------------------+
+-------------------+------------------+
| demand_forecaster | order_generator  |
| Linear regression | Claude API       |
| + rolling avg     | structured JSON  |
| per-item forecast | order table      |
+-------------------+------------------+
    |
    v
Claude claude-sonnet-4-6 (response synthesis)
Current date/time injected into every LLM call
```

---

## Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Backend     | Python 3.11, FastAPI 0.115, uvicorn                 |
| AI agent    | LangGraph 0.2, LangChain Core 0.2.43                |
| LLM         | Anthropic Claude claude-sonnet-4-6                  |
| Vector DB   | ChromaDB 0.5 (local persistent)                     |
| Embeddings  | sentence-transformers all-MiniLM-L6-v2 (local)      |
| Forecasting | numpy linear regression + pandas rolling averages   |
| Data        | pandas 2.2, openpyxl 3.1, 51-week produce sales CSV |
| Frontend    | React 18, Vite 5, Tailwind CSS 3                    |
| Streaming   | Server-Sent Events (SSE)                            |
| Container   | Docker multi-stage, docker-compose                  |
| CI          | GitHub Actions (backend + frontend)                 |
| Deploy      | Railway (backend), nginx (frontend)                 |

---

## How It Works

### RAG Pipeline

On startup, MarketMate reads `produce_sales.csv` and ingests it into ChromaDB as weekly summary documents. Each document describes one item for one week: total quantity sold, daily average, peak day, trend vs previous week, spoilage window, holiday context, and revenue.

The current dataset covers **51 weeks, 28 items, 9,996 rows** calibrated to $50,000 AUD weekly produce revenue. ChromaDB holds approximately 1,428 documents.

When a user asks a question, `sales_retriever` embeds the query using `all-MiniLM-L6-v2` (runs locally, no API key needed) and retrieves the 4 most relevant weekly records. This is the manager's memory - historical patterns the LLM reasons over.

### LangGraph Agent

The agent is a `StateGraph` with 7 nodes:

1. **query_router** - analyses the query and sets routing flags
2. **sales_retriever_node** - always runs, fetches RAG context from ChromaDB
3. **demand_forecaster_node** - runs for trend/forecast/prediction queries; uses statistical model
4. **holiday_checker_node** - runs if the query mentions dates, events, or weekends
5. **spoilage_scorer_node** - runs if the query mentions leftover stock or waste
6. **order_generator_node** - runs if the query asks for an order recommendation
7. **response_synthesiser** - all paths converge here; calls Claude with all context

Every LLM call receives the **current date, time, day name, and week number** injected into the prompt, so Claude can never confuse day names or misidentify the trading window.

Each node appends to `agent_trace`, which streams to the frontend in real time.

### Learning Pipeline

MarketMate improves as you log more data. Every time you log sales, three things happen:

```
Sales logged (manual or Excel upload)
          |
          v
Rows appended to produce_sales.csv
          |
          v
run_ingestion() re-indexes ChromaDB
(collection grows over time)
          |
          v
demand_forecaster cache invalidated
(next query uses fresh data)
```

After 4 weeks of real data, demand forecasts reach Medium confidence. After 8 weeks, High confidence on stable items. After 52 weeks, seasonal patterns are confirmed by real observed data rather than generated baselines.

---

## The Five Tools

| Tool                  | Purpose                                                                    |
|-----------------------|----------------------------------------------------------------------------|
| `sales_retriever`     | RAG over 51-week ChromaDB collection. Core of the manager's memory.       |
| `demand_forecaster`   | Statistical demand prediction: linear regression + 4/8-week rolling avg.  |
| `holiday_checker`     | Returns VIC 2026 public holiday and event data with trade impact %s.       |
| `spoilage_scorer`     | Calculates spoilage risk ratio and velocity for a specific item.           |
| `order_generator`     | Uses Claude to produce structured JSON order recommendation + text table.  |

---

## Demo Mode vs Live AI Mode

The UI header has a toggle to switch modes at runtime without restarting the server.

| | Demo Mode | Live AI Mode |
|---|---|---|
| Queries answered | 6 preset only | Any question |
| Response source | Pre-written strings | Claude API |
| Agent trace | Fake, hardcoded | Real tool calls |
| Cost | $0 | ~$0.01-0.05 per query |
| Works offline | Yes | No |
| Date awareness | N/A | Current date injected |

### Demo queries

| Chip label                  | Query                                                   |
|-----------------------------|---------------------------------------------------------|
| Monday order                | what should i order this monday                         |
| Strawberries in June        | are strawberries still worth ordering in june           |
| Queen's Birthday week       | queens birthday is next week how do i adjust            |
| Leftover strawberries       | we have leftover strawberries from friday what do we do |
| Order mangoes               | should i order mangoes this week                        |
| Best performers this month  | which items have been our best performers this month    |

The toggle calls `POST /api/settings/demo` and flips the mode in memory immediately - no restart needed.

---

## Logging Sales Data

Staff can log daily sales two ways, accessible via the **Log Sales** button in the header.

### Manual entry

Select a date, enter quantities sold per item, click Save. The system appends to CSV and re-indexes ChromaDB automatically.

### Excel / CSV upload

1. Download the template from the Upload tab (pre-filled with your 28 items)
2. Fill in quantities - one row per day, items as columns
3. Upload the file

Supported formats: `.xlsx`, `.xls`, `.csv`

Both wide format (date + item columns) and long format (date, item, qty rows) are auto-detected.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Status, doc count, model name |
| POST | `/api/chat` | Non-streaming chat |
| GET | `/api/chat/stream` | SSE streaming chat |
| GET | `/api/settings` | Current demo mode and model |
| POST | `/api/settings/demo` | Toggle demo mode at runtime |
| GET | `/api/sales/items` | List of tracked produce items |
| POST | `/api/sales/daily` | Log daily sales records |
| POST | `/api/sales/upload` | Upload Excel or CSV file |
| GET | `/api/sales/template` | Download blank Excel/CSV template |
| GET | `/api/sales/forecast/{item}` | Statistical demand forecast for one item |
| GET | `/api/sales/stats` | Weeks of data, doc count, item count |

---

## Local Setup

### Prerequisites

- Python 3.11 (from python.org, not MSYS2/Homebrew-built)
- Node 20+
- Git

### Backend (Windows)

```powershell
cd backend
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env - set ANTHROPIC_API_KEY
.\venv\Scripts\uvicorn.exe app.main:app --reload
```

### Backend (macOS / Linux)

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env - set ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

On first startup, MarketMate ingests `produce_sales.csv` into ChromaDB. With the full 51-week dataset this takes 30-60 seconds while sentence-transformers embeds 9,996 rows. Subsequent startups skip ingestion.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### With Docker Compose

```bash
# Add your API key to backend/.env first
docker-compose up --build
```

Backend at http://localhost:8000, frontend at http://localhost:5173.

---

## Environment Variables

| Variable              | Required | Default               | Description                            |
|-----------------------|----------|-----------------------|----------------------------------------|
| `ANTHROPIC_API_KEY`   | Yes      | -                     | Your Anthropic API key                 |
| `LLM_PROVIDER`        | No       | `anthropic`           | LLM provider (only anthropic supported)|
| `LLM_MODEL`           | No       | `claude-sonnet-4-6`   | Claude model ID                        |
| `CHROMA_PERSIST_DIR`  | No       | `./chroma_db`         | Path to ChromaDB persistence directory |
| `SALES_DATA_PATH`     | No       | `./data/produce_sales.csv` | Path to sales CSV                 |
| `DEMO_MODE`           | No       | `true`                | Startup default for demo mode          |
| `CORS_ORIGINS`        | No       | `http://localhost:5173` | Allowed CORS origins                 |
| `LOG_LEVEL`           | No       | `INFO`                | Python logging level                   |

`DEMO_MODE` sets the startup default. The UI toggle overrides it at runtime without a restart.

---

## Project Structure

```
marketmate/
+-- backend/
|   +-- app/
|   |   +-- config.py              # pydantic-settings, loads .env with utf-8-sig
|   |   +-- models.py              # Pydantic v2 request/response models
|   |   +-- main.py                # FastAPI app, lifespan ingestion, CORS
|   |   +-- runtime_config.py      # In-memory demo mode override (runtime toggle)
|   |   +-- routes/
|   |   |   +-- chat.py            # SSE streaming + POST chat endpoints
|   |   |   +-- health.py          # /health endpoint
|   |   |   +-- sales.py           # Sales logging, upload, forecast, stats
|   |   |   +-- settings.py        # Runtime settings toggle endpoints
|   |   +-- services/
|   |   |   +-- agent.py           # LangGraph StateGraph, 7 nodes
|   |   |   +-- ingestion.py       # CSV -> ChromaDB weekly summary ingestion
|   |   |   +-- llm.py             # Anthropic Claude wrapper (sync + async)
|   |   |   +-- sales_store.py     # CSV append, Excel/CSV parsing, templates
|   |   |   +-- vector_store.py    # ChromaDB wrapper
|   |   +-- tools/
|   |   |   +-- sales_retriever.py    # RAG tool - manager's memory
|   |   |   +-- demand_forecaster.py  # Linear regression + rolling avg forecast
|   |   |   +-- spoilage_scorer.py    # Spoilage risk + velocity scoring
|   |   |   +-- holiday_checker.py    # VIC 2026 public holidays + events
|   |   |   +-- order_generator.py    # LLM-driven structured order generation
|   |   +-- demo/
|   |       +-- responses.py          # 6 pre-written demo responses
|   +-- data/
|   |   +-- produce_sales.csv         # 51-week dataset, 28 items, 9,996 rows
|   +-- tests/
|   |   +-- test_ingestion.py
|   |   +-- test_tools.py
|   |   +-- test_agent.py
|   +-- requirements.txt
|   +-- Dockerfile
+-- frontend/
|   +-- src/
|   |   +-- components/
|   |   |   +-- ChatWindow.jsx     # Main 70/30 layout, mobile responsive
|   |   |   +-- MessageBubble.jsx  # Inline markdown renderer, typing indicator
|   |   |   +-- AgentTrace.jsx     # Real-time tool call panel, collapsible
|   |   |   +-- OrderCard.jsx      # Order table with export-to-clipboard
|   |   |   +-- SalesLogModal.jsx  # Manual entry + Excel/CSV upload modal
|   |   |   +-- DemoChips.jsx      # 6 demo query pill buttons
|   |   |   +-- SpoilageAlert.jsx  # Spoilage risk badge component
|   |   +-- hooks/
|   |   |   +-- useChat.js         # SSE state, streaming token accumulation
|   |   |   +-- useAgentTrace.js   # Trace step state management
|   |   +-- services/
|   |       +-- api.js             # Axios + EventSource, all API calls
|   +-- package.json
|   +-- vite.config.js
|   +-- tailwind.config.js
+-- .github/workflows/
|   +-- backend-ci.yml
|   +-- frontend-ci.yml
+-- docker-compose.yml
+-- railway.json
```

---

## Data

The bundled dataset covers January to December 2026, 28 produce items, calibrated to a Melbourne shop with $50,000 AUD weekly produce revenue ($85,000 total). Key properties:

- Full seasonal cycles: mango (Oct-Feb), strawberry peak (Nov-Jan), citrus peak (Jun-Aug), stone fruit (Dec-Mar)
- Day-of-week patterns: Saturday 1.5x, Friday 1.25x, Monday 0.65x
- All 13 VIC 2026 public holidays with correct trade impact (pre-holiday +50%, day-of -70%)
- Gaussian noise (7% std) for realistic day-to-day variance

To replace with your own data: format a CSV to match the schema, drop it at `backend/data/produce_sales.csv`, delete `backend/chroma_db/`, and restart. Ingestion runs automatically.

---

## Known Limitations

- **No POS integration.** Sales data is logged manually or via Excel upload. A production version would pull from Square, Lightspeed, or Neto via nightly webhook and update ChromaDB automatically.
- **Single shop.** Ordering logic assumes one location with uniform pricing. Multi-site operations need per-store data partitioning.
- **Order generator is generative.** The `order_generator` calls Claude to produce quantities. Spot-check generated orders before placing with suppliers, especially for seasonal edge cases.
- **Forecast accuracy is limited under 8 weeks of real data.** The statistical model needs variance history to produce reliable confidence intervals. Generated baseline data helps but real observed data is always better.

---

## Author

**Vedant Pandya**
- LinkedIn: https://linkedin.com/in/vedant-pandya15
- Portfolio: https://vedant-pandya.vercel.app
