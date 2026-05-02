import logging
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_EMBEDDING_COMPLETE, QUEUE_EMBEDDING, build_event
from ...core.rabbitmq import consume, publish_event
from .constants import DEFAULT_TENANT_ID, EMBEDDING_BATCH_SIZE, EMBEDDING_DIMENSION
from .hf_client import request_embeddings
from .utils import batch


logger = logging.getLogger(__name__)


def process_nlp_completed(event_payload: dict[str, Any]) -> None:
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", DEFAULT_TENANT_ID))
  filename = str(payload.get("filename", "uploaded-file"))

  if not document_id:
    raise RuntimeError("nlp_completed event missing document_id")

  existing_document = document_repository.get_document(document_id, tenant_id)
  if existing_document is None:
    logger.info(
      "Skipping embedding for missing document_id=%s tenant_id=%s (stale or deleted event)",
      document_id,
      tenant_id,
    )
    return

  if existing_document.status in {"embedding_complete", "compliance_processing", "compliance_completed"}:
    return

  if not document_repository.update_document_status_if_current(
    document_id,
    tenant_id,
    "nlp_completed",
    "embedding_processing",
  ):
    latest = document_repository.get_document(document_id, tenant_id)
    if latest is None or latest.status in {"embedding_complete", "compliance_processing", "compliance_completed"}:
      return
    if latest.status != "embedding_processing":
      _ = document_repository.update_document_status(document_id, tenant_id, "embedding_processing")

  chunks = document_repository.list_document_chunks(document_id)
  if not chunks:
    _ = document_repository.update_document_status(document_id, tenant_id, "embedding_complete")
    completion_event = build_event(
      EVENT_EMBEDDING_COMPLETE,
      {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "filename": filename,
        "status": "embedding_complete",
        "embedding_count": 0,
        "embedding_dimension": EMBEDDING_DIMENSION,
      },
    )
    publish_event(EVENT_EMBEDDING_COMPLETE, completion_event)
    return

  chunk_texts = [
    chunk.get("content_translated") or chunk.get("content", "")
    for chunk in chunks
  ]

  vectors_by_chunk_id: list[tuple[str, list[float]]] = []
  cursor = 0
  try:
    for text_batch in batch(chunk_texts, EMBEDDING_BATCH_SIZE):
      embeddings = request_embeddings(text_batch)
      for vector in embeddings:
        chunk_id = str(chunks[cursor].get("id", ""))
        if not chunk_id:
          raise RuntimeError("Chunk record missing id during embedding persistence")
        vectors_by_chunk_id.append((chunk_id, vector))
        cursor += 1

    document_repository.save_chunk_embeddings(document_id, vectors_by_chunk_id)
    _ = document_repository.update_document_status(document_id, tenant_id, "embedding_complete")

    completion_event = build_event(
      EVENT_EMBEDDING_COMPLETE,
      {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "filename": filename,
        "status": "embedding_complete",
        "embedding_count": len(vectors_by_chunk_id),
        "embedding_dimension": EMBEDDING_DIMENSION,
        "batch_size": EMBEDDING_BATCH_SIZE,
        "batch_count": len(batch(chunk_texts, EMBEDDING_BATCH_SIZE)),
      },
    )
    publish_event(EVENT_EMBEDDING_COMPLETE, completion_event)
  except Exception:
    _ = document_repository.update_document_status(document_id, tenant_id, "embedding_failed")
    raise


def run_embedding_worker() -> None:
  consume(QUEUE_EMBEDDING, process_nlp_completed)
