# P2M-TAI — DevOps & Observability Plan

> Goal: take `main` from "runs on my machine" to a deployed, automated, monitored product.
> Assumes the product is functionally complete first (see §0). Then DevOps (§A), then Observability (§B).

---

## 0. Prerequisite — "full product working" gate

DevOps on a half-wired app is wasted effort. Before §A is worth doing, close these (from `docs/ROADMAP.md` Phase 1–3):

- [ ] Every dashboard page calls the real API (mock-fallback allowed behind `NEXT_PUBLIC_USE_MOCK`).
- [ ] Auth end-to-end: Supabase session + `middleware.ts` guard + JWT verified by API + tenant from JWT.
- [ ] All pipeline workers run and advance a document to `completed`.
- [ ] The 3 broken + 9 stubbed endpoints resolved.
- [ ] One full path works: **upload → OCR → NLP → embed → compliance → RAG → generate → DOCX export → download**.

> DevOps plan below starts the moment that gate is green. It is written to be executed incrementally.

---

## PART A — DEVOPS

### A1. Environments (define once)
| Env | Purpose | Data | URL |
|-----|---------|------|-----|
| `local` | dev on laptop | local Supabase + local Rabbit/Redis | localhost |
| `staging` | pre-prod rehearsal | Supabase branch project + managed MQ | staging.p2m.dev |
| `prod` | live demo / users | Supabase prod + managed MQ | app.p2m.dev |

Rules: identical images across envs; only config differs; promote staging → prod, never build twice.

---

### A2. Containerization (fix what exists)
Current gaps: no DB, no workers, no healthchecks, no storage volume, unpinned images.

- [ ] **Pin base images by digest**: `python:3.11-slim@sha256:…`, `node:20-bookworm-slim@sha256:…`, `redis:7-alpine`, `rabbitmq:3.13-management`.
- [ ] **API Dockerfile**: multi-stage, run as non-root, `pip install --no-cache-dir`, add `HEALTHCHECK`.
- [ ] **Web Dockerfile**: copy `package-lock.json`, use `output: 'standalone'` in `next.config.mjs`, smaller runtime image, non-root.
- [ ] **Workers**: one worker image (same as API) with role via command/env:
      `python -m src.services.<svc>.run_worker`. Add 8 services OR a supervisord process group.
- [ ] **Persistent volume** for `apps/api/storage` (documents/artifacts/exports) — or move to Supabase Storage (preferred for prod).
- [ ] **Healthchecks + `depends_on: condition: service_healthy`** on rabbitmq/redis/api.
- [ ] **`.dockerignore`** complete (exclude `.git`, `node_modules`, `.next`, `storage`, tests).
- [ ] Keep `docker-compose.app.yml` for local; add **`docker-compose.prod.yml`** for prod overlay.

Deliverables: updated `apps/api/Dockerfile`, `apps/web/Dockerfile`, `docker-compose.app.yml`, new `docker-compose.prod.yml`.

---

### A3. CI pipeline (GitHub Actions)
File: `.github/workflows/ci.yml` — runs on every PR/push.

```yaml
name: ci
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
      - run: ruff check apps/api
      - run: python -m compileall -q apps/api/src
      - run: pytest -q apps/api/tests
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run typecheck -w apps/web
      - run: npm run build -w apps/web
      - run: npm run lint -w apps/web
```

- [ ] Add `requirements-dev.txt` (pytest, ruff, httpx).
- [ ] Add `ruff.toml` and ESLint/Prettier configs.
- [ ] Add test suites (see ROADMAP Phase 5) — CI needs something to run.
- [ ] **Required checks** on `main`; block merge if red.

---

### A4. CD pipeline (build → registry → deploy)
File: `.github/workflows/cd.yml` — on push to `main` (after CI green).

- [ ] Build & tag images: `ghcr.io/<user>/p2m-api:<sha>`, `p2m-web:<sha>`.
- [ ] Push to **GitHub Container Registry (ghcr.io)**.
- [ ] Deploy step → platform-specific (see A5).
- [ ] Tag `latest` + semver on releases.
- [ ] Post-deploy smoke test: `curl -f https://api…/health` + `curl -f https://app… .

---

### A5. Hosting topology (two options)

**Option 1 — Managed (recommended for PFE, low ops):**
| Component | Service |
|-----------|---------|
| Web (Next.js) | **Vercel** (native Next deploy, preview envs) |
| API + 8 workers | **Railway** or **Fly.io** (Docker, private networking) |
| Redis | Railway/Upstash |
| RabbitMQ | CloudAMQP (free tier) |
| Postgres+pgvector | **Supabase Cloud** |
| Storage | Supabase Storage (S3-compatible) |

Cost: ~free–$10/mo. Zero server admin. Preview deploys per PR.

**Option 2 — Single VPS (Docker Compose + Caddy):**
- One $6 VPS (Hetzner/DigitalOcean).
- `docker-compose.prod.yml` + **Caddy** reverse proxy (auto TLS).
- **Watchtower** for image auto-update, or a `deploy.sh` pulled by CD via SSH.
- Backups: nightly `pg_dump` + storage rsync.

Deliverables: `Caddyfile`, `deploy.sh`, `docs/DEPLOY.md` runbook.

---

### A6. Secrets & config
- [ ] **GitHub Secrets**: `SUPABASE_*`, `MISTRAL_API_KEY`, `GROQ_API_KEY`, `HF_TOKEN`, `SENDGRID_*`, `RABBITMQ_URL`, `REDIS_URL`, registry token.
- [ ] Per-env `.env.prod.example` (committed, no values) documenting every var (add missing `HF_TOKEN`, `REDIS_URL`).
- [ ] **Never** commit real `.env` (already ignored — verify). Consider `gitleaks` in CI.
- [ ] Rotate any key ever exposed in history (the old `admin/admin` MQ creds).

---

### A7. Database migrations
- [ ] Make `infra/supabase/migrations` the single source of truth.
- [ ] Apply via **Supabase CLI** in CI/CD: `supabase db push --linked` (staging then prod).
- [ ] Add **rollback** files or require forward-only migrations.
- [ ] Add a **seed** task for demo data (`supabase/seed.sql`).
- [ ] Snapshot before prod migration (Supabase PITR / manual dump).

---

### A8. Release hygiene
- [ ] Branch strategy: `main` protected; feature branches; PR template.
- [ ] Conventional commits + auto changelog (`git-cliff` or release-please).
- [ ] Semantic versioning tags; `CHANGELOG.md`.
- [ ] `CODEOWNERS` fixed to real paths.
- [ ] Remove nested `apps/web/.git`; single repo, single history.

### A9. Security hardening checklist
- [ ] Non-root containers; read-only FS where possible.
- [ ] CORS locked to real origins (not `*`).
- [ ] Rate limiting at the proxy (Caddy/Cloudflare).
- [ ] Secrets never logged; structured logs redact tokens.
- [ ] Dependency scanning: Dependabot + `pip-audit` + `npm audit` in CI.

---

## PART B — OBSERVABILITY (builds directly on A)

Stack choice (matches your Prometheus + Grafana + tracing experience): **Prometheus + Grafana + Loki + Tempo/Jaeger + OpenTelemetry**, with **Sentry** for frontend/backend exceptions.

### B1. Metrics (Prometheus)
- [ ] **API**: `prometheus-fastapi-instrumentator` → `/metrics` (request count, latency histogram, in-flight, error rate).
- [ ] **Workers**: custom counters/histograms per stage:
      `pipeline_stage_duration_seconds{stage="ocr|nlp|embed|compliance|llm|export"}`, `pipeline_documents_total{status}`, `pipeline_failures_total{stage,reason}`.
- [ ] **RabbitMQ**: `rabbitmq_prometheus` plugin → **queue depth, consumers, publish/deliver rate, unacked** (most important signal).
- [ ] **Redis**: `redis_exporter` (memory, hit rate).
- [ ] **DB**: Supabase metrics or `postgres_exporter` (connections, slow queries).
- [ ] **Node/host**: `node-exporter` (CPU/mem/disk).
- [ ] **Business metrics**: `tenders_processed_total`, `compliance_go_rate`, `avg_response_generation_seconds`, `exports_created_total`.

### B2. Logs (Loki)
- [ ] **Structured JSON logs** in API and all workers (`structlog` / stdlib JSON formatter).
- [ ] Include `trace_id`, `tenant_id`, `document_id`, `stage`, `event`.
- [ ] Promtail/Alloy ships container logs → Loki; Grafana queries by `{app="p2m-api"}`.
- [ ] **No `print()`** — replace with logger.

### B3. Tracing (OpenTelemetry → Tempo/Jaeger)
- [ ] Instrument FastAPI (`opentelemetry-instrumentation-fastapi`).
- [ ] Propagate context across **RabbitMQ** messages (inject `traceparent` in event payload) so a document's full pipeline is one trace.
- [ ] Span per stage: upload → ocr → nlp → embed → compliance → llm → export.
- [ ] Export to Tempo (or Jaeger/Zipkin — you already know Zipkin).

### B4. Grafana dashboards (provisioned as JSON, committed)
- [ ] **API overview**: RPS, p50/p95/p99 latency, 5xx rate, in-flight.
- [ ] **Pipeline health**: queue depth per queue, consumer count, stage latency heatmap, DLQ count.
- [ ] **Workers**: active, throughput, failure rate per stage.
- [ ] **Business**: tenders/day, go-rate, avg generation time.
- [ ] **Infra**: CPU/mem/disk, Redis, DB connections.
Store dashboards in `infra/observability/grafana/dashboards/*.json` + datasource provisioning.

### B5. Alerting (Alertmanager)
- [ ] Queue backlog high (`rabbitmq_queue_messages > N` for 5m) → pipeline stuck.
- [ ] API 5xx rate > 2% for 5m.
- [ ] p95 latency > 2s for 10m.
- [ ] Worker down (no `pipeline_stage` metrics for 5m).
- [ ] Disk > 80%, DB connections > 80%.
- [ ] Route to email (SendGrid you already have) or Slack/Discord.

### B6. Error tracking (Sentry)
- [ ] Backend + frontend Sentry SDKs; release tagging; source maps for web.
- [ ] Alert on new/unhandled exceptions, grouped.

### B7. Uptime & SLOs
- [ ] External uptime monitor (UptimeRobot/Better Stack) on `/health` and app root.
- [ ] Define SLOs: API availability 99.5%, p95 < 1.5s, pipeline success ≥ 95%.
- [ ] Status page (optional).

---

## Implementation order (recommended)

| # | Milestone | Depends on | Effort |
|---|-----------|-----------|--------|
| 1 | Product-completion gate (§0) | — | L |
| 2 | CI (lint + typecheck + build + tests) | gate | M |
| 3 | Docker hardening + workers + prod compose | gate | L |
| 4 | Deploy staging (Option 1 or 2) | 2,3 | M |
| 5 | DB migration automation + secrets | 4 | M |
| 6 | CD pipeline (images → deploy → smoke) | 2,4 | M |
| 7 | **Metrics** (Prometheus + exporters + /metrics) | 4 | M |
| 8 | **Structured logs** → Loki | 4 | M |
| 9 | **Tracing** (OTel, cross-rabbit) | 7 | M |
| 10 | **Grafana dashboards** (provisioned) | 7,8 | M |
| 11 | **Alerting** + Sentry + uptime | 7–10 | S |
| 12 | Prod deploy + SLO/status page | all | M |

---

## Files to create (checklist)

```
.github/workflows/ci.yml
.github/workflows/cd.yml
apps/api/Dockerfile            (harden)
apps/web/Dockerfile            (standalone + lockfile)
docker-compose.prod.yml
Caddyfile
deploy.sh
apps/api/requirements-dev.txt
apps/api/ruff.toml
apps/api/tests/…
apps/web/eslint.config.mjs
.github/dependabot.yml
infra/observability/prometheus.yml
infra/observability/alerts.yml
infra/observability/grafana/provisioning/datasources.yml
infra/observability/grafana/dashboards/*.json
infra/observability/docker-compose.observability.yml
docs/DEPLOY.md
docs/OBSERVABILITY.md
```

---

## Definition of done

- Push to `main` → CI green → images built → auto-deployed to staging → smoke test passes.
- One click promotes staging → prod.
- A dashboard shows RPS/latency/errors + queue depth + per-stage pipeline latency.
- An alert fires when the pipeline stalls or API errors spike.
- Any document can be traced end-to-end (upload → export) by `trace_id`.
- Rollback = redeploy previous image tag in < 2 min.
