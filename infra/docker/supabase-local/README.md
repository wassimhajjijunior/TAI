# Local Supabase Stack

This folder is reserved for your separate local Supabase Docker setup.

## Usage

- Keep your Supabase compose/config files in this folder.
- Start it independently from the messaging stack.

## Suggested command

```bash
docker compose -f infra/docker/supabase-local/docker-compose.yml up -d
```
