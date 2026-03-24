# P2M-TAI Feature Split Execution Plan

## 1) Goal

Set up and execute a vertical-slice delivery model for the tender platform so two contributors can work in parallel with minimal merge conflicts:

- Track A: Document Ingestion & Analysis
- Track B: Response Generation & Export

## 2) Shared Foundation Scope (Day 1-2)

### Required Outputs

1. Supabase project initialized and team access configured.
2. Monorepo scaffold created with:
   - `apps/web` (Next.js)
   - `apps/api` (FastAPI)
   - `packages/shared-types`
   - `infra/supabase/migrations`
3. Base tables created: `tenants`, `users`.
4. Auth pages and base app layout created.
5. Shared contracts for chunk/RAG request created.

### Task Checklist

- [ ] Validate local dev setup for Node + Python.
- [ ] Configure Supabase env variables in both apps.
- [ ] Apply migration `0001_shared_foundation.sql`.
- [ ] Verify web app compiles.
- [ ] Verify API Python modules compile.

## 3) Track A Scope (Document Ingestion & Analysis)

### Owned Database Objects

- `documents`
- `chunks`
- `requirements`
- `compliance_reports`
- `company_profiles`
- `annexes`

### Owned API Endpoints

- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/status`
- `GET /api/v1/documents/{id}/requirements`
- `GET /api/v1/documents/{id}/compliance`
- `GET/PUT /api/v1/company/profile`
- `GET/POST /api/v1/company/annexes`

### Owned Web Areas

- `/dashboard`
- `/documents/new`
- `/documents/[id]`
- `/documents/[id]/compliance`
- `/settings/company`
- `/settings/annexes`

### Task Checklist

- [ ] Implement upload flow with storage integration.
- [ ] Implement OCR worker integration.
- [ ] Implement NLP chunking + translation.
- [ ] Store embeddings in `chunks`.
- [ ] Build compliance matrix UI.

## 4) Track B Scope (Response Generation & Export)

### Owned Database Objects

- `responses`
- `exports`

### Owned API Endpoints

- `POST /api/v1/rag/query`
- `POST /api/v1/generate/response`
- `GET /api/v1/responses/{id}`
- `PATCH /api/v1/responses/{id}`
- `POST /api/v1/documents/{id}/export`
- `GET /api/v1/exports/{id}/download`

### Owned Web Areas

- `/documents/[id]/respond`
- `/documents/[id]/export`

### Task Checklist

- [ ] Implement RAG retriever using `chunks`.
- [ ] Implement LLM generation flow with citations.
- [ ] Build editor + suggestion panel.
- [ ] Implement export generator (DOCX/PDF).
- [ ] Add download UX and status handling.

## 5) Integration Contract

Track A produces and Track B consumes the shared `Chunk` contract:

```ts
type Chunk = {
  id: string;
  document_id: string;
  content: string;
  content_translated: string;
  embedding: number[];
  position: number;
  page_number: number;
};
```

RAG query contract:

```ts
type RagQueryRequest = {
  document_id: string;
  query: string;
  top_k: number;
};
```

## 6) Branching & Merge Policy

### Branches

- `feature/track-a/*`
- `feature/track-b/*`

### Rules

1. Shared files require review by both contributors.
2. Track-owned files can be merged by track owner.
3. Daily sync: both pull `main` each morning.

## 7) QA Scenarios (Executable)

### Scenario A — Structure Validation

- Tool: `glob`
- Steps:
  1. List `apps/web/src/app/**` and verify all planned pages exist.
  2. List `apps/api/src/routers/**` and verify endpoint ownership files exist.
- Expected:
  - All required folders/files are present.

### Scenario B — Type/Lint Readiness

- Tool: `npm run typecheck:web`
- Steps:
  1. Run command from repo root.
- Expected:
  - Exit code 0.

### Scenario C — Build Readiness

- Tool: `npm run build:web`
- Steps:
  1. Run command from repo root.
- Expected:
  - Exit code 0 with all scaffold routes built.

### Scenario D — Python Module Readiness

- Tool: `python -m compileall apps/api/src`
- Steps:
  1. Compile API package.
- Expected:
  - No syntax errors.

## 8) Done Criteria

- Folder ownership is clear for Track A and Track B.
- Shared contracts exist in `packages/shared-types`.
- Core migrations exist for shared + each track.
- Web and API scaffolds are runnable.
- QA scenarios pass.
