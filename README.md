# MarketMate 🥦 - Agentic RAG System for Produce Ordering


AI ordering assistant for a Melbourne fresh produce retailer.

| | |
|---|---|
| Frontend | https://marketmate-eight.vercel.app |
| Backend API | https://vedant1515-marketmate.hf.space |
| Health check | https://vedant1515-marketmate.hf.space/health |
| GitHub | https://github.com/Vedant1515/MarketMate |

---

## Problem

Ordering decisions at a Melbourne produce shop are locked inside one experienced manager's head. When that manager is unavailable, untrained staff over-order causing spoilage or under-order causing stockouts.

The shop does **$85,000 AUD per week** total, with **$50,000 from produce**. A 5% ordering error costs $2,500 per week - $130,000 annualised in avoidable waste or lost sales.

MarketMate learns from a full year of daily sales data across 28 produce items and replicates the manager's ordering instincts for any staff member, any day of the week.

---

## Architecture

```
Browser (React + Vite + Tailwind)
         |
         | SSE stream / REST
         v
FastAPI (Python 3.11) on Hugging Face Spaces
         |
         | LangGraph StateGraph (7 nodes)
         v
+------------------+-------------------+------------------+
| sales_retriever  | demand_forecaster | holiday_checker  |
| ChromaDB RAG     | Linear regression | VIC 2026 holidays|
| 1,428 documents  | + rolling avg     | + event impacts  |
+------------------+-------------------+------------------+
+------------------+-------------------+
| spoilage_scorer  | order_generator   |
| Velocity + shelf | Claude API        |
| life ratio       | structured JSON   |
+------------------+-------------------+
         |
         v
Claude claude-sonnet-4-6
Current date/time injected into every LLM call
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI 0.115, uvicorn |
| AI agent | LangGraph 0.2, LangChain Core 0.2.43 |
| LLM | Anthropic Claude claude-sonnet-4-6 |
| Vector DB | ChromaDB 0.5 (local persistent) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (local, no API) |
| Forecasting | numpy linear regression + pandas rolling averages |
| Data | pandas 2.2, openpyxl 3.1, 51-week produce sales CSV |
| Frontend | React 18, Vite 5, Tailwind CSS 3 |
| Streaming | Server-Sent Events (SSE) |
| Backend host | Hugging Face Spaces (Docker SDK) |
| Frontend host | Vercel |
| Container | Docker multi-stage |
| CI | GitHub Actions (lint + test + build) |

---

## How It Works

### RAG Pipeline

On startup, MarketMate reads `produce_sales.csv` and ingests it into ChromaDB as weekly summary documents. Each document covers one item for one week: total quantity sold, daily average, peak day, week-over-week trend, spoilage window, holiday context, and revenue.

The dataset covers 51 weeks, 28 items, 9,996 rows calibrated to $50,000 AUD weekly produce revenue. ChromaDB holds approximately 1,428 documents.

When a user asks a question, `sales_retriever` embeds the query using `all-MiniLM-L6-v2` and retrieves the 4 most relevant weekly records. This is the manager's memory - historical patterns the LLM reasons over.

### LangGraph Agent (7 nodes)

```
query_router
    |
    v
sales_retriever (always runs)
    |
    +--[forecast query?]--> demand_forecaster
    |
    +--[holiday/date?]----> holiday_checker
    |
    +--[spoilage/waste?]--> spoilage_scorer
    |
    +--[order request?]--> order_generator
    |
    v
response_synthesiser (all paths converge)
    |
    v
Claude claude-sonnet-4-6
+ current date/time injected
```

Every LLM call receives the exact current date, time, day name, and week number. Claude cannot confuse day names or misidentify the trading window.

### Learning Pipeline

Every time sales are logged, three things happen automatically:

1. New rows appended to `produce_sales.csv`
2. `run_ingestion()` re-indexes ChromaDB - collection grows over time
3. Demand forecaster cache cleared - next query uses fresh data

Forecast confidence improves with data: under 4 weeks = Low, 4-8 weeks = Medium, 8+ weeks = High.

---

## The Five Tools

| Tool | Purpose |
|---|---|
| `sales_retriever` | RAG over ChromaDB. Core of the manager's memory. |
| `demand_forecaster` | Linear regression + 4/8-week rolling average per item. |
| `holiday_checker` | VIC 2026 public holidays with foot traffic impact percentages. |
| `spoilage_scorer` | Spoilage risk ratio based on shelf life and sales velocity. |
| `order_generator` | Claude-generated structured order with quantities, costs, confidence. |

---

## Demo Mode vs Live AI

Toggle in the UI header - switches at runtime, no restart needed.

| | Demo | Live AI |
|---|---|---|
| Queries answered | 6 preset only | Any question |
| Response | Pre-written | Claude API |
| Cost | $0 | ~$0.01-0.05/query |
| Date awareness | N/A | Exact date injected |

### Demo queries

| Label | Query |
|---|---|
| Monday order | what should i order this monday |
| Strawberries in June | are strawberries still worth ordering in june |
| Queen's Birthday week | queens birthday is next week how do i adjust |
| Leftover strawberries | we have leftover strawberries from friday what do we do |
| Order mangoes | should i order mangoes this week |
| Best performers this month | which items have been our best performers this month |

---

## Logging Sales Data

Click **Log Sales** in the header to open the modal.

**Manual entry:** select date, enter quantities per item, click Save.

**Excel / CSV upload:**
1. Download the template (pre-filled with 28 items as columns)
2. Fill in quantities - one row per day
3. Upload - wide format (date + item columns) and long format (date/item/qty rows) both supported

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Status, document count, model |
| POST | `/api/chat` | Non-streaming chat |
| GET | `/api/chat/stream` | SSE streaming chat |
| GET | `/api/settings` | Current mode and model |
| POST | `/api/settings/demo` | Toggle demo/live mode |
| GET | `/api/sales/items` | List of tracked items |
| POST | `/api/sales/daily` | Log daily sales |
| POST | `/api/sales/upload` | Upload Excel or CSV |
| GET | `/api/sales/template` | Download blank template |
| GET | `/api/sales/forecast/{item}` | Statistical demand forecast |
| GET | `/api/sales/stats` | Weeks of data, doc count |

---

## Local Setup

### Prerequisites

- Python 3.11 from python.org (not MSYS2 or system Python)
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

First startup ingests `produce_sales.csv` into ChromaDB. With the full 51-week dataset this takes 30-60 seconds. Subsequent startups skip ingestion.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
# Set ANTHROPIC_API_KEY in backend/.env first
docker-compose up --build
```

Backend at http://localhost:8000, frontend at http://localhost:5173.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key |
| `LLM_PROVIDER` | No | `anthropic` | LLM provider |
| `LLM_MODEL` | No | `claude-sonnet-4-6` | Claude model ID |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |
| `SALES_DATA_PATH` | No | `./data/produce_sales.csv` | Sales data path |
| `DEMO_MODE` | No | `true` | Startup default for demo mode |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

`DEMO_MODE` is the startup default only. The UI toggle overrides it at runtime.

---

## Project Structure

```
marketmate/
├── Dockerfile                     # Root Dockerfile for Hugging Face Spaces (port 7860)
├── .dockerignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile                 # Backend Dockerfile for local/compose (port 8000)
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── config.py              # pydantic-settings, utf-8-sig .env loading
│   │   ├── models.py              # Pydantic v2 models
│   │   ├── main.py                # FastAPI app, lifespan, CORS
│   │   ├── runtime_config.py      # In-memory demo mode override
│   │   ├── routes/
│   │   │   ├── chat.py            # SSE streaming + POST chat
│   │   │   ├── health.py          # /health
│   │   │   ├── sales.py           # Sales logging, upload, forecast, stats
│   │   │   └── settings.py        # Runtime toggle
│   │   ├── services/
│   │   │   ├── agent.py           # LangGraph StateGraph, 7 nodes
│   │   │   ├── ingestion.py       # CSV -> ChromaDB ingestion
│   │   │   ├── llm.py             # Anthropic Claude wrapper
│   │   │   ├── sales_store.py     # CSV append, Excel/CSV parsing
│   │   │   └── vector_store.py    # ChromaDB wrapper
│   │   ├── tools/
│   │   │   ├── sales_retriever.py
│   │   │   ├── demand_forecaster.py
│   │   │   ├── spoilage_scorer.py
│   │   │   ├── holiday_checker.py
│   │   │   └── order_generator.py
│   │   └── demo/
│   │       └── responses.py       # 6 pre-written demo responses
│   ├── data/
│   │   └── produce_sales.csv      # 51 weeks, 28 items, 9,996 rows
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── AgentTrace.jsx
│   │   │   ├── OrderCard.jsx
│   │   │   ├── SalesLogModal.jsx
│   │   │   ├── DemoChips.jsx
│   │   │   └── SpoilageAlert.jsx
│   │   ├── hooks/
│   │   │   ├── useChat.js
│   │   │   └── useAgentTrace.js
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── .github/
    └── workflows/
        ├── backend-ci.yml
        └── frontend-ci.yml
```

---

## Data

The bundled dataset covers January to December 2026, 28 produce items, calibrated to $50,000 AUD weekly produce revenue. Full seasonal cycles for all items, day-of-week patterns, and all 13 VIC 2026 public holidays are included.

To use your own data: format a CSV to match the schema in `backend/data/produce_sales.csv`, replace the file, delete `backend/chroma_db/`, and restart.

---

## Known Limitations

- No POS integration. Sales are logged manually or via Excel. Production needs a nightly webhook from Square, Lightspeed, or Neto.
- Single shop only. No per-location partitioning.
- Order generator quantities come from the LLM - spot-check before placing with suppliers.
- Forecast accuracy needs 8+ weeks of real observed data for High confidence.
- No authentication or rate limiting on the API.

---

## Author

**Vedant Pandya**
- LinkedIn: https://linkedin.com/in/vedant-pandya15
- Portfolio: https://vedant-pandya.vercel.app
