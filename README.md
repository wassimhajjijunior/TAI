# P2M-TAI — Procurement Intelligence Platform

An AI platform that automates the tender-response lifecycle: ingest a tender document, extract and index its content, evaluate compliance, answer questions with retrieval-augmented generation, draft a grounded response, and export a submittable DOCX.

![status](https://img.shields.io/badge/status-active-blue)
![backend](https://img.shields.io/badge/backend-FastAPI-009688)
![frontend](https://img.shields.io/badge/frontend-Next.js%2016-black)
![db](https://img.shields.io/badge/database-Supabase%20%2B%20pgvector-3ECF8E)
![queue](https://img.shields.io/badge/async-RabbitMQ-FF6600)

---

## Table of Contents

- [Overview](#overview)
- [Problem](#problem)
- [Solution](#solution)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Processing Pipeline](#processing-pipeline)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Data Model](#data-model)
- [API Reference](#api-reference)
- [Core Flows](#core-flows)
- [Frontend Routes](#frontend-routes)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Verification](#verification)
- [Design Decisions](#design-decisions)
- [Author](#author)

---

## Overview

**P2M-TAI** turns a tender PDF into a structured, actionable bid workspace. It combines a deterministic rules engine with retrieval-augmented generation (RAG) and large language models to reduce the manual effort of reading, qualifying, and answering procurement documents.

The system is a modern monorepo:

- **`apps/web`** — Next.js 16 (App Router) dashboard.
- **`apps/api`** — FastAPI backend with an event-driven document-processing pipeline.
- **`packages/*`** — shared TypeScript types and UI primitives.

The backend is organized as a **modular monolith** with nine isolated service domains plus asynchronous workers, backed by Supabase (Postgres + `pgvector`), RabbitMQ, and Redis.

---

## Problem

Procurement teams responding to tenders face a costly, error-prone workflow:

- Tender documents are long, heterogeneous (PDF, scans, multi-language) and dense with legal clauses.
- Eligibility requirements must be checked manually against company credentials.
- Drafting a compliant, well-structured response takes days per bid.
- Knowledge is locked in documents — answering a single question requires re-reading hundreds of pages.

The result: low win rates, missed deadlines, compliance failures, and high labor cost per bid.

## Solution

P2M-TAI applies a hybrid AI pipeline:

1. **Ingest** — parse and OCR the tender; detect language; chunk and embed content.
2. **Qualify** — evaluate requirements with a rules engine and produce an eligibility score.
3. **Retrieve** — ground every answer in the source via vector search (`pgvector`).
4. **Generate** — draft responses with an LLM using retrieved context and citations.
5. **Export** — produce a formatted DOCX ready for submission.

---

## Key Features

- **Document ingestion** — PDF/DOCX upload, OCR via Mistral, artifact storage.
- **Multilingual NLP** — language detection (`langdetect`), sentence-aware chunking (`chonkie`), FR→EN translation (`deep-translator`).
- **Vector search** — BGE-M3 embeddings (1024-dim) in Supabase `pgvector`, HNSW-indexed, `match_chunks` RPC.
- **Compliance engine** — rules-based requirement evaluation with eligibility score and go/no-go recommendation.
- **RAG Q&A** — ask questions, get grounded answers with page/section citations.
- **Response generation** — LLM drafts (`llama-3.3-70b` via Groq) organized by section, with citations.
- **DOCX export** — `python-docx`-generated submission document with metadata, sections, and footer.
- **Async choreography** — RabbitMQ event pipeline linking OCR → NLP → Embedding → Compliance → Notification.
- **Observability-ready** — health checks across Supabase, RabbitMQ, and Redis; live document status via WebSocket.
- **Modern UI** — Next.js 16, Tailwind v4, accessible component system.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Browser (Client)                             │
│                 Next.js 16 App Router  ·  Port 3000                    │
│   Sidebar · Dashboard · Tenders · Qualification · Response · Ask       │
└───────────────┬───────────────────────────────────────┬──────────────┘
                │  HTTP/REST (/api/v1)                   │  WebSocket
                ▼                                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend  ·  Port 8100                     │
│                                                                        │
│  Routers (/api/v1):                                                    │
│    documents   compliance   company   rag   generate   export   system │
│                                                                        │
│  Services (modular monolith):                                          │
│    ingestion  ocr  nlp  embedding  compliance  rag  llm  export  notif │
│                                                                        │
│  Core: document_repository (Supabase REST) · rabbitmq · file_storage   │
└───────┬─────────────────────┬─────────────────────┬──────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Supabase    │     │   RabbitMQ    │     │     Redis     │
│ Postgres 15   │     │  p2m.events   │     │  cache/state  │
│  + pgvector   │     │  5672/15672   │     │    6400       │
└───────────────┘     └───────────────┘     └───────────────┘
```

**Layering principle:** routers handle HTTP only; services hold domain logic; `core` provides cross-cutting infrastructure (repository, messaging, storage). Workers consume broker events and advance document state independently of the API server.

---

## Processing Pipeline

Documents flow through an asynchronous, event-driven pipeline. Each worker consumes one event and publishes the next:

```
  Upload
    │  POST /api/v1/documents
    ▼
ingestion ──► document_uploaded
                   │
                   ▼
             ocr (Mistral OCR) ──► ocr_complete
                   │
                   ▼
             nlp (spaCy · chonkie · translate) ──► nlp_completed
                   │
                   ▼
             embedding (BGE-M3 · 1024-dim) ──► embedding_complete
                   │
                   ▼
             compliance (rules + score) ──► compliance_completed
                   │
                   ▼
             notification (SendGrid)   ──► email on qualified tenders
```

Document status transitions:

```
uploaded → reading → indexing → qualifying → qualified → generating → completed
                                                              └────────► failed
```

Workers run as independent processes (`python -m src.services.<domain>.run_worker`), decoupled from the FastAPI server.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16 (App Router), React, TypeScript, Tailwind CSS v4, shadcn/ui (Base UI), Lucide icons |
| **Backend** | FastAPI (Python 3.11+), Uvicorn, Pydantic |
| **AI / OCR** | Mistral OCR (`mistral-ocr-latest`) |
| **AI / LLM** | Groq (`llama-3.3-70b-versatile`) |
| **AI / Embeddings** | Hugging Face `BAAI/bge-m3` (1024-dim) via LangChain |
| **NLP** | spaCy, Chonkie (chunking), langdetect, deep-translator |
| **RAG** | LangChain + Supabase `pgvector` (`match_chunks` RPC, HNSW) |
| **Database** | Supabase (Postgres 15 + pgvector) via PostgREST |
| **Messaging** | RabbitMQ (`pika`) |
| **Cache** | Redis |
| **Export** | python-docx |
| **Email** | SendGrid |
| **Infra** | Docker, Docker Compose |

---

## Repository Structure

```
P2M-TAI/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── src/
│   │   │   ├── app.py                # App factory, CORS, route registration
│   │   │   ├── routers/              # HTTP layer (documents, compliance, rag, ...)
│   │   │   ├── core/                 # document_repository, rabbitmq, file_storage
│   │   │   └── services/             # ocr, nlp, embedding, compliance,
│   │   │                             #   rag, llm, export, notification, ingestion
│   │   ├── storage/                  # artifacts & uploaded documents (runtime)
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── web/                          # Next.js frontend
│       ├── src/
│       │   ├── app/                  # App Router pages (dashboard, tenders, ...)
│       │   ├── components/           # ui, layout, auth, upload
│       │   ├── lib/                  # api client, supabase, utils
│       │   └── types/                # shared TypeScript interfaces
│       └── .env.example
├── packages/
│   ├── shared-types/                 # cross-app TypeScript contracts
│   └── ui/                           # shared UI primitives
├── infra/
│   ├── supabase/migrations/          # 0001–0013 SQL migrations
│   └── docker/                       # messaging + local supabase compose
├── docs/                             # architecture, roadmap, devops, testing
├── docker-compose.app.yml
└── README.md
```

---

## Data Model

Supabase schema, applied through `infra/supabase/migrations/` (13 versioned migrations):

| Table | Purpose |
|-------|---------|
| `tenants` | Tenant isolation root |
| `documents` | Uploaded tender records + processing status, metadata, `chunk_count` |
| `chunks` | Extracted text segments + `embedding vector(1024)` (HNSW index) + metadata |
| `requirements` | Extracted compliance requirements (`met`, `confidence`, `weight`, `actual_value`) |
| `compliance_reports` | Per-document eligibility score + recommendation |
| `company_profiles` | Company information used during qualification/generation |
| `annexes` | Supporting credential documents |
| `responses` | Generated draft responses + citations |
| `exports` | Export records + status + storage reference |
| `notifications` | Email events with idempotency (`event_id` unique index) |
| `users` | Reserved for auth/ownership |

RPC: `match_chunks(document_id, query_embedding, match_count)` — cosine distance (`<=>`), HNSW-accelerated.

---

## API Reference

All routes are prefixed with `/api/v1` (except the liveness probe). Interactive docs at `/docs` and `/redoc`.

### Documents
```
POST   /api/v1/documents                       Upload a document (multipart: file)
GET    /api/v1/documents                       List documents
GET    /api/v1/documents/{id}                  Get document
DELETE /api/v1/documents/{id}                  Delete document
GET    /api/v1/documents/{id}/status           Processing status
GET    /api/v1/documents/{id}/requirements     Extracted requirements
GET    /api/v1/documents/{id}/ocr-artifact     OCR artifact
```

### Compliance
```
GET    /api/v1/documents/{id}/compliance                 Full report + requirements
GET    /api/v1/documents/{id}/compliance/score           Score + go/no-go
POST   /api/v1/documents/{id}/compliance/check           Trigger re-check
PUT    /api/v1/documents/{id}/compliance/{req_id}        Update requirement status
```

### Company
```
GET    /api/v1/company/profile                 Get profile
PUT    /api/v1/company/profile                 Update profile
GET    /api/v1/company/annexes                 List annexes
POST   /api/v1/company/annexes                 Upload annex
```

### RAG
```
POST   /api/v1/rag/query                        Semantic query (document_id, query, top_k)
GET    /api/v1/documents/{id}/rag/history       Chat history
DELETE /api/v1/documents/{id}/rag/history       Clear history
```

### Response Generation
```
POST   /api/v1/generate/response                          Generate a response
GET    /api/v1/responses/{id}                             Get response
PATCH  /api/v1/responses/{id}                             Update response
GET    /api/v1/documents/{id}/responses                   List responses
POST   /api/v1/documents/{id}/responses/generate         Generate for document
GET    /api/v1/documents/{id}/responses/{rid}             Get document response
PUT    /api/v1/documents/{id}/responses/{rid}             Update document response
DELETE /api/v1/documents/{id}/responses/{rid}            Delete document response
```

### Export
```
POST   /api/v1/documents/{id}/export            Create DOCX export (response_id, format)
GET    /api/v1/documents/{id}/exports           List exports
GET    /api/v1/exports/{id}/download            Download export file
```

### System
```
GET    /api/v1/system/health                    Full health (Supabase, RabbitMQ, Redis)
GET    /api/v1/system/messaging                 Broker connectivity
GET    /api/v1/system/messaging/topology        Queues and exchanges
GET    /api/v1/system/activity                  Activity log
GET    /health                                  Liveness probe
WS     /api/v1/live/documents                   Live document status stream
```

---

## Core Flows

**Upload → Qualify → Export**
1. `POST /api/v1/documents` saves the file and publishes `document_uploaded`.
2. OCR → NLP → Embedding workers populate chunks and vectors.
3. Compliance worker scores requirements and writes `compliance_reports`.
4. Dashboard shows score and per-clause status at `/dashboard/tenders/{id}/qualification`.
5. `POST /api/v1/documents/{id}/responses/generate` drafts a response.
6. `POST /api/v1/documents/{id}/export` renders DOCX; `GET /api/v1/exports/{id}/download` retrieves it.

**RAG Q&A**
1. `POST /api/v1/rag/query` embeds the question.
2. `match_chunks` retrieves the closest chunks.
3. The LLM answers strictly from retrieved context; sources are returned with page/section.

---

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/login`, `/register` | Authentication (Supabase) |
| `/dashboard` | Overview: stats, recent tenders, quick actions |
| `/dashboard/tenders` | Tender library |
| `/dashboard/tenders/new` | Upload a tender |
| `/dashboard/tenders/{id}/overview` | Document metadata and processing timeline |
| `/dashboard/tenders/{id}/qualification` | Compliance score, go/no-go, clause checklist |
| `/dashboard/tenders/{id}/response` | Draft response editor |
| `/dashboard/tenders/{id}/ask` | RAG chat |
| `/dashboard/tenders/{id}/exports` | Export management |
| `/dashboard/company/profile` | Company profile |
| `/dashboard/company/credentials` | Credentials/annexes |
| `/dashboard/activity` | System health and activity |

---

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker (for RabbitMQ, Redis, and optionally local Supabase)

### Option 1 — Docker (full stack)
```bash
docker compose -f docker-compose.app.yml up --build -d
```
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8100 |
| API docs | http://localhost:8100/docs |
| RabbitMQ UI | http://localhost:15672 (admin/admin) |

> Workers are not part of the default compose file; start them separately for full pipeline processing.

### Option 2 — Local development
```bash
# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.app:app --reload --port 8100

# Frontend (new terminal)
cd apps/web
npm install
npm run dev
```

Detailed local testing steps: see [`docs/LOCAL_TESTING.md`](docs/LOCAL_TESTING.md).

---

## Environment Variables

### Backend (`apps/api/.env`)
| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service-role key |
| `API_ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `RABBITMQ_URL` | AMQP connection URL |
| `REDIS_URL` | Redis connection URL |
| `MISTRAL_API_KEY` | Mistral (OCR) key |
| `GROQ_API_KEY` | Groq (LLM) key |
| `HF_TOKEN` | Hugging Face token (embeddings) |
| `LANGCHAIN_EMBEDDING_MODEL` | Embedding model id (default `BAAI/bge-m3`) |
| `LANGCHAIN_GROQ_METADATA_MODEL` | Metadata-extraction model id |
| `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `NOTIFICATION_RECIPIENT_EMAIL` | Email notifications |
| `WEB_BASE_URL` | Frontend base URL (for links) |

### Frontend (`apps/web/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend base URL (default `http://localhost:8100`; client normalizes to `/api/v1`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

---

## Project Status

A real backend engine backs a demo-mode frontend. Maturity by layer:

| Layer | Status | Notes |
|-------|--------|-------|
| AI service pipeline | Done | OCR, NLP, embeddings, RAG, LLM, export, notification implemented |
| Database schema | Done | 13 migrations, pgvector + HNSW |
| API surface | Partial | Most endpoints live; auth/tenant + a few stubs pending |
| Frontend | Demo | Pages render with mock data; backend wiring is in progress |
| Auth | In progress | Supabase forms present; session/route-guard/JWT in progress |
| Tests / CI | Planned | Not yet implemented |

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full gap analysis and plan.

## Roadmap

High-level next milestones:
1. Wire frontend pages to the live API (with mock fallback).
2. Authentication and multi-tenant authorization end-to-end.
3. Complete remaining stubs (annexes, activity log, RAG history).
4. Automated tests and CI.
5. DevOps deployment and observability (see [`docs/DEVOPS_PLAN.md`](docs/DEVOPS_PLAN.md)).

---

## Verification

```bash
# Backend syntax
python -m compileall -q apps/api/src

# Frontend typecheck + production build
cd apps/web && npx tsc --noEmit && npx next build
```
All three currently pass.

---

## Design Decisions

- **Modular monolith over microservices** — nine clear service domains within one deployable; extracted to services only when a boundary demands independent scaling.
- **Supabase (Postgres + pgvector) over a dedicated vector DB** — one store for relational + vector data, fewer moving parts.
- **Event-driven pipeline** — long-running OCR/embedding work is decoupled from HTTP request latency; workers scale independently.
- **Hybrid rules + LLM compliance** — deterministic rule evaluation for auditability, LLM assistance for language-heavy clauses.
- **Citations everywhere** — RAG answers and generated responses always reference source clauses to preserve trust and auditability.

---

## Author

**Wassim Hajji**
- GitHub: [@wassimhajjijunior](https://github.com/wassimhajjijunior)
- LinkedIn: [linkedin.com/in/hajji-wassim](https://linkedin.com/in/hajji-wassim)

---

<sub>Built with FastAPI, Next.js, Supabase, pgvector, RabbitMQ, and LangChain.</sub>
