# Local Testing Workflow

> How to run P2M-TAI locally and verify the code manually.
> Windows + PowerShell. Two workflows: **A = UI (works now)**, **B = backend (needs Supabase fix)**.

---

## Current reality

| Layer | Can test now? | Why |
|-------|---------------|-----|
| Frontend UI | ✅ Yes | Builds green; pages use mock data |
| Backend compile | ✅ Yes | `python -m compileall apps/api/src` passes |
| Backend runtime | ⚠️ After Supabase fix | `SUPABASE_URL=http://localhost:8000` not a live DB; `REDIS_URL` missing; migrations not applied; workers not started |
| Full UI↔backend | ❌ Not yet | Pages not wired to API (Phase 1); UI is mock |

---

## WORKFLOW A — Frontend UI (start here, 2 minutes)

```powershell
cd C:\Users\LENOVO\Desktop\p2m\P2M-TAI\apps\web
npm install          # first time only
npm run dev
```

Open **http://localhost:3000**

### Manual test checklist
- [ ] `/` landing → "Go to Dashboard" works
- [ ] `/dashboard` → stats, recent tenders, quick actions render
- [ ] `/dashboard/tenders` → table of 7 tenders
- [ ] `/dashboard/tenders/new` → select a PDF → animated progress → redirects to an overview
- [ ] `/dashboard/tenders/1/overview` → metadata + processing timeline
- [ ] `/dashboard/tenders/1/qualification` → score cards + GO badge + checklist
- [ ] `/dashboard/tenders/1/response` → drafts list + editor + "Generate"
- [ ] `/dashboard/tenders/1/ask` → empty → click the 2 preset questions → answers with sources
- [ ] `/dashboard/tenders/1/exports` → 3 exports + create + download
- [ ] `/dashboard/company/profile` → form + save success
- [ ] `/dashboard/company/credentials` → credentials list
- [ ] `/dashboard/activity` → health, queues, activity log

If every page renders and buttons respond → UI is correct.

Stop with `Ctrl+C`.

---

## WORKFLOW B — Backend API (after fixing Supabase)

### B0. Prerequisites
```powershell
# From repo root
cd C:\Users\LENOVO\Desktop\p2m\P2M-TAI
docker --version      # you have Docker 29 ✔
```

### B1. Fix the Supabase target (required)
The `.env` points to `http://localhost:8000` which is not a running Supabase. Pick ONE:

**Option 1 — Supabase Cloud (easiest):**
1. Create a project at supabase.com (free).
2. Copy Project URL + `anon` key + `service_role` key.
3. In `apps/api/.env`, set:
   ```
   SUPABASE_URL=https://<your-ref>.supabase.co
   SUPABASE_ANON_KEY=<anon>
   SUPABASE_SERVICE_ROLE_KEY=<service_role>
   ```
4. Apply the schema — run the 13 migrations in order in the Supabase SQL editor
   (`infra/supabase/migrations/0001_...` → `0013_...`), or with Supabase CLI:
   ```powershell
   supabase link --project-ref <ref>
   supabase db push
   ```

**Option 2 — Local Supabase CLI:**
```powershell
supabase start        # requires Docker + supabase CLI
# then use the printed API URL + keys in apps/api/.env
# apply migrations:
supabase db reset     # applies infra/supabase/migrations if linked
```

### B2. Add the missing Redis var
Append to `apps/api/.env`:
```
REDIS_URL=redis://localhost:6400/0
```

### B3. Start infra (RabbitMQ + Redis only — not web/api)
```powershell
cd C:\Users\LENOVO\Desktop\p2m\P2M-TAI
docker compose -f docker-compose.app.yml up -d rabbitmq redis
```
- RabbitMQ UI: http://localhost:15672  (admin / admin)
- Redis: `localhost:6400`

### B4. Python env + install
> Your `python` is MSYS/MinGW 3.12 — its venv uses `bin/` not `Scripts/`. If activation misbehaves, use a standard Windows Python 3.11 from python.org, or run the API in Docker (B4-alt).

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # If this path doesn't exist (MSYS venv), use: .\.venv\bin\activate
pip install -r requirements.txt
```
> First install is heavy (spaCy, LangChain, HF). Allow several minutes.

**B4-alt — run API in Docker instead (more reliable):**
```powershell
docker compose -f docker-compose.app.yml up --build api
```
(Requires `.env`'s `SUPABASE_URL` reachable from inside the container → use Cloud or `host.docker.internal`.)

### B5. Start the API
```powershell
cd apps\api
uvicorn src.app:app --reload --port 8100
```
Test:
- http://localhost:8100/health → `{"status":"ok"}`
- http://localhost:8100/docs → Swagger UI (all endpoints)

### B6. Manual API tests (Swagger `/docs`)
- [ ] `GET /api/v1/documents` → `{ "items": [...] }`
- [ ] `POST /api/v1/documents` (multipart `file`=PDF) → returns document record
- [ ] `GET /api/v1/documents/{id}` → `{ "document": {...} }`
- [ ] `GET /api/v1/documents/{id}/status` → `{ "id", "status" }`
- [ ] `GET /api/v1/system/health` → supabase/rabbitmq/redis status
- [ ] `PUT /api/v1/documents/{id}/compliance/{req_id}` → now works (was broken)
- [ ] `GET /api/v1/documents/{id}/responses` → now works (was broken)

### B7. Start pipeline workers (full pipeline only)
Each in its own PowerShell terminal, from `apps\api` with venv active:
```powershell
python -m src.services.ocr.run_worker
python -m src.services.nlp.run_worker
python -m src.services.embedding.run_worker
python -m src.services.compliance.run_worker
python -m src.services.notification.run_worker
```
Then upload a PDF at `/docs` and poll `GET /api/v1/documents/{id}/status` to watch:
`uploaded → reading → indexing → qualifying → qualified → generating → completed`.

---

## WORKFLOW C — Full UI ↔ backend
Not available until Phase 1 (pages wired). Right now the UI is mock, so uploading in the UI will NOT hit the backend. Wire pages first (see `docs/ROADMAP.md` Phase 1), then Workflow A will exercise Workflow B.

---

## Quick "is the code correct?" gate (no servers needed)

```powershell
cd C:\Users\LENOVO\Desktop\p2m\P2M-TAI

# Backend syntax
python -m compileall -q apps/api/src ; echo "py exit=$LASTEXITCODE"

# Frontend typecheck + build
cd apps\web
npx tsc --noEmit ; echo "tsc exit=$LASTEXITCODE"
npx next build   ; echo "build exit=$LASTEXITCODE"
```
All three should print `exit=0`. (Currently verified green.)

---

## Known gotchas
- `SUPABASE_URL` must be a real, reachable project with the 13 migrations applied — otherwise every document endpoint 500s.
- `REDIS_URL` missing → system health Redis check may warn; add it.
- Workers are NOT in docker-compose → in Docker the pipeline stalls unless you run them.
- Frontend `NEXT_PUBLIC_API_URL` may omit `/api/v1`; the client now auto-normalizes it, but keep it as `http://localhost:8100/api/v1` for clarity.
- App entry is `src.app:app` (run from `apps/api`), not `apps.api.src...`.
