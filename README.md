# P2M-TAI

Tender AI platform organized by vertical feature slices:
- Track A: Document Ingestion & Analysis
- Track B: Response Generation & Export

## Repository Layout

```text
P2M-TAI/
├── apps/
│   ├── web/                # Next.js frontend
│   └── api/                # FastAPI backend
├── packages/
│   ├── shared-types/       # Shared API/data contracts
│   └── ui/                 # Shared UI components
├── infra/
│   ├── supabase/           # Supabase config and SQL
│   └── docker/             # Local stack definitions (separate compose files)
├── docs/
│   ├── architecture/
│   ├── api/
│   └── handoff/
└── .sisyphus/
    └── plans/
```

## Work Ownership

- Track A folders are marked in structure comments/files.
- Track B folders are marked in structure comments/files.
- Shared foundation is under `infra/`, `packages/`, and root configs.

## Docker Split

- Messaging stack (RabbitMQ + Redis):
  - `infra/docker/messaging/docker-compose.yml`
- Local Supabase stack (separate):
  - `infra/docker/supabase-local/docker-compose.yml`
