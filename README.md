# P2M-TAI

P2M-TAI is a tender AI platform organized as vertical feature tracks so multiple teammates can work in parallel with minimal merge conflicts.

- **Track A**: Document Ingestion & Analysis
- **Track B**: Response Generation & Export

---

## 1) Tech Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS v4, shadcn/ui
- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (Postgres)
- **Messaging (local optional)**: RabbitMQ + Redis (separate docker compose)

---

## 2) Repository Structure

```text
P2M-TAI/
├── apps/
│   ├── web/                    # Next.js frontend
│   └── api/                    # FastAPI backend
├── packages/
│   ├── shared-types/           # Shared contracts between tracks
│   └── ui/                     # Shared UI package placeholder
├── infra/
│   ├── supabase/
│   │   ├── config.toml
│   │   └── migrations/         # DB migrations (shared + track-specific)
│   └── docker/
│       ├── messaging/          # RabbitMQ + Redis compose
│       └── supabase-local/     # Separate local Supabase-related compose
├── docs/
│   ├── architecture/
│   ├── api/
│   └── handoff/
└── .sisyphus/plans/
```

---

## 3) Prerequisites

Install on your machine:

- **Node.js** 20+
- **npm** 10+
- **Python** 3.11+
- **Git**
- **Supabase local stack** (your existing local setup)
- Optional: **Docker Desktop** (for messaging/local DB helper services)

---

## 4) Quick Start (Teammate Onboarding)

From project root:

```bash
cd P2M-TAI
npm install
```

### 4.1 Configure environment

#### Frontend env

```bash
copy apps/web/.env.example apps/web/.env.local
```

Set values in `apps/web/.env.local`:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL` (default backend is `http://localhost:8100`)

#### Backend env

```bash
copy apps/api/.env.example apps/api/.env
```

Set values in `apps/api/.env`:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `API_ALLOWED_ORIGINS`

> Security: never expose `SUPABASE_SERVICE_ROLE_KEY` in frontend code.

### 4.2 Apply database migrations

Migrations are in:

`infra/supabase/migrations`

Current files:

- `0001_shared_foundation.sql`
- `0002_track_a.sql`
- `0003_track_b.sql`
- `0004_track_a_documents_metadata.sql`

Apply them to your local Supabase project before testing upload/persistence flows.

### 4.3 Run backend (FastAPI)

```bash
.venv311/Scripts/python -m uvicorn apps.api.src.main:app --reload --host 127.0.0.1 --port 8100
```

Health check:

`GET http://127.0.0.1:8100/health`

### 4.4 Run frontend (Next.js)

```bash
npm run dev:web
```

Open:

`http://localhost:3000`

---

## 5) NPM Scripts

From root:

- `npm run dev:web` → start frontend dev server
- `npm run typecheck:web` → TypeScript check for web app
- `npm run build:web` → production build for web app

From `apps/web`:

- `npm run dev`
- `npm run typecheck`
- `npm run build`

---

## 6) Local Docker (Optional)

### Messaging stack

```bash
docker compose -f infra/docker/messaging/docker-compose.yml up -d
```

Services:

- RabbitMQ: `localhost:5672`, management UI `localhost:15672`
- Redis: `localhost:6400`

### Supabase-local helper compose

```bash
docker compose -f infra/docker/supabase-local/docker-compose.yml up -d
```

---

## 7) Current Feature Status (Important)

### Track A – Implemented now

- Upload page at `/documents/new` with Tailwind + shadcn styling
- Drag-and-drop + file input upload
- `POST /api/v1/documents` persists metadata in Supabase `documents` table
- Existing uploaded files are listed on the same page
- Files can be deleted from UI (`DELETE /api/v1/documents/{id}`)
- Processing status is now shown in UI with polling progress
- Upload publishes `document_uploaded` event to RabbitMQ

### OCR Worker (Mistral AI)

Track A OCR worker consumes `document_uploaded` and publishes `ocr_complete`.

Run OCR worker:

```bash
.venv311/Scripts/python -m apps.api.src.services.ocr.run_worker
```

Required env vars in `apps/api/.env`:

- `RABBITMQ_URL`
- `MISTRAL_API_KEY`

How OCR source is resolved:

- Upload endpoint stores incoming file in local backend path:
  - `apps/api/storage/documents/`
- `document_uploaded` event includes `storage_path`
- OCR worker uploads that file to Mistral Files API, gets signed URL, then runs OCR

Pipeline events used now:

`document_uploaded` → `ocr_complete` → `nlp_completed` → `embedding_complete`

### Key upload constraints

- Accepted types: PDF, DOC, DOCX, TXT
- Max file size: 20 MB

---

## 8) API Ownership (Summary)

See full API list in: `docs/api/endpoints.md`

- **Track A**: documents/compliance/company profile + annexes
- **Track B**: rag/generate/response/export

---

## 9) Team Ownership

- Track A scope: `docs/handoff/track-a.md`
- Track B scope: `docs/handoff/track-b.md`

Use these files to avoid overlap and coordinate PR ownership.

---

## 10) Troubleshooting

### `405 Method Not Allowed` on DELETE

Usually stale backend process. Restart API server and verify route in OpenAPI:

`http://127.0.0.1:8100/openapi.json`

### `Missing required environment variable: SUPABASE_URL`

Create and fill:

`apps/api/.env`

### Port conflict on `8100`

Use another port (e.g. `8110`) and update frontend:

- `NEXT_PUBLIC_API_URL=http://localhost:8110`

---

## 11) Suggested Collaboration Workflow

1. Pull latest `main`
2. Work on your track-owned folders only
3. Run checks before PR:
   - `npm run typecheck:web`
   - `npm run build:web`
   - `python -m compileall apps/api/src`
4. Open PR with changed scope clearly tagged (Track A or Track B)

---

## 12) Additional Docs

- Architecture split: `docs/architecture/feature-split.md`
- API contract/ownership: `docs/api/endpoints.md`
- Handoff scope: `docs/handoff/track-a.md`, `docs/handoff/track-b.md`
