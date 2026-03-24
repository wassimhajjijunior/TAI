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
  created_at: str


class TenantRow(TypedDict):
  id: str
  name: str


@dataclass(frozen=True)
class DocumentRecord:
  id: str
  tenant_id: str
  filename: str
  status: str
  size_bytes: int
  content_type: str
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

  return DocumentRecord(
    id=str(row["id"]),
    tenant_id=str(row["tenant_id"]),
    filename=str(row["filename"]),
    status=str(row["status"]),
    size_bytes=size_bytes,
    content_type=str(row.get("content_type", "application/octet-stream")),
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
  return _to_record(normalized)


def list_documents(tenant_id: str) -> list[DocumentRecord]:
  client = _get_client()
  try:
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,size_bytes,content_type,created_at")
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
      .select("id,tenant_id,filename,status,created_at")
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
    records.append(_to_record(normalized))
  return records


def get_document(document_id: str, tenant_id: str) -> DocumentRecord | None:
  client = _get_client()
  try:
    result = (
      client.table("documents")
      .select("id,tenant_id,filename,status,size_bytes,content_type,created_at")
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
      .select("id,tenant_id,filename,status,created_at")
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
  return _to_record(normalized)


def delete_document(document_id: str, tenant_id: str) -> bool:
  existing = get_document(document_id, tenant_id)
  if existing is None:
    return False

  client = _get_client()
  _ = (
    client.table("documents")
    .delete()
    .eq("id", document_id)
    .eq("tenant_id", tenant_id)
    .execute()
  )
  return True


def to_dict(document: DocumentRecord) -> dict[str, object]:
  return {
    "id": document.id,
    "tenant_id": document.tenant_id,
    "filename": document.filename,
    "status": document.status,
    "size_bytes": document.size_bytes,
    "content_type": document.content_type,
    "created_at": document.created_at,
  }
