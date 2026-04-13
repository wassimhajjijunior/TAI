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
    metadata: dict[str, object] | None


class RequirementRecord(TypedDict):
    id: str
    document_id: str
    requirement_text: str
    requirement_code: str | None
    category: str | None
    weight: float | None
    met: bool | None
    confidence: float | None
    actual_value: str | None


class CompanyProfileRecord(TypedDict):
    id: str
    tenant_id: str
    profile: dict[str, object]


class ComplianceReportRecord(TypedDict):
    id: str
    document_id: str
    eligibility_score: float | None
    recommendation: str | None
    report: dict[str, object] | None


class NotificationRecord(TypedDict):
    id: str
    event_id: str | None
    document_id: str
    tenant_id: str
    recipient_email: str
    template_name: str
    channel: str
    status: str
    subject: str
    payload: dict[str, object] | None


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


def create_document(
    tenant_id: str, filename: str, size_bytes: int, content_type: str
) -> DocumentRecord:
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
            .select(
                "id,tenant_id,filename,status,size_bytes,content_type,chunk_count,metadata,created_at"
            )
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
            .select(
                "id,tenant_id,filename,status,size_bytes,content_type,chunk_count,metadata,created_at"
            )
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
    _ = (
        client.table("compliance_reports")
        .delete()
        .eq("document_id", document_id)
        .execute()
    )
    _ = client.table("notifications").delete().eq("document_id", document_id).execute()
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


def update_document_status_if_current(
    document_id: str, tenant_id: str, expected_status: str, next_status: str
) -> bool:
    client = _get_client()
    result = (
        client.table("documents")
        .update({"status": next_status})
        .eq("id", document_id)
        .eq("tenant_id", tenant_id)
        .eq("status", expected_status)
        .execute()
    )
    data = getattr(result, "data", None)
    return bool(data)


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


def replace_document_chunks(
    document_id: str,
    chunks: list[str],
    translated_chunks: list[str],
    chunk_metadata: list[dict[str, object]] | None = None,
) -> None:
    client = _get_client()
    _ = client.table("chunks").delete().eq("document_id", document_id).execute()

    if not chunks:
        return

    rows: list[dict[str, object]] = []
    for index, chunk in enumerate(chunks):
        translated = (
            translated_chunks[index] if index < len(translated_chunks) else None
        )
        metadata = (
            chunk_metadata[index]
            if chunk_metadata is not None and index < len(chunk_metadata)
            else None
        )
        metadata_payload = metadata if isinstance(metadata, dict) else {}
        rows.append(
            {
                "id": str(uuid4()),
                "document_id": document_id,
                "content": chunk,
                "content_translated": translated,
                "position": index,
                "metadata": metadata_payload,
            }
        )

    try:
        _ = client.table("chunks").insert(rows).execute()
    except Exception as error:
        error_text = str(error)
        if "metadata" not in error_text:
            raise

        fallback_rows: list[dict[str, object]] = []
        for row in rows:
            fallback_row = dict(row)
            fallback_row.pop("metadata", None)
            fallback_rows.append(fallback_row)
        _ = client.table("chunks").insert(fallback_rows).execute()


def list_document_chunks(document_id: str) -> list[ChunkRecord]:
    client = _get_client()
    try:
        result = (
            client.table("chunks")
            .select("id,document_id,content,content_translated,position,metadata")
            .eq("document_id", document_id)
            .order("position")
            .execute()
        )
    except Exception as error:
        error_text = str(error)
        if "metadata" not in error_text:
            raise
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
        metadata_raw = normalized.get("metadata")
        records.append(
            {
                "id": str(normalized.get("id", "")),
                "document_id": str(normalized.get("document_id", document_id)),
                "content": str(normalized.get("content", "")),
                "content_translated": str(translated)
                if isinstance(translated, str)
                else None,
                "position": position,
                "metadata": metadata_raw if isinstance(metadata_raw, dict) else None,
            }
        )

    return records


def _vector_to_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.10f}" for value in vector) + "]"


def save_chunk_embeddings(
    document_id: str, chunk_vectors: list[tuple[str, list[float]]]
) -> None:
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


def _to_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except Exception:
            return None
    return None


def _to_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def list_requirements(document_id: str) -> list[RequirementRecord]:
    client = _get_client()
    try:
        result = (
            client.table("requirements")
            .select(
                "id,document_id,requirement_text,requirement_code,category,weight,met,confidence,actual_value"
            )
            .eq("document_id", document_id)
            .execute()
        )
        data = getattr(result, "data", [])
        records: list[RequirementRecord] = []
        for item in data:
            normalized = cast(dict[str, object], item)
            records.append(
                {
                    "id": str(normalized.get("id", "")),
                    "document_id": str(normalized.get("document_id", document_id)),
                    "requirement_text": str(normalized.get("requirement_text", "")),
                    "requirement_code": str(normalized.get("requirement_code"))
                    if normalized.get("requirement_code") is not None
                    else None,
                    "category": str(normalized.get("category"))
                    if normalized.get("category") is not None
                    else None,
                    "weight": _to_float(normalized.get("weight")),
                    "met": _to_bool(normalized.get("met")),
                    "confidence": _to_float(normalized.get("confidence")),
                    "actual_value": str(normalized.get("actual_value"))
                    if normalized.get("actual_value") is not None
                    else None,
                }
            )
        return records
    except Exception:
        result = (
            client.table("requirements")
            .select("id,document_id,requirement_text")
            .eq("document_id", document_id)
            .execute()
        )
        data = getattr(result, "data", [])
        fallback_records: list[RequirementRecord] = []
        for item in data:
            normalized = cast(dict[str, object], item)
            fallback_records.append(
                {
                    "id": str(normalized.get("id", "")),
                    "document_id": str(normalized.get("document_id", document_id)),
                    "requirement_text": str(normalized.get("requirement_text", "")),
                    "requirement_code": None,
                    "category": None,
                    "weight": None,
                    "met": None,
                    "confidence": None,
                    "actual_value": None,
                }
            )
        return fallback_records


def replace_requirements(
    document_id: str, requirements: list[dict[str, object]]
) -> None:
    client = _get_client()
    _ = client.table("requirements").delete().eq("document_id", document_id).execute()
    if not requirements:
        return

    rows: list[dict[str, object]] = []
    for requirement in requirements:
        rows.append(
            {
                "id": str(uuid4()),
                "document_id": document_id,
                "requirement_text": str(requirement.get("requirement_text", "")),
                "requirement_code": requirement.get("requirement_code"),
                "category": requirement.get("category"),
                "weight": requirement.get("weight"),
                "met": requirement.get("met"),
                "confidence": requirement.get("confidence"),
                "actual_value": requirement.get("actual_value"),
            }
        )
    _ = client.table("requirements").insert(rows).execute()


def get_company_profile(tenant_id: str) -> CompanyProfileRecord | None:
    client = _get_client()
    result = (
        client.table("company_profiles")
        .select("id,tenant_id,profile")
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    data = getattr(result, "data", None)
    if not data:
        return None
    normalized = cast(dict[str, object], data)
    profile = normalized.get("profile")
    return {
        "id": str(normalized.get("id", "")),
        "tenant_id": str(normalized.get("tenant_id", tenant_id)),
        "profile": cast(
            dict[str, object], profile if isinstance(profile, dict) else {}
        ),
    }


def upsert_company_profile(
    tenant_id: str, profile: dict[str, object]
) -> CompanyProfileRecord:
    ensure_tenant_exists(tenant_id)
    row = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "profile": profile,
    }
    client = _get_client()
    _ = client.table("company_profiles").upsert(row, on_conflict="tenant_id").execute()
    stored = get_company_profile(tenant_id)
    if stored is None:
        raise RuntimeError("Failed to upsert company profile")
    return stored


def upsert_compliance_report(
    document_id: str,
    eligibility_score: float,
    recommendation: str,
    report: dict[str, object],
) -> ComplianceReportRecord:
    client = _get_client()
    row = {
        "id": str(uuid4()),
        "document_id": document_id,
        "eligibility_score": eligibility_score,
        "recommendation": recommendation,
        "report": report,
    }
    _ = (
        client.table("compliance_reports")
        .upsert(row, on_conflict="document_id")
        .execute()
    )
    stored = get_compliance_report(document_id)
    if stored is None:
        raise RuntimeError("Failed to persist compliance report")
    return stored


def get_compliance_report(document_id: str) -> ComplianceReportRecord | None:
    client = _get_client()
    result = (
        client.table("compliance_reports")
        .select("id,document_id,eligibility_score,recommendation,report")
        .eq("document_id", document_id)
        .maybe_single()
        .execute()
    )
    data = getattr(result, "data", None)
    if not data:
        return None
    normalized = cast(dict[str, object], data)
    report_obj = normalized.get("report")
    return {
        "id": str(normalized.get("id", "")),
        "document_id": str(normalized.get("document_id", document_id)),
        "eligibility_score": _to_float(normalized.get("eligibility_score")),
        "recommendation": str(normalized.get("recommendation"))
        if normalized.get("recommendation") is not None
        else None,
        "report": cast(
            dict[str, object] | None,
            report_obj if isinstance(report_obj, dict) else None,
        ),
    }


def create_notification(
    event_id: str,
    document_id: str,
    tenant_id: str,
    recipient_email: str,
    template_name: str,
    channel: str,
    status: str,
    subject: str,
    payload: dict[str, object],
) -> NotificationRecord:
    client = _get_client()
    row = {
        "id": str(uuid4()),
        "event_id": event_id,
        "document_id": document_id,
        "tenant_id": tenant_id,
        "recipient_email": recipient_email,
        "template_name": template_name,
        "channel": channel,
        "status": status,
        "subject": subject,
        "payload": payload,
    }
    result = client.table("notifications").insert(row).execute()
    data = getattr(result, "data", [])
    if not data:
        raise RuntimeError("Failed to insert notification")
    inserted = cast(dict[str, object], data[0])
    payload_obj = inserted.get("payload")
    return {
        "id": str(inserted.get("id", row["id"])),
        "event_id": str(inserted.get("event_id", event_id))
        if inserted.get("event_id") is not None
        else None,
        "document_id": str(inserted.get("document_id", document_id)),
        "tenant_id": str(inserted.get("tenant_id", tenant_id)),
        "recipient_email": str(inserted.get("recipient_email", recipient_email)),
        "template_name": str(inserted.get("template_name", template_name)),
        "channel": str(inserted.get("channel", channel)),
        "status": str(inserted.get("status", status)),
        "subject": str(inserted.get("subject", subject)),
        "payload": cast(
            dict[str, object] | None,
            payload_obj if isinstance(payload_obj, dict) else None,
        ),
    }


def update_notification_status(notification_id: str, status: str) -> bool:
    client = _get_client()
    result = (
        client.table("notifications")
        .update({"status": status})
        .eq("id", notification_id)
        .execute()
    )
    data = getattr(result, "data", None)
    return bool(data)


def get_notification_by_event(
    event_id: str,
    template_name: str,
    recipient_email: str,
) -> NotificationRecord | None:
    client = _get_client()
    result = (
        client.table("notifications")
        .select(
            "id,event_id,document_id,tenant_id,recipient_email,template_name,channel,status,subject,payload"
        )
        .eq("event_id", event_id)
        .eq("template_name", template_name)
        .eq("recipient_email", recipient_email)
        .maybe_single()
        .execute()
    )
    data = getattr(result, "data", None)
    if not data:
        return None
    normalized = cast(dict[str, object], data)
    payload_obj = normalized.get("payload")
    return {
        "id": str(normalized.get("id", "")),
        "event_id": str(normalized.get("event_id"))
        if normalized.get("event_id") is not None
        else None,
        "document_id": str(normalized.get("document_id", "")),
        "tenant_id": str(normalized.get("tenant_id", "")),
        "recipient_email": str(normalized.get("recipient_email", "")),
        "template_name": str(normalized.get("template_name", "")),
        "channel": str(normalized.get("channel", "")),
        "status": str(normalized.get("status", "")),
        "subject": str(normalized.get("subject", "")),
        "payload": cast(
            dict[str, object] | None,
            payload_obj if isinstance(payload_obj, dict) else None,
        ),
    }


class ResponseRecord(TypedDict):
    id: str
    document_id: str
    content: str
    citations: dict[str, object] | None
    created_at: str
    updated_at: str


class ExportRecord(TypedDict):
    id: str
    document_id: str
    response_id: str
    format: str
    file_path: str
    status: str
    tenant_id: str
    created_at: str


def create_response(
    document_id: str,
    content: str,
    citations: dict[str, object] | None = None,
) -> ResponseRecord:
    client = _get_client()
    row = {
        "id": str(uuid4()),
        "document_id": document_id,
        "content": content,
        "citations": citations,
    }
    result = client.table("responses").insert(row).execute()
    data = getattr(result, "data", [])
    if not data:
        raise RuntimeError("Failed to insert response")
    inserted = cast(dict[str, object], data[0])
    citations_obj = inserted.get("citations")
    return {
        "id": str(inserted.get("id", row["id"])),
        "document_id": str(inserted.get("document_id", document_id)),
        "content": str(inserted.get("content", content)),
        "citations": cast(
            dict[str, object] | None,
            citations_obj if isinstance(citations_obj, dict) else None,
        ),
        "created_at": str(inserted.get("created_at", "")),
        "updated_at": str(inserted.get("updated_at", "")),
    }


def get_response(response_id: str) -> ResponseRecord | None:
    client = _get_client()
    result = (
        client.table("responses")
        .select("id,document_id,content,citations,created_at,updated_at")
        .eq("id", response_id)
        .maybe_single()
        .execute()
    )
    data = getattr(result, "data", None)
    if not data:
        return None
    normalized = cast(dict[str, object], data)
    citations_obj = normalized.get("citations")
    return {
        "id": str(normalized.get("id", "")),
        "document_id": str(normalized.get("document_id", "")),
        "content": str(normalized.get("content", "")),
        "citations": cast(
            dict[str, object] | None,
            citations_obj if isinstance(citations_obj, dict) else None,
        ),
        "created_at": str(normalized.get("created_at", "")),
        "updated_at": str(normalized.get("updated_at", "")),
    }


def update_response(response_id: str, content: str) -> bool:
    client = _get_client()
    result = (
        client.table("responses")
        .update({"content": content})
        .eq("id", response_id)
        .execute()
    )
    data = getattr(result, "data", None)
    return bool(data)


def list_responses(document_id: str) -> list[ResponseRecord]:
    client = _get_client()
    result = (
        client.table("responses")
        .select("id,document_id,content,citations,created_at,updated_at")
        .eq("document_id", document_id)
        .order("created_at", desc=True)
        .execute()
    )
    data = getattr(result, "data", [])
    records: list[ResponseRecord] = []
    for item in data:
        normalized = cast(dict[str, object], item)
        citations_obj = normalized.get("citations")
        records.append(
            {
                "id": str(normalized.get("id", "")),
                "document_id": str(normalized.get("document_id", "")),
                "content": str(normalized.get("content", "")),
                "citations": cast(
                    dict[str, object] | None,
                    citations_obj if isinstance(citations_obj, dict) else None,
                ),
                "created_at": str(normalized.get("created_at", "")),
                "updated_at": str(normalized.get("updated_at", "")),
            }
        )
    return records


def create_export(
    document_id: str,
    response_id: str,
    format: str,
    file_path: str,
    tenant_id: str,
) -> ExportRecord:
    ensure_tenant_exists(tenant_id)
    client = _get_client()
    row = {
        "id": str(uuid4()),
        "document_id": document_id,
        "response_id": response_id,
        "format": format,
        "file_path": file_path,
        "status": "processing",
        "tenant_id": tenant_id,
    }
    result = client.table("exports").insert(row).execute()
    data = getattr(result, "data", [])
    if not data:
        raise RuntimeError("Failed to insert export")
    inserted = cast(dict[str, object], data[0])
    return {
        "id": str(inserted.get("id", row["id"])),
        "document_id": str(inserted.get("document_id", document_id)),
        "response_id": str(inserted.get("response_id", response_id)),
        "format": str(inserted.get("format", format)),
        "file_path": str(inserted.get("file_path", file_path)),
        "status": str(inserted.get("status", "processing")),
        "tenant_id": str(inserted.get("tenant_id", tenant_id)),
        "created_at": str(inserted.get("created_at", "")),
    }


def get_export(export_id: str) -> ExportRecord | None:
    client = _get_client()
    result = (
        client.table("exports")
        .select(
            "id,document_id,response_id,format,file_path,status,tenant_id,created_at"
        )
        .eq("id", export_id)
        .maybe_single()
        .execute()
    )
    data = getattr(result, "data", None)
    if not data:
        return None
    normalized = cast(dict[str, object], data)
    return {
        "id": str(normalized.get("id", "")),
        "document_id": str(normalized.get("document_id", "")),
        "response_id": str(normalized.get("response_id", "")),
        "format": str(normalized.get("format", "")),
        "file_path": str(normalized.get("file_path", "")),
        "status": str(normalized.get("status", "")),
        "tenant_id": str(normalized.get("tenant_id", "")),
        "created_at": str(normalized.get("created_at", "")),
    }


def update_export_status(
    export_id: str, status: str, file_path: str | None = None
) -> bool:
    client = _get_client()
    update_data: dict[str, object] = {"status": status}
    if file_path is not None:
        update_data["file_path"] = file_path
    result = client.table("exports").update(update_data).eq("id", export_id).execute()
    data = getattr(result, "data", None)
    return bool(data)


def list_exports(document_id: str, tenant_id: str) -> list[ExportRecord]:
    client = _get_client()
    result = (
        client.table("exports")
        .select(
            "id,document_id,response_id,format,file_path,status,tenant_id,created_at"
        )
        .eq("document_id", document_id)
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    data = getattr(result, "data", [])
    records: list[ExportRecord] = []
    for item in data:
        normalized = cast(dict[str, object], item)
        records.append(
            {
                "id": str(normalized.get("id", "")),
                "document_id": str(normalized.get("document_id", "")),
                "response_id": str(normalized.get("response_id", "")),
                "format": str(normalized.get("format", "")),
                "file_path": str(normalized.get("file_path", "")),
                "status": str(normalized.get("status", "")),
                "tenant_id": str(normalized.get("tenant_id", "")),
                "created_at": str(normalized.get("created_at", "")),
            }
        )
    return records
