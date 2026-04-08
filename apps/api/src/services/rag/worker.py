"""RAG worker for processing generation requests via RabbitMQ."""

import logging
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import (
    EVENT_COMPLIANCE_COMPLETED,
    EVENT_LLM_GENERATION,
    QUEUE_RAG,
    build_event,
)
from ...core.rabbitmq import consume, publish_event
from .client import retrieve_context_for_query


logger = logging.getLogger(__name__)


def _load_embedding_client():
    """Lazy load embedding HF client."""
    from importlib import import_module

    hf_client_module = import_module("apps.api.src.services.embedding.hf_client")
    request_embeddings = getattr(hf_client_module, "request_embeddings")
    return request_embeddings


def process_rag_request(event_payload: dict[str, Any]) -> dict[str, object]:
    """Process a compliance completion event by retrieving relevant context via RAG.

    This worker is triggered by EVENT_COMPLIANCE_COMPLETED and retrieves
    relevant chunks from the document for LLM generation.

    Returns the retrieved chunks for use by LLM worker.
    """
    payload = event_payload.get("payload", event_payload)
    document_id = str(payload.get("document_id", ""))
    tenant_id = str(payload.get("tenant_id", ""))
    filename = str(payload.get("filename", "document"))

    if not document_id:
        raise RuntimeError("compliance_completed event missing document_id")

    if not tenant_id:
        raise RuntimeError("compliance_completed event missing tenant_id")

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        logger.info("Skipping RAG for deleted document_id=%s", document_id)
        return {"status": "skipped", "reason": "Document not found"}

    valid_statuses = {"embedding_complete", "compliance_completed", "generation_ready"}
    if document.status not in valid_statuses:
        logger.info(
            "Skipping RAG for document_id=%s with status=%s",
            document_id,
            document.status,
        )
        return {"status": "skipped", "reason": f"Document status is {document.status}"}

    query = str(payload.get("query", ""))
    sections = payload.get("sections", ["technical", "financial", "administrative"])

    if not query:
        requirements = document_repository.list_requirements(document_id)
        if requirements:
            req_texts = [r["requirement_text"] for r in requirements[:10]]
            query = "Generate a complete tender response covering: " + "; ".join(
                req_texts
            )
        else:
            query = "Generate a comprehensive tender response based on the uploaded tender document."

    try:
        request_embeddings = _load_embedding_client()
        query_embeddings = request_embeddings([query])
        query_embedding = query_embeddings[0]

        chunks = retrieve_context_for_query(
            document_id=document_id,
            query=query,
            query_embedding=query_embedding,
            top_k=10,
        )

        if not chunks:
            logger.warning("No relevant chunks found for document_id=%s", document_id)
            return {
                "status": "failed",
                "error": "No relevant context found",
                "document_id": document_id,
            }

        chunk_data = [
            {
                "id": chunk["id"],
                "content": chunk.get("content_translated") or chunk["content"],
                "position": chunk.get("position", 0),
                "similarity": chunk.get("similarity", 0.0),
            }
            for chunk in chunks
        ]

        llm_event = build_event(
            EVENT_LLM_GENERATION,
            {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "filename": filename,
                "query": query,
                "sections": sections,
                "chunks": chunk_data,
                "citations": [
                    {"id": c["id"], "position": c["position"]} for c in chunk_data
                ],
            },
        )
        publish_event(EVENT_LLM_GENERATION, llm_event)

        logger.info(
            "RAG complete: retrieved %d chunks for document_id=%s, published to llm_generation",
            len(chunks),
            document_id,
        )

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_found": len(chunks),
            "chunks": chunk_data,
        }

    except Exception as error:
        logger.exception("RAG processing failed for document_id=%s", document_id)
        return {
            "status": "failed",
            "error": str(error),
            "document_id": document_id,
        }


def run_rag_worker() -> None:
    """Start the RAG worker consuming from RAG queue.

    The RAG worker is triggered by EVENT_COMPLIANCE_COMPLETED and
    publishes to EVENT_LLM_GENERATION for the LLM worker to consume.
    """
    logger.info("Starting RAG worker on queue: %s", QUEUE_RAG)
    consume(QUEUE_RAG, process_rag_request)
