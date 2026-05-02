from ...core import document_repository
from ...core.file_storage import save_uploaded_file
from ...core.pipeline_events import EVENT_DOCUMENT_UPLOADED, build_event
from ...core.rabbitmq import publish_event
from .constants import DEFAULT_TENANT_ID, INGESTION_INITIAL_STATUS


def ingest_uploaded_document(filename: str, size_bytes: int, content_type: str, content: bytes) -> dict[str, object]:
  stored = document_repository.create_document(
    tenant_id=DEFAULT_TENANT_ID,
    filename=filename,
    size_bytes=size_bytes,
    content_type=content_type,
  )

  try:
    storage_path = save_uploaded_file(stored.id, filename, content)

    _ = document_repository.update_document_status(stored.id, DEFAULT_TENANT_ID, INGESTION_INITIAL_STATUS)
    upload_event = build_event(
      EVENT_DOCUMENT_UPLOADED,
      {
        "document_id": stored.id,
        "tenant_id": DEFAULT_TENANT_ID,
        "filename": filename,
        "storage_path": storage_path,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "status": INGESTION_INITIAL_STATUS,
      },
    )
    publish_event(EVENT_DOCUMENT_UPLOADED, upload_event)
  except Exception:
    _ = document_repository.update_document_status_if_current(
      stored.id,
      DEFAULT_TENANT_ID,
      INGESTION_INITIAL_STATUS,
      "ocr_failed",
    )
    _ = document_repository.update_document_status_if_current(
      stored.id,
      DEFAULT_TENANT_ID,
      "uploaded",
      "ocr_failed",
    )
    raise

  updated_document = document_repository.get_document(stored.id, DEFAULT_TENANT_ID) or stored
  return {
    "document": document_repository.to_dict(updated_document),
  }
