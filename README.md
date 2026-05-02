# P2M-TAI — Procurement AI Platform

Enterprise procurement intelligence platform that automates tender document ingestion, compliance checking, AI-powered response generation, and export — all accessible through a modern web dashboard.

---

## Table of Contents

1. [Purpose & Vision](#1-purpose--vision)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [Repository Structure](#4-repository-structure)
5. [Quick Start (Docker)](#5-quick-start-docker)
6. [Quick Start (Local Development)](#6-quick-start-local-development)
7. [Docker Setup](#7-docker-setup)
8. [API Contract](#8-api-contract)
9. [Core Flows](#9-core-flows)
10. [Environment Variables](#10-environment-variables)
11. [Workers & Processing Pipeline](#11-workers--processing-pipeline)
12. [Frontend Routes](#12-frontend-routes)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Purpose & Vision

P2M-TAI automates the end-to-end lifecycle of government/corporate tender responses:

- **Ingestion** — Upload tender PDFs; pipeline extracts text (OCR), detects language, segments into sentences, translates FR→EN chunks, and generates vector embeddings.
- **Compliance** — Rules + LLM hybrid engine evaluates tender requirements against company profile, produces an eligibility score and per-clause met/unmet/review determination.
- **RAG Query** — Semantic search over embedded chunks to ground answers in source documents.
- **Response Generation** — AI-generated draft responses organized by section (technical, financial, administrative), with citations.
- **Export** — Generate formatted DOCX responses for submission.

The platform uses Supabase (Postgres + pgvector) for persistence, RabbitMQ for async pipeline event choreography, and a Next.js frontend for human interaction.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser / Client                              │
│                    Next.js (Port 3000)                               │
│  Sidebar Nav │ Dashboard │ Tenders │ Company │ Activity             │
└──────────┬───────────────────────────────────────┬──────────────────┘
           │                                       │
    HTTP/REST (JSON)                    WebSocket (optional)
           │                                       │
┌──────────▼──────────────────────────────────────▼──────────────────┐
│                      FastAPI Backend (Port 8100)                      │
│                                                                       │
│  Routers:                                                            │
│    documents.py   — upload, list, get, delete                        │
│    compliance.py  — per-document requirements & scores               │
│    company.py     — profile & annexes                                │
│    rag.py         — semantic query                                    │
│    generate.py    — response generation                               │
│    export.py      — DOCX export creation & download                  │
│    system.py      — health, activity, messaging topology               │
│                                                                       │
│  All routes prefixed: /api/v1/*  (see API Contract below)           │
└──────────┬───────────────┬──────────────────┬──────────────────────┘
           │               │                  │
     ┌─────▼─────┐  ┌──────▼──────┐  ┌───────▼──────┐
     │ Supabase  │  │  RabbitMQ   │  │    Redis     │
     │ Postgres  │  │  (async)    │  │   (cache)    │
     │ +pgvector │  │  Port 5672  │  │  Port 6400   │
     └───────────┘  └─────────────┘  └──────────────┘
```

### Processing Pipeline (Async Workers)

```
Document Upload
      │
      ▼
document_uploaded ──► OCR Worker (Mistral AI)
      │                     │
      │                ocr_complete
      │                     │
      ▼                     ▼
NLP Worker (spaCy + deep-translator)
      │
      │ nlp_completed
      ▼
Embedding Worker (BGE-M3 / Hugging Face)
      │
      │ embedding_complete
      ▼
Compliance Worker (rules + LLM adjudication)
      │
      │ compliance_completed
      ▼
Notification Worker (SendGrid) ──► Email on high-score tenders
```

---

## 3. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend | FastAPI (Python 3.11), Uvicorn |
| Database | Supabase (Postgres 15 + pgvector) |
| Message Broker | RabbitMQ 3-management |
| Cache | Redis 7 |
| AI/ML | Hugging Face BGE-M3 embeddings, Mistral OCR, LLM generation |
| Container Runtime | Docker + Docker Compose |

---

## 4. Repository Structure

```
P2M-TAI/
├── docker-compose.app.yml          # Full stack compose (web + api + rabbitmq + redis)
├── apps/
│   ├── api/                        # FastAPI backend
│   │   ├── src/
│   │   │   ├── app.py             # FastAPI app factory, route registration
│   │   │   ├── routers/           # Route handlers (documents, compliance, etc.)
│   │   │   ├── core/              # Shared: db client, rabbitmq, file storage
│   │   │   └── services/          # Worker implementations (ocr, nlp, embedding…)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── web/                        # Next.js frontend
│       ├── src/
│       │   ├── app/               # App Router pages
│       │   │   ├── (auth)/        # Login, register
│       │   │   └── dashboard/     # Dashboard, tenders, company, activity
│       │   ├── components/        # UI components + layout (sidebar, shell, topbar)
│       │   ├── hooks/            # Custom React hooks
│       │   ├── lib/api/          # Typed API client functions
│       │   └── types/            # TypeScript interfaces
│       ├── Dockerfile
│       ├── .env.example
│       └── .env.local
├── infra/
│   └── supabase/
│       └── migrations/           # Postgres schema migrations
└── docs/
    └── design/                   # Architecture & design docs
```

---

## 5. Quick Start (Docker)

### Prerequisites
- Docker Desktop (with compose plugin) installed and running
- Ports `3000`, `5672`, `6400`, `8100`, `15672` available

### Start the full stack

```bash
cd P2M-TAI
docker compose -f docker-compose.app.yml up --build -d
```

### Verify services

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | — |
| Backend API | http://localhost:8100 | — |
| API Health | http://localhost:8100/health | — |
| RabbitMQ Management | http://localhost:15672 | admin / admin |
| RabbitMQ AMQP | amqp://localhost:5672 | admin / admin |
| Redis | localhost:6400 | — |

### Check container logs

```bash
# All containers
docker compose -f docker-compose.app.yml logs

# API only
docker compose -f docker-compose.app.yml logs api

# Web only
docker compose -f docker-compose.app.yml logs web
```

### Stop the stack

```bash
docker compose -f docker-compose.app.yml down
```

---

## 6. Quick Start (Local Development)

### Prerequisites
- Node.js 20+, Python 3.11+
- Supabase local stack running
- RabbitMQ + Redis (or via Docker: `docker compose -f infra/docker/messaging/docker-compose.yml up -d`)

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # fill in your Supabase credentials

# Start
uvicorn src.app:app --reload --port 8100
```

### Frontend

```bash
cd apps/web
npm install

# Configure environment
copy .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8100

npm run dev
```

Open http://localhost:3000

---

## 7. Docker Setup

### Services

| Container | Image | Ports |
|-----------|-------|-------|
| `p2m-web` | `tai-web` (built from `apps/web/Dockerfile`) | `3000:3000` |
| `p2m-api` | `tai-api` (built from `apps/api/Dockerfile`) | `8100:8100` |
| `p2m-rabbitmq` | `rabbitmq:3-management` | `5672:5672`, `15672:15672` |
| `p2m-redis` | `redis:7-alpine` | `6400:6379` |

### Environment injection

The compose file passes these environment variables into each container:

**API container:**
- `API_ALLOWED_ORIGINS` — comma-separated CORS origins
- `RABBITMQ_URL` — internal RabbitMQ connection string
- `REDIS_URL` — internal Redis connection string
- `WEB_BASE_URL` — frontend base URL (for notifications/links)
- Values read from `apps/api/.env`

**Web container:**
- `NEXT_PUBLIC_API_URL=http://api:8100/api/v1` (internal container-to-container)
- `API_URL=http://api:8100/api/v1`

### Build arguments

When building the web image, `NEXT_PUBLIC_API_URL` can be overridden at build time via the `--build-arg` flag. The production value passed by compose is `http://api:8100/api/v1`.

---

## 8. API Contract

All backend routes are prefixed with `/api/v1` by the FastAPI app factory. The frontend API client (`apps/web/src/lib/api/client.ts`) prepends `NEXT_PUBLIC_API_URL` (which in Docker is `http://api:8100/api/v1`), so frontend API functions use **paths without the `/api/v1` prefix** (e.g., `/documents` resolves to `http://api:8100/api/v1/documents`).

### Documents

```
POST   /documents                    Upload a tender document
GET    /documents                    List all documents (paginated)
GET    /documents/{document_id}      Get document details
DELETE /documents/{document_id}     Delete a document
GET    /documents/{document_id}/status         Current processing status
GET    /documents/{document_id}/requirements   Compliance requirements
```

**Upload**: `Content-Type: multipart/form-data`, field name `file`, max 20MB.

**List response**:
```json
{
  "items": [{ "id", "filename", "status", "created_at", "updated_at", ... }],
  "total": 11,
  "limit": 50,
  "offset": 0
}
```

### Compliance

```
GET    /documents/{document_id}/compliance              Full compliance report
GET    /documents/{document_id}/compliance/score       Summary score + go/no-go
POST   /documents/{document_id}/compliance/check        Trigger re-check
PUT    /documents/{document_id}/compliance/{requirement_id}  Update requirement status
```

**Compliance response** (`GET /compliance`):
```json
{
  "id": "...",
  "eligibility_score": 75.0,
  "recommendation": "Proceed with caution",
  "requirements": [
    {
      "id": "req-1",
      "tender_id": "doc-id",
      "clause": "5.2.1",
      "requirement": "ISO 9001 certification required",
      "status": "met|unmet|review",
      "evidence": "Certificate uploaded"
    }
  ],
  "report": { ... }
}
```

**Score response** (`GET /compliance/score`):
```json
{
  "id": "...",
  "eligibility_score": 75.0,
  "total_requirements": 10,
  "met_requirements": 7,
  "recommendation": "Proceed with caution",
  "go_no_go": "review"
}
```

### Company

```
GET    /company/profile             Get company profile
PUT    /company/profile             Update company profile
GET    /company/annexes             List annexes
POST   /company/annexes             Upload an annex
DELETE /company/annexes/{annex_id}  Delete an annex
```

### RAG

```
POST   /rag/query                             Query document knowledge base
GET    /documents/{document_id}/rag/history   Get RAG message history
DELETE /documents/{document_id}/rag/history  Clear RAG history
```

**RAG query request**:
```json
{ "document_id": "...", "query": "What is the deadline?", "top_k": 5 }
```

**RAG query response**:
```json
{
  "document_id": "...",
  "query": "What is the deadline?",
  "results": [{ "page": 3, "section": "§5.2", "excerpt": "...", "relevance": 0.92 }],
  "total_results": 3
}
```

### Responses (Generation)

```
POST   /documents/{document_id}/responses/generate    Trigger response generation
GET    /documents/{document_id}/responses             List all responses for document
GET    /documents/{document_id}/responses/{response_id}  Get specific response
PUT    /documents/{document_id}/responses/{response_id}  Update response content
DELETE /documents/{document_id}/responses/{response_id}  Delete response
```

**Generate request**:
```json
{ "query": "Generate tender response", "sections": ["technical", "financial", "administrative"] }
```

### Export

```
POST   /documents/{document_id}/export          Create DOCX export (requires response_id)
GET    /documents/{document_id}/exports        List exports for document
GET    /exports/{export_id}                     Get export metadata
DELETE /exports/{export_id}                     Delete export
GET    /exports/{export_id}/download            Download export file
```

**Create export request**:
```json
{ "response_id": "...", "format": "docx" }
```

### System

```
GET    /system/health                  Full health check (DB, RabbitMQ, Redis)
GET    /system/messaging               RabbitMQ connection status
GET    /system/messaging/topology      Queue and exchange topology
GET    /system/activity                Activity log (paginated)
GET    /health                          Simple liveness check
```

**Health response**:
```json
{
  "status": "ok|degraded|unhealthy",
  "checks": {
    "supabase": { "status": "connected" },
    "rabbitmq": { "status": "connected" },
    "redis": { "status": "connected" }
  }
}
```

---

## 9. Core Flows

### Upload → Compliance → Export

1. User navigates to `/dashboard/tenders/new`, drops a PDF.
2. `POST /documents` saves the file, publishes `document_uploaded` to RabbitMQ.
3. OCR worker extracts text; NLP worker segments/translates; Embedding worker creates vectors.
4. Compliance worker evaluates requirements; results stored in `compliance_reports` + `requirements` tables.
5. User opens `/dashboard/tenders/[id]/qualification` to see score + per-clause status.
6. User opens `/dashboard/tenders/[id]/response` → clicks **Generate Draft** → `POST /documents/{id}/responses/generate`.
7. User reviews/edits generated response.
8. User opens `/dashboard/tenders/[id]/exports` → clicks **Create Export** → `POST /documents/{id}/export`.
9. User downloads DOCX via `GET /exports/{id}/download`.

### RAG Query Flow

1. User opens `/dashboard/tenders/[id]/ask`.
2. Types a question → `POST /rag/query` with `document_id` and `query`.
3. Backend embeds the query, searches pgvector for similar chunks, returns grounded answer.
4. Chat history stored server-side; accessible via `GET /documents/{id}/rag/history`.

### Sidebar Navigation

- **Expanded mode** (default): full-width sidebar (288px) with labels + icons for all nav items.
- **Collapsed mode**: icon-only sidebar (80px); click the **←** toggle button to collapse/expand.
- Available in the top bar of any dashboard page.

---

## 10. Environment Variables

### Backend (`apps/api/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | `eyJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJ...` |
| `API_ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000` |
| `RABBITMQ_URL` | RabbitMQ AMQP URL | `amqp://admin:admin@rabbitmq:5672/%2F` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `WEB_BASE_URL` | Frontend base URL | `http://localhost:3000` |
| `MISTRAL_API_KEY` | Mistral AI API key (for OCR) | |
| `HF_TOKEN` | Hugging Face token (for embeddings + LLM) | |

### Frontend (`apps/web/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL | `http://127.0.0.1:54321` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | |
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8100` |

> In Docker, `NEXT_PUBLIC_API_URL` is set to `http://api:8100/api/v1` (container-internal).

---

## 11. Workers & Processing Pipeline

Workers consume RabbitMQ events and publish back to advance the pipeline. They are **separate processes** that run independently of the FastAPI server.

| Worker | Command | Consumes | Produces |
|--------|---------|----------|----------|
| OCR | `python -m apps.api.src.services.ocr.run_worker` | `document_uploaded` | `ocr_complete` |
| NLP | `python -m apps.api.src.services.nlp.run_worker` | `ocr_complete` | `nlp_completed` |
| Embedding | `python -m apps.api.src.services.embedding.run_worker` | `nlp_completed` | `embedding_complete` |
| Compliance | `python -m apps.api.src.services.compliance.run_worker` | `embedding_complete` | `compliance_completed` |
| Notification | `python -m apps.api.src.services.notification.run_worker` | `compliance_completed` | (email only) |
| RAG | `python -m apps.api.src.services.rag.worker` | (on-demand, not queued) | |
| LLM Generation | `python -m apps.api.src.services.llm.worker` | (on-demand, not queued) | |
| Export | `python -m apps.api.src.services.export.worker` | (on-demand, not queued) | |

Workers are triggered via HTTP calls to the FastAPI server, which enqueues jobs into RabbitMQ, or via direct function calls. The REST endpoints themselves handle the async dispatch.

---

## 12. Frontend Routes

| Route | Description |
|-------|-------------|
| `/login` | Authentication — login |
| `/register` | Authentication — registration |
| `/dashboard` | Overview: tender count, system status, recent tenders, quick actions |
| `/dashboard/tenders` | Tender library: list all documents, upload button, status badges |
| `/dashboard/tenders/new` | Upload new tender document |
| `/dashboard/tenders/[id]/overview` | Document metadata, file info, processing status |
| `/dashboard/tenders/[id]/qualification` | Compliance score card, go/no-go, per-clause status, re-check button |
| `/dashboard/tenders/[id]/response` | RAG-grounded Q&A, response generation, draft editing |
| `/dashboard/tenders/[id]/ask` | RAG chat interface — ask questions about the tender |
| `/dashboard/tenders/[id]/exports` | Export management — create, list, download DOCX files |
| `/dashboard/company/profile` | Company profile view and edit |
| `/dashboard/company/credentials` | Credential/document annexes management |
| `/dashboard/activity` | System status and activity logs |

---

## 13. Troubleshooting

### "Failed to fetch" on tenders page

Most likely a CORS or API URL misconfiguration. Verify:
1. `NEXT_PUBLIC_API_URL` in `.env.local` matches the running backend (e.g., `http://localhost:8100` for local, `http://api:8100/api/v1` for Docker).
2. `API_ALLOWED_ORIGINS` in the backend `.env` includes the frontend origin.
3. Run `docker compose logs web` and `docker compose logs api` to check for errors.

### RabbitMQ connection refused

Ensure the RabbitMQ container is running:
```bash
docker compose -f docker-compose.app.yml ps rabbitmq
```
If stopped, remove and restart:
```bash
docker compose -f docker-compose.app.yml down
docker compose -f docker-compose.app.yml up -d
```

### Port already in use

If ports conflict with existing containers, edit `docker-compose.app.yml`:
```yaml
ports:
  - "3001:3000"    # change host port for web
  - "8101:8100"    # change host port for api
```

### Document stuck in processing state

Check worker logs:
```bash
docker compose logs api | grep -i "worker"
```
Ensure workers are running. Processing status transitions: `uploaded` → `reading` → `indexing` → `qualifying` → `qualified` → `generating` → `completed` (or `failed`).

### API returns 500 on topology

This indicates the RabbitMQ management API is not reachable from inside the API container. Ensure `RABBITMQ_URL` is set correctly in `apps/api/.env` and matches the compose service name.

### Web build fails with `EBADPLATFORM`

The `package.json` must not include platform-specific `@next/swc-*` packages. The `package.json` ships with a pure Node.js frontend and uses Next.js's built-in compiler (Turbopack). Do not add `@next/swc-win32-x64-msvc` or similar.
