from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from typing import TypedDict, cast
from uuid import uuid4

from .supabase_client import get_supabase_settings


class DocumentRow(TypedDict):
  id: str
  tenant_id: str
  filename: str
  status: str
  size_bytes: int
  content_type: str
  chunk_count: int
  metadata: dict[str, object] | None
  created_at: str


class TenantRow(TypedDict):
  id: str
  name: str


class ChunkRecord(TypedDict):
  id: str
  document_id: str
  content: str
  content_translated: str | None
  position: int


@dataclass(frozen=True)
class DocumentRecord:
  id: str
  tenant_id: str
  filename: str
  status: str
  size_bytes: int
  content_type: str
  chunk_count: int
  metadata: dict[str, object] | None
  created_at: str


def _load_supabase_module():
  return import_module("supabase")


def _get_client():
  settings = get_supabase_settings()
  module = _load_supabase_module()
  create_client = getattr(module, "create_client")
  return create_client(settings.url, settings.service_role_key)


def ensure_tenant_exists(tenant_id: str) -> None:
  client = _get_client()
  tenant: TenantRow = {
    "id": tenant_id,
    "name": "Default Tenant",
  }
  client.table("tenants").upsert(tenant).execute()


def _to_record(row: dict[str, object]) -> DocumentRecord:
  size_value = row.get("size_bytes", 0)
  if isinstance(size_value, int):
    size_bytes = size_value
  elif isinstance(size_value, str) and size_value.isdigit():
    size_bytes = int(size_value)
  else:
    size_bytes = 0

  chunk_count_value = row.get("chunk_count", 0)
  if isinstance(chunk_count_value, int):
    chunk_count = chunk_count_value
  elif isinstance(chunk_count_value, str) and chunk_count_value.isdigit():
    chunk_count = int(chunk_count_value)
  else:
    chunk_count = 0

  metadata_value = row.get("metadata")
  metadata = metadata_value if isinstance(metadata_value, dict) else None

  return DocumentRecord(
    id=str(row["id"]),
    tenant_id=str(row["tenant_id"]),
    filename=str(row["filename"]),
    status=str(row["status"]),
    size_bytes=size_bytes,
    content_type=str(row.get("content_type", "application/octet-stream")),
    chunk_count=chunk_count,
    metadata=cast(dict[str, object] | None, metadata),
    created_at=str(row.get("created_at", datetime.now(timezone.utc).isoformat())),
  )


def create_document(tenant_id: str, filename: str, size_bytes: int, content_type: str) -> DocumentRecord:
  ensure_tenant_exists(tenant_id)
  row: DocumentRow = {
    "id": str(uuid4()),
    "tenant_id": tenant_id,
    "filename": filename,
    "status": "uploaded",
    "size_bytes": size_bytes,
    "content_type": content_type,
    "chunk_count": 0,
    "metadata": None,
    "created_at": datetime.now(timezone.utc).isoformat(),
  }
  client = _get_client()
  try:
    result = client.table("documents").insert(row).execute()
  except Exception as error:
    error_text = str(error)
    if "content_type" not in error_text and "size_bytes" not in error_text:
      raise

    fallback_row = {
      "id": row["id"],
      "tenant_id": row["tenant_id"],
      "filename": row["filename"],
      "status": row["status"],
      "chunk_count": row["chunk_count"],
      "metadata": row["metadata"],
      "created_at": row["created_at"],
    }
    result = client.table("documents").insert(fallback_row).execute()

  data = getattr(result, "data", [])
  if not data:
    raise RuntimeError("Supabase insert failed for documents")
  inserted = data[0]
  normalized = cast(dict[str, object], inserted)
  normalized.setdefault("size_bytes", size_bytes)
  normalized.setdefault("content_type", content_type)
  normalized.setdefault("chunk_count", 0)
  normalized.setdefault("metadata", None)
  return _to_record(normalized)


def list_documents(tenant_id: str) -> list[DocumentRecord]:
  client = _get_client()
  try:
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,size_bytes,content_type,chunk_count,metadata,created_at")
      .eq("tenant_id", tenant_id)
      .order("created_at", desc=True)
      .execute()
    )
  except Exception as error:
    error_text = str(error)
    if "content_type" not in error_text and "size_bytes" not in error_text:
      raise
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,chunk_count,metadata,created_at")
      .eq("tenant_id", tenant_id)
      .order("created_at", desc=True)
      .execute()
    )

  data = getattr(result, "data", [])
  records: list[DocumentRecord] = []
  for item in data:
    normalized = cast(dict[str, object], item)
    normalized.setdefault("size_bytes", 0)
    normalized.setdefault("content_type", "application/octet-stream")
    normalized.setdefault("chunk_count", 0)
    normalized.setdefault("metadata", None)
    records.append(_to_record(normalized))
  return records


def get_document(document_id: str, tenant_id: str) -> DocumentRecord | None:
  client = _get_client()
  try:
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,size_bytes,content_type,chunk_count,metadata,created_at")
      .eq("id", document_id)
      .eq("tenant_id", tenant_id)
      .maybe_single()
      .execute()
    )
  except Exception as error:
    error_text = str(error)
    if "content_type" not in error_text and "size_bytes" not in error_text:
      raise
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,chunk_count,metadata,created_at")
      .eq("id", document_id)
      .eq("tenant_id", tenant_id)
      .maybe_single()
      .execute()
    )

  data = getattr(result, "data", None)
  if not data:
    return None
  normalized = cast(dict[str, object], data)
  normalized.setdefault("size_bytes", 0)
  normalized.setdefault("content_type", "application/octet-stream")
  normalized.setdefault("chunk_count", 0)
  normalized.setdefault("metadata", None)
  return _to_record(normalized)


def delete_document(document_id: str, tenant_id: str) -> bool:
  existing = get_document(document_id, tenant_id)
  if existing is None:
    return False

  client = _get_client()
  _ = client.table("chunks").delete().eq("document_id", document_id).execute()
  _ = client.table("requirements").delete().eq("document_id", document_id).execute()
  _ = client.table("compliance_reports").delete().eq("document_id", document_id).execute()
  _ = (
    client.table("documents")
    .delete()
    .eq("id", document_id)
    .eq("tenant_id", tenant_id)
    .execute()
  )
  return True


def update_document_status(document_id: str, tenant_id: str, status: str) -> bool:
  existing = get_document(document_id, tenant_id)
  if existing is None:
    return False

  client = _get_client()
  _ = (
    client.table("documents")
    .update({"status": status})
    .eq("id", document_id)
    .eq("tenant_id", tenant_id)
    .execute()
  )
  return True


def update_document_nlp_result(
  document_id: str,
  tenant_id: str,
  status: str,
  chunk_count: int,
  metadata: dict[str, object],
) -> bool:
  existing = get_document(document_id, tenant_id)
  if existing is None:
    return False

  client = _get_client()
  _ = (
    client.table("documents")
    .update(
      {
        "status": status,
        "chunk_count": chunk_count,
        "metadata": metadata,
      }
    )
    .eq("id", document_id)
    .eq("tenant_id", tenant_id)
    .execute()
  )
  return True


def replace_document_chunks(document_id: str, chunks: list[str], translated_chunks: list[str]) -> None:
  client = _get_client()
  _ = client.table("chunks").delete().eq("document_id", document_id).execute()

  if not chunks:
    return

  rows: list[dict[str, object]] = []
  for index, chunk in enumerate(chunks):
    translated = translated_chunks[index] if index < len(translated_chunks) else None
    rows.append(
      {
        "id": str(uuid4()),
        "document_id": document_id,
        "content": chunk,
        "content_translated": translated,
        "position": index,
      }
    )

  _ = client.table("chunks").insert(rows).execute()


def list_document_chunks(document_id: str) -> list[ChunkRecord]:
  client = _get_client()
  result = (
    client.table("chunks")
    .select("id,document_id,content,content_translated,position")
    .eq("document_id", document_id)
    .order("position")
    .execute()
  )

  data = getattr(result, "data", [])
  records: list[ChunkRecord] = []
  for item in data:
    normalized = cast(dict[str, object], item)
    position_value = normalized.get("position", 0)
    if isinstance(position_value, int):
      position = position_value
    elif isinstance(position_value, str) and position_value.isdigit():
      position = int(position_value)
    else:
      position = 0

    translated = normalized.get("content_translated")
    records.append(
      {
        "id": str(normalized.get("id", "")),
        "document_id": str(normalized.get("document_id", document_id)),
        "content": str(normalized.get("content", "")),
        "content_translated": str(translated) if isinstance(translated, str) else None,
        "position": position,
      }
    )

  return records


def _vector_to_literal(vector: list[float]) -> str:
  return "[" + ",".join(f"{value:.10f}" for value in vector) + "]"


def save_chunk_embeddings(document_id: str, chunk_vectors: list[tuple[str, list[float]]]) -> None:
  if not chunk_vectors:
    return

  client = _get_client()
  for chunk_id, vector in chunk_vectors:
    _ = (
      client.table("chunks")
      .update({"embedding": _vector_to_literal(vector)})
      .eq("id", chunk_id)
      .eq("document_id", document_id)
      .execute()
    )


def to_dict(document: DocumentRecord) -> dict[str, object]:
  return {
    "id": document.id,
    "tenant_id": document.tenant_id,
    "filename": document.filename,
    "status": document.status,
    "size_bytes": document.size_bytes,
    "content_type": document.content_type,
    "chunk_count": document.chunk_count,
    "metadata": document.metadata,
    "created_at": document.created_at,
  }
