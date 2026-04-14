from importlib import import_module

from ...core.supabase_client import get_supabase_settings
from .metadata import extract_chunk_metadata
from .models import TextChunk


def _get_client():
  settings = get_supabase_settings()
  supabase_module = import_module("supabase")
  create_client = getattr(supabase_module, "create_client")
  return create_client(settings.url, settings.service_role_key)


def run_backfill(limit: int | None = None, offset: int = 0) -> dict[str, int]:
  client = _get_client()
  query = client.table("chunks").select("id,content,position").order("id")
  if limit is not None:
    query = query.range(offset, offset + limit - 1)
  rows = getattr(query.execute(), "data", []) or []

  updated = 0
  non_empty = 0
  for row in rows:
    chunk_id = str(row.get("id", ""))
    content = str(row.get("content", ""))
    position_raw = row.get("position", 0)
    if isinstance(position_raw, int):
      position = position_raw
    elif isinstance(position_raw, str) and position_raw.isdigit():
      position = int(position_raw)
    else:
      position = 0

    metadata = extract_chunk_metadata(TextChunk(index=position, text=content))
    payload = metadata if isinstance(metadata, dict) else {}
    if payload:
      non_empty += 1
    _ = client.table("chunks").update({"metadata": payload}).eq("id", chunk_id).execute()
    updated += 1

  return {"updated": updated, "non_empty": non_empty}


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("--limit", type=int, default=None)
  parser.add_argument("--offset", type=int, default=0)
  args = parser.parse_args()
  _ = args
  result = run_backfill(limit=args.limit, offset=args.offset)
  print(result)
