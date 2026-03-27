import os
import logging
from importlib import import_module
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_EMBEDDING_COMPLETE, QUEUE_EMBEDDING, build_event
from ...core.rabbitmq import consume, publish_event


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
EMBEDDING_BATCH_SIZE = 32
EMBEDDING_DIMENSION = 1024
HF_DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"

logger = logging.getLogger(__name__)


def _hf_embedding_endpoint() -> str:
  configured = os.getenv("HF_EMBEDDING_API_URL", "").strip()
  if configured:
    return configured

  model_name = os.getenv("HF_EMBEDDING_MODEL", HF_DEFAULT_EMBEDDING_MODEL).strip() or HF_DEFAULT_EMBEDDING_MODEL
  return f"https://router.huggingface.co/hf-inference/models/{model_name}/pipeline/feature-extraction"


def _hf_token() -> str:
  token = os.getenv("HF_TOKEN", "").strip()
  if not token:
    raise RuntimeError("Missing required environment variable: HF_TOKEN")
  return token


def _batch(values: list[str], size: int) -> list[list[str]]:
  if size <= 0:
    return [values]
  return [values[index:index + size] for index in range(0, len(values), size)]


def _coerce_embeddings(payload: object, expected_count: int) -> list[list[float]]:
  if isinstance(payload, dict):
    embeddings_value = payload.get("embeddings") if isinstance(payload.get("embeddings"), list) else None
    if embeddings_value is not None:
      payload = embeddings_value

  if isinstance(payload, list) and payload and all(isinstance(item, (int, float)) for item in payload):
    vectors = [[float(value) for value in payload]]
  elif isinstance(payload, list) and all(isinstance(item, list) for item in payload):
    vectors = [[float(value) for value in row if isinstance(value, (int, float))] for row in payload]
  else:
    raise RuntimeError("Unexpected embedding payload shape from Hugging Face endpoint")

  if len(vectors) != expected_count:
    raise RuntimeError(
      f"Embedding payload count mismatch: expected {expected_count}, got {len(vectors)}"
    )

  for vector in vectors:
    if len(vector) != EMBEDDING_DIMENSION:
      raise RuntimeError(
        f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(vector)}"
      )

  return vectors


def _request_embeddings(texts: list[str]) -> list[list[float]]:
  requests_module = import_module("requests")
  post = getattr(requests_module, "post")

  response = post(
    _hf_embedding_endpoint(),
    headers={"Authorization": f"Bearer {_hf_token()}"},
    json={
      "inputs": texts,
      "options": {"wait_for_model": True},
    },
    timeout=45,
  )
  if not bool(getattr(response, "ok", False)):
    response_text = str(getattr(response, "text", ""))
    raise RuntimeError(f"HF embedding request failed: {getattr(response, 'status_code', 'unknown')} {response_text}")

  payload = response.json()
  if isinstance(payload, dict) and "error" in payload:
    raise RuntimeError(f"HF embedding error: {payload['error']}")

  return _coerce_embeddings(payload, len(texts))


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
    for text_batch in _batch(chunk_texts, EMBEDDING_BATCH_SIZE):
      embeddings = _request_embeddings(text_batch)
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
        "batch_count": len(_batch(chunk_texts, EMBEDDING_BATCH_SIZE)),
      },
    )
    publish_event(EVENT_EMBEDDING_COMPLETE, completion_event)
  except Exception:
    _ = document_repository.update_document_status(document_id, tenant_id, "embedding_failed")
    raise


def run_embedding_worker() -> None:
  consume(QUEUE_EMBEDDING, process_nlp_completed)
