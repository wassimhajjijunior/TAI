# Local Supabase Stack

This folder contains a separate local Supabase Docker stack for development.

## Usage

- Keep Supabase isolated from `infra/docker/messaging`.
- Configure values using `.env.example` as template.

## Commands

```bash
docker compose -f infra/docker/supabase-local/docker-compose.yml up -d
docker compose -f infra/docker/supabase-local/docker-compose.yml down
```

## Connection details for app env files

- Supabase URL: `http://127.0.0.1:54321` (when full local Supabase API stack is used)
- Local Postgres in this compose: `postgresql://postgres:postgres@localhost:54322/postgres`
- Studio: `http://localhost:54323`

## Note

If you already run a full Supabase stack elsewhere on your laptop, keep this folder as the repository reference and continue using your existing local instance.
