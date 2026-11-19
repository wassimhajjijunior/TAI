# P2M-TAI — Project Stage Assessment & Roadmap

> Generated from a full codebase audit (backend routers/services, frontend pages, infra/CI).
> Goal: turn this into a strong **fullstack + AI** PFE portfolio piece.

---

## 1. SNAPSHOT — Where the project stands

**Overall maturity: ~60–65%.** A real AI engine exists behind a demo frontend, with no auth, no tests, and no CI.

| Layer | Grade | Verdict |
|-------|-------|---------|
| **AI / Backend services** | 🟢 Strong | 9 services genuinely implemented (Mistral OCR, spaCy+chonkie NLP, BGE-M3 embeddings, pgvector RAG, Groq LLM, python-docx export, SendGrid). ~5,000 LOC. Not stubs. |
| **API surface** | 🟡 Partial | 25/37 endpoints implemented, **3 broken**, **9 stubbed**. No auth, hardcoded tenant, no models layer. |
| **Database** | 🟢 Strong | 13 real migrations: pgvector(1024), HNSW index, `match_chunks` RPC, tenancy, idempotency. |
| **Frontend** | 🔴 Demo shell | 16 pages, **0 wire to the API** — all hardcoded fixtures + `setTimeout`. Real API client + upload component exist but are **orphaned**. |
| **Auth** | 🔴 Missing | Supabase login/register forms work in isolation; no session, no middleware, no route guard, no JWT to API. |
| **Infra / CI** | 🔴 Minimal | Docker has 4 services (no DB, no workers, no healthchecks, no volumes). **No CI, no tests, no linter.** Non-reproducible builds (`"latest"`). |

### What this means in one line
> You built the hard part (the AI pipeline) correctly, but the product is not *connected*: the frontend is a mockup, the API has no security, and nothing is tested or automated.

### Immediate wins already secured
- ✅ Working tree clean, all work committed on `Final-start`.
- ✅ Frontend `tsc --noEmit` now **passes** (fixed `components/ui/modal.tsx` broken JSX + `app/not-found.tsx` invalid `pill` prop).

---

## 2. BRANCH VERDICT

| Branch | Reality |
|--------|---------|
| **`Final-start`** (current) | ✅ The real final state = `origin/main` + all mock-frontend work (May 8). |
| `origin/main` | Behind by 26 files. |
| local `main` | **Stale** (Mar 25) — do not use. |
| `compliance/nlp/nlp_service/ocr-service` | Already in main lineage (0 commits ahead). |
| `notif-service`, `rag-service`, `test` | Only stray "trash"/"nothing" commits — nothing real to merge. |

**Action:** `Final-start` is the final result. Promote it to `main`. Nothing needs merging *in*.

```bash
# After reviewing, from repo root:
git push origin Final-start:main
# or open a PR: Final-start -> main on GitHub
```

---

## 3. GAP REGISTER (evidence-backed)

### A. Broken endpoints (will 500 at runtime)
1. `PUT /documents/{id}/compliance/{req_id}` → calls missing `document_repository.update_requirement_status`.
2. `DELETE /documents/{id}/responses/{rid}` → calls missing `document_repository.delete_response`.
3. `GET /documents/{id}/responses` → passes `limit/offset` to `list_responses(document_id)` (signature mismatch → TypeError).

### B. Stubbed endpoints (silent no-ops)
4. Company annexes: `GET` returns `{items:[]}`, `POST` persists nothing (table exists).
5. `POST /documents/{id}/compliance/check` returns "triggered", publishes nothing.
6. RAG history `GET`/`DELETE` return empty/cleared, no storage.
7. `GET /system/activity` returns empty, no activity table.
8. `/workers/rag|llm|export` return "manual_trigger_required".
9. `GET /system/messaging/topology` hardcodes `messages:0, consumers:0`.

### C. Security / tenancy
10. **No auth anywhere.** Every endpoint public. No `Depends`/JWT/RBAC.
11. Hardcoded `DEFAULT_TENANT_ID` in 7 files; `users` table unused.
12. API client sends no `Authorization` header.

### D. Frontend wiring
13. **All 16 pages mocked** (dashboard, tenders, new, activity, overview, qualification, response, ask, exports, company/profile, company/credentials).
14. Real `document-upload-dropzone.tsx` + `useApi`/`useTenderActions` hooks are **orphaned**.
15. **7 contract mismatches** (e.g. `getTender` expects flat object vs `{document:{...}}`; export body `{type}` vs `{response_id,format}`; `getExports` shape; `/exports/{id}` route missing; `deleteAnnex` route missing).
16. Base URL bug: `.env` sets `http://localhost:8100` but routes live under `/api/v1` → local 404s.
17. No `middleware.ts`, no session provider; login doesn't redirect.
18. Dead buttons: overview Edit/Export, TopBar Approve, Sidebar Log Out.
19. No per-route loading/error states; `ErrorState` unused.

### E. Infra / quality
20. **No CI** (`.github/` only has CODEOWNERS), **no tests** (0 files), **no linter**.
21. 8 `run_worker.py` processes **not containerized** → pipeline stalls in Docker.
22. No DB in app compose; supabase-local provides raw Postgres only.
23. No healthchecks, no persistent `storage` volume, no migration job.
24. Non-reproducible builds: `next/react/typescript/supabase-js: "latest"`; web Dockerfile ignores lockfile.
25. `HF_TOKEN`, `REDIS_URL` missing from `.env.example`; web Docker missing Supabase env in Docker.
26. Repo hygiene: nested `apps/web/.git`, committed `=0.3.0`, `tsconfig.tsbuildinfo`, `.env.exemple`.
27. Stale CODEOWNERS/handoff paths (`app/documents/*` moved to `dashboard/tenders/*`).

---

## 4. ROADMAP — Priority-ordered TODO

Legend: effort S(<2h) · M(half-day) · L(1–2 days) · XL(3+ days). **CV** = how much it strengthens your portfolio story.

### PHASE 0 — Consolidate & hygiene (do first, ~half day)
- [ ] Push `Final-start` → `origin/main` (PR). **CV: high** (clean history shows discipline)
- [ ] Delete junk: `=0.3.0`, `tsconfig.tsbuildinfo`, `infra/supabase/.env.exemple`
- [ ] Remove nested `apps/web/.git`; add to `.gitignore`
- [ ] Fix `.env.example` + `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8100/api/v1`
- [ ] Add `HF_TOKEN`, `REDIS_URL` to `apps/api/.env.example`
- [ ] Update CODEOWNERS + handoff docs to real paths

### PHASE 1 — Make it genuinely fullstack (the biggest CV win)
**This is the single most important phase: a real frontend calling a real API.**
- [ ] Fix 3 broken backend endpoints (add `update_requirement_status`, `delete_response` repo methods; fix `list_responses` signature) — **S**
- [ ] Reconcile the 7 contract mismatches (align shapes: `{document:{...}}`, `{items}`, export request/response, add missing `/exports/{id}` + `DELETE /company/annexes/{id}`) — **M**
- [ ] Wire `/dashboard/tenders` → `getTenders()` with loading/error — **M**
- [ ] Mount real `DocumentUploadDropzone` on `/tenders/new` (replace mock) — **S**
- [ ] Wire `/tenders/[id]/overview` → `getTender()` + `useTenderStatus` polling — **M**
- [ ] Wire `/qualification` → `getComplianceScore`/`getComplianceRequirements`/`updateRequirementStatus` — **M**
- [ ] Wire `/response` → `getDraftResponses`/`generate`/`update`/`delete` — **M**
- [ ] Wire `/ask` → `queryRAG` + history — **M**
- [ ] Wire `/exports` → `getExports`/`createExport`/download — **M**
- [ ] Wire `/company/profile` + `/credentials` (annexes) — **M**
- [ ] Wire `/dashboard` + `/activity` → `getSystemHealth`/`getActivityLogs`/`getMessagingTopology` — **S**
- [ ] Add mock-fallback flag `NEXT_PUBLIC_USE_MOCK` so the demo still works offline while real wiring exists — **S** **CV: high** (shows both)

### PHASE 2 — Auth end-to-end (interviewer magnet)
- [ ] Add `@supabase/ssr` + `middleware.ts`; server-read session; protect `/dashboard/**` — **L**
- [ ] Login/register redirect + session provider in root layout — **S**
- [ ] Attach Supabase JWT in `lib/api/client.ts` as `Authorization: Bearer` — **S**
- [ ] Backend: `Depends(verify_jwt)` → derive `tenant_id` from user (remove hardcoded tenant) — **L**
- [ ] Add RBAC (`admin` vs `candidate`) with `require_role` — **M** **CV: very high** (auth+RBAC is exactly your target stack)
- [ ] Wire Sidebar "Log Out" → `signOut` + redirect

### PHASE 3 — Complete the stubs (product completeness)
- [ ] Company annexes: upload/list/delete + Supabase Storage — **M**
- [ ] Compliance re-check: `POST /check` publishes `document_uploaded`-style event to re-run engine — **S**
- [ ] RAG history: persist messages table + endpoints — **M**
- [ ] Activity log: `activity_log` table + writes on key actions + `GET /system/activity` — **M**
- [ ] Worker trigger endpoints → actually dispatch jobs — **S**
- [ ] Topology counts → real `QueueDeclareOk` — **S**

### PHASE 4 — Infra & DevEx (makes the repo look professional)
- [ ] Docker: add 8 worker services (or one worker image with role env) to compose — **L**
- [ ] Add Supabase (or document external) + migration job + persistent `storage` volume — **M**
- [ ] Add `healthcheck` + `condition: service_healthy` on rabbitmq/redis/api/web — **S**
- [ ] Pin versions (`next/react/ts/node`, Python `==`), commit lockfiles, Dockerfile copies lockfile — **S**
- [ ] Web Docker: pass `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY` — **S**
- [ ] Add `.github/workflows/ci.yml`: ruff + pytest + `tsc --noEmit` + `next build` — **M** **CV: high**
- [ ] Add linters: `ruff.toml`, ESLint + Prettier — **S**
- [ ] Root `package.json`: add `lint`, `test`, `dev:api`, unified scripts — **S**

### PHASE 5 — Tests (turns "demo" into "engineering")
- [ ] Backend: `pytest` + `TestClient` for documents/compliance/rag/export routers — **L**
- [ ] Backend: unit tests for `compliance/engine.py` (rules) + `nlp/chunking.py` — **M**
- [ ] Frontend: `vitest` for `lib/api/*` (mock fetch) — **M**
- [ ] One Playwright smoke test: upload → overview renders — **M** **CV: very high** (tests are rare in student projects)

### PHASE 6 — AI depth / differentiators (what makes it special)
- [ ] Compliance engine: upgrade from 4 hardcoded rules → **LLM adjudication** with citations + confidence (you already have Groq) — **XL** **CV: very high**
- [ ] Citations UI in response editor (show source clause → generated text) — **M**
- [ ] Streaming LLM responses (dead `generate_stream` exists) via SSE — **M**
- [ ] RAG evaluation harness (precision@k / hit-rate on a labeled set) — **L** **CV: very high** (shows you measure AI quality)
- [ ] Multi-language: the NLP translate step exists — surface FR/AR/EN in UI — **M**
- [ ] Fine-tuning or re-rank step (optional stretch) — **XL**

### PHASE 7 — Portfolio polish
- [ ] Rewrite README with real screenshots + architecture diagram + "what works" matrix — **M**
- [ ] Seed script with 2–3 realistic tenders — **S**
- [ ] Live deploy (Vercel frontend + Railway/Fly API + Supabase cloud) — **L** **CV: high** (a live link on a CV is gold)
- [ ] 2-min demo video / GIF — **S**
- [ ] `docs/ADR/` — record 3–4 key decisions (why RabbitMQ, why pgvector, why modular monolith) — **S** **CV: high**

---

## 5. RECOMMENDED ORDER (maximum CV ROI first)

1. **Phase 0** — consolidate (half day)
2. **Phase 1** — connect frontend↔backend (biggest visible jump)
3. **Phase 4 (CI + pinning)** — cheap, makes repo look professional
4. **Phase 2 (auth + RBAC)** — matches your Track A/B target exactly
5. **Phase 3 (stubs)** — completeness
6. **Phase 5 (tests)** — credibility
7. **Phase 6 (AI depth)** — the "wow" / differentiation
8. **Phase 7 (polish + deploy)** — presentation

> If time is short for PFE: do **Phase 0 → 1 → 4(CI only) → 2 → 7(deploy)**. That alone gives you a demonstrable, secure, CI-backed fullstack AI app with a live link.

---

## 6. SCOPE DISCIPLINE — do NOT do now
- ❌ Do not build more mock pages — replace mocks with real wiring instead.
- ❌ Do not add a new frontend framework or state library — the current stack is fine.
- ❌ Do not split into真 microservices — the modular monolith + workers is the right size for PFE.
- ❌ Do not chase new AI features before the app actually works end-to-end.
- ❌ Do not merge `notif-service`/`rag-service`/`test` — they carry only junk commits.

---

## 7. WHAT IS ALREADY GOOD (lean into this in your pitch)
- Real hybrid **rules + RAG + LLM** pipeline (not a ChatGPT wrapper).
- **pgvector** with HNSW + `match_chunks` RPC = genuine vector search.
- **Async event choreography** (RabbitMQ) across 5 pipeline stages.
- **13 migrations** with tenancy, idempotency, indexes.
- Multi-language NLP (langdetect + translation + chunking).
- Docker-based monorepo with typed API client.

These are the things that read as "real engineer", not "tutorial follower" — protect them while you finish the wiring.
