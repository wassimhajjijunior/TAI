import logging
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_NLP_COMPLETED, QUEUE_NLP, build_event
from ...core.rabbitmq import consume, publish_event
from .chunking import build_chonkie_chunks, detect_language
from .constants import (
  DEFAULT_TENANT_ID,
  MAX_CHUNK_TOKENS,
)
from .metadata import build_chunk_metadata, build_metadata
from .text_utils import clean_text_preserve_structure
from .translation import translate_chunks_to_english


logger = logging.getLogger(__name__)


def process_ocr_complete(event_payload: dict[str, Any]) -> None:
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", DEFAULT_TENANT_ID))
  filename = str(payload.get("filename", "uploaded-file"))
  ocr_text = str(payload.get("ocr_text", ""))

  if not document_id:
    raise RuntimeError("ocr_complete event missing document_id")

  existing_document = document_repository.get_document(document_id, tenant_id)
  if existing_document is None:
    logger.info(
      "Skipping NLP for missing document_id=%s tenant_id=%s (stale or deleted event)",
      document_id,
      tenant_id,
    )
    return

  if existing_document.status in {"nlp_completed", "embedding_processing", "embedding_complete", "compliance_processing", "compliance_completed"}:
    return
  if existing_document.status == "nlp_processing":
    return

  if not document_repository.update_document_status_if_current(
    document_id,
    tenant_id,
    "ocr_complete",
    "nlp_processing",
  ):
    latest = document_repository.get_document(document_id, tenant_id)
    if latest is None:
      logger.info(
        "Skipping NLP for deleted document during status transition document_id=%s tenant_id=%s",
        document_id,
        tenant_id,
      )
      return
    if latest.status in {"nlp_processing", "nlp_completed", "embedding_processing", "embedding_complete", "compliance_processing", "compliance_completed"}:
      return
    if latest.status != "nlp_processing":
      _ = document_repository.update_document_status(document_id, tenant_id, "nlp_processing")

  cleaned_text = clean_text_preserve_structure(ocr_text)
  language, lang_confidence = detect_language(cleaned_text)
  chunks = build_chonkie_chunks(cleaned_text, MAX_CHUNK_TOKENS)
  translated_chunks = translate_chunks_to_english(chunks, language)
  chunk_metadata = build_chunk_metadata(chunks)
  metadata = build_metadata(chunks, language, lang_confidence)

  chunk_texts = [chunk.text for chunk in chunks]
  try:
    document_repository.replace_document_chunks(
      document_id,
      chunk_texts,
      translated_chunks,
      chunk_metadata,
    )
  except Exception as error:
    error_text = str(error)
    if "chunks_document_id_fkey" in error_text or "is not present in table \"documents\"" in error_text:
      latest_document = document_repository.get_document(document_id, tenant_id)
      if latest_document is None:
        logger.info(
          "Skipping stale NLP event after FK miss for deleted document_id=%s tenant_id=%s",
          document_id,
          tenant_id,
        )
        return
      _ = document_repository.update_document_status(document_id, tenant_id, "nlp_failed")
      raise
    _ = document_repository.update_document_status(document_id, tenant_id, "nlp_failed")
    raise

  _ = document_repository.update_document_nlp_result(
    document_id=document_id,
    tenant_id=tenant_id,
    status="nlp_completed",
    chunk_count=len(chunks),
    metadata=metadata,
  )

  completion_event = build_event(
    EVENT_NLP_COMPLETED,
    {
      "document_id": document_id,
      "tenant_id": tenant_id,
      "filename": filename,
      "status": "nlp_completed",
      "chunk_count": len(chunks),
      "metadata": metadata,
    },
  )
  publish_event(EVENT_NLP_COMPLETED, completion_event)


def run_nlp_worker() -> None:
  consume(QUEUE_NLP, process_ocr_complete)
  
