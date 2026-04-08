"""LLM worker for processing generation requests via RabbitMQ."""

import logging
from typing import Any

from ...core import document_repository
from ...core.file_storage import save_response_artifact
from ...core.pipeline_events import (
    EVENT_GENERATION_COMPLETE,
    EVENT_LLM_GENERATION,
    QUEUE_LLM_GENERATION,
    build_event,
)
from ...core.rabbitmq import consume, publish_event
from .client import _detect_language, extract_citations, generate_response


logger = logging.getLogger(__name__)


def process_llm_generation(event_payload: dict[str, Any]) -> None:
    """Process LLM generation event to create a tender response.

    This worker consumes EVENT_LLM_GENERATION events and generates responses
    using the Groq API, then saves them to the database.
    """
    payload = event_payload.get("payload", event_payload)
    document_id = str(payload.get("document_id", ""))
    tenant_id = str(payload.get("tenant_id", ""))
    query = str(payload.get("query", ""))
    sections = payload.get("sections", ["technical", "financial", "administrative"])
    chunks = payload.get("chunks", [])

    if not document_id:
        raise RuntimeError("llm_generation event missing document_id")

    if not tenant_id:
        raise RuntimeError("llm_generation event missing tenant_id")

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        logger.info("Skipping generation for deleted document_id=%s", document_id)
        return

    _ = document_repository.update_document_status(document_id, tenant_id, "generating")

    try:
        context_parts: list[str] = []
        for i, chunk in enumerate(chunks[:10]):
            content = str(chunk.get("content", chunk.get("content_translated", "")))
            position = chunk.get("position", i)
            context_parts.append(f"[Excerpt {i + 1} - Position {position}]:\n{content}")

        context = "\n\n---\n\n".join(context_parts)
        language = _detect_language(query + " " + context)

        logger.info(
            "Starting LLM generation for document_id=%s with %d chunks",
            document_id,
            len(chunks),
        )

        response_text = generate_response(
            query=query,
            context=context,
            sections=sections,
            temperature=0.7,
            max_tokens=4096,
        )

        citations = extract_citations(response_text, chunks)
        citations_data = {
            "citations": citations,
            "chunks_used": len(chunks),
            "language": language,
            "model": "llama-3.3-70b-versatile",
            "sections": sections,
        }

        response_record = document_repository.create_response(
            document_id=document_id,
            content=response_text,
            citations=citations_data,
        )

        artifact_content = {
            "response_id": response_record["id"],
            "document_id": document_id,
            "content": response_text,
            "citations": citations_data,
            "metadata": {
                "chunks_count": len(chunks),
                "language": language,
                "model": "llama-3.3-70b-versatile",
                "sections": sections,
            },
        }
        artifact_path = save_response_artifact(response_record["id"], artifact_content)

        _ = document_repository.update_document_status(
            document_id, tenant_id, "generation_complete"
        )

        completion_event = build_event(
            EVENT_GENERATION_COMPLETE,
            {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "response_id": response_record["id"],
                "status": "generation_complete",
                "citations_count": len(citations),
                "artifact_path": artifact_path,
                "language": language,
            },
        )
        publish_event(EVENT_GENERATION_COMPLETE, completion_event)

        logger.info(
            "LLM generation complete for document_id=%s, response_id=%s",
            document_id,
            response_record["id"],
        )

    except Exception as error:
        logger.exception("LLM generation failed for document_id=%s", document_id)
        _ = document_repository.update_document_status(
            document_id, tenant_id, "generation_failed"
        )
        raise


def process_generation_manual(
    document_id: str,
    tenant_id: str,
    query: str,
    sections: list[str] | None = None,
) -> dict[str, object]:
    """Process a manual generation request (for API endpoint)."""
    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        raise RuntimeError(f"Document not found: {document_id}")

    chunks = document_repository.list_document_chunks(document_id)
    if not chunks:
        raise RuntimeError(f"No chunks found for document: {document_id}")

    from importlib import import_module

    hf_module = import_module("apps.api.src.services.embedding.hf_client")
    request_embeddings = getattr(hf_module, "request_embeddings")

    query_embeddings = request_embeddings([query])
    query_embedding = query_embeddings[0]

    from ..rag.client import search_similar_chunks

    similar_chunks = search_similar_chunks(
        document_id=document_id,
        query_embedding=query_embedding,
        top_k=10,
    )

    if not similar_chunks:
        raise RuntimeError(f"No relevant context found for query: {query}")

    context_parts: list[str] = []
    for i, chunk in enumerate(similar_chunks):
        content = str(chunk.get("content_translated") or chunk.get("content", ""))
        position = chunk.get("position", i)
        context_parts.append(f"[Excerpt {i + 1} - Position {position}]:\n{content}")

    context = "\n\n---\n\n".join(context_parts)
    language = _detect_language(query + " " + context)

    response_text = generate_response(
        query=query,
        context=context,
        sections=sections or ["technical", "financial", "administrative"],
        temperature=0.7,
        max_tokens=4096,
    )

    citations = extract_citations(response_text, similar_chunks)
    citations_data = {
        "citations": citations,
        "chunks_used": len(similar_chunks),
        "language": language,
        "model": "llama-3.3-70b-versatile",
        "sections": sections or ["technical", "financial", "administrative"],
    }

    response_record = document_repository.create_response(
        document_id=document_id,
        content=response_text,
        citations=citations_data,
    )

    artifact_content = {
        "response_id": response_record["id"],
        "document_id": document_id,
        "content": response_text,
        "citations": citations_data,
        "metadata": {
            "chunks_count": len(similar_chunks),
            "language": language,
            "model": "llama-3.3-70b-versatile",
            "sections": sections,
        },
    }
    artifact_path = save_response_artifact(response_record["id"], artifact_content)

    logger.info(
        "Manual generation complete for document_id=%s, response_id=%s",
        document_id,
        response_record["id"],
    )

    return {
        "id": response_record["id"],
        "document_id": document_id,
        "content": response_text,
        "citations": citations_data,
        "artifact_path": artifact_path,
        "created_at": response_record["created_at"],
    }


def run_llm_worker() -> None:
    """Start the LLM worker consuming from LLM generation queue."""
    logger.info("Starting LLM worker on queue: %s", QUEUE_LLM_GENERATION)
    consume(QUEUE_LLM_GENERATION, process_llm_generation)
