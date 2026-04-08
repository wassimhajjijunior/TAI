GENERATE_ENDPOINTS = [
    "POST /api/v1/generate/response",
    "GET /api/v1/responses/{id}",
    "PATCH /api/v1/responses/{id}",
]


async def generate_response(
    payload: dict[str, object], tenant_id: str | None = None
) -> dict[str, object]:
    """Generate a tender response for a document.

    Args:
        payload: Request with document_id, query, and optional sections
        tenant_id: Tenant ID for the request

    Returns:
        Generated response with citations
    """
    from importlib import import_module
    from typing import cast

    from ..core import document_repository
    from ..services.llm.worker import process_generation_manual

    document_id = str(payload.get("document_id", ""))
    query = str(payload.get("query", ""))
    sections = cast(
        list[str], payload.get("sections", ["technical", "financial", "administrative"])
    )

    if not document_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="document_id is required")

    if not tenant_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="tenant_id is required")

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Document not found")

    valid_statuses = {
        "embedding_complete",
        "compliance_completed",
        "generation_complete",
        "generation_ready",
    }
    if document.status not in valid_statuses:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready for generation. Current status: {document.status}",
        )

    result = process_generation_manual(
        document_id=document_id,
        tenant_id=tenant_id,
        query=query or "Generate a comprehensive tender response",
        sections=sections,
    )

    return result


def get_response(response_id: str, tenant_id: str | None = None) -> dict[str, object]:
    """Get a generated response by ID."""
    from importlib import import_module

    from ..core import document_repository

    response = document_repository.get_response(response_id)
    if response is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Response not found")

    return {
        "id": response["id"],
        "document_id": response["document_id"],
        "content": response["content"],
        "citations": response["citations"],
        "created_at": response["created_at"],
        "updated_at": response["updated_at"],
    }


def patch_response(
    response_id: str, payload: dict[str, object], tenant_id: str | None = None
) -> dict[str, object]:
    """Update response content."""
    from importlib import import_module

    from ..core import document_repository

    content = str(payload.get("content", ""))
    if not content:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="content is required")

    existing = document_repository.get_response(response_id)
    if existing is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Response not found")

    updated = document_repository.update_response(response_id, content)
    if not updated:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=500, detail="Failed to update response")

    return get_response(response_id, tenant_id)


def list_document_responses(
    document_id: str, tenant_id: str | None = None
) -> dict[str, object]:
    """List all responses for a document."""
    if not tenant_id:
        from importlib import import_module

        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="tenant_id is required")

    from ..core import document_repository

    responses = document_repository.list_responses(document_id)

    return {
        "document_id": document_id,
        "responses": responses,
        "total": len(responses),
    }


GENERATE_ROUTES = [
    ("POST", "/generate/response", generate_response),
    ("GET", "/responses/{response_id}", get_response),
    ("PATCH", "/responses/{response_id}", patch_response),
    ("GET", "/documents/{document_id}/responses", list_document_responses),
]
