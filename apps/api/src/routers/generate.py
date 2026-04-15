from fastapi import HTTPException
from typing import cast

GENERATE_ENDPOINTS = [
    "POST /api/v1/generate/response",
    "GET /api/v1/responses/{id}",
    "PATCH /api/v1/responses/{id}",
    "GET /api/v1/documents/{id}/responses",
    "POST /api/v1/documents/{id}/responses/generate",
    "GET /api/v1/documents/{id}/responses/{response_id}",
    "PUT /api/v1/documents/{id}/responses/{response_id}",
    "DELETE /api/v1/documents/{id}/responses/{response_id}",
]


async def generate_response(
    payload: dict[str, object], tenant_id: str | None = None
) -> dict[str, object]:
    from ..core import document_repository
    from ..services.llm.worker import process_generation_manual

    document_id = str(payload.get("document_id", ""))
    query = str(payload.get("query", ""))
    sections = cast(
        list[str], payload.get("sections", ["technical", "financial", "administrative"])
    )

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    valid_statuses = {
        "embedding_complete",
        "compliance_completed",
        "generation_complete",
        "generation_ready",
    }
    if document.status not in valid_statuses:
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
    from ..core import document_repository

    response = document_repository.get_response(response_id)
    if response is None:
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
    from ..core import document_repository

    content = str(payload.get("content", ""))
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    existing = document_repository.get_response(response_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Response not found")

    updated = document_repository.update_response(response_id, content)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update response")

    return get_response(response_id, tenant_id)


def list_document_responses(
    document_id: str,
    tenant_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    from ..core import document_repository

    result = document_repository.list_responses(document_id, limit=limit, offset=offset)

    return {
        "document_id": document_id,
        "responses": result["items"],
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
    }


def delete_document_response(
    document_id: str,
    response_id: str,
    tenant_id: str | None = None,
) -> dict[str, str]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    from ..core import document_repository

    deleted = document_repository.delete_response(response_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Response not found")
    return {"status": "deleted", "id": response_id}


GENERATE_ROUTES = [
    ("POST", "/generate/response", generate_response),
    ("GET", "/responses/{response_id}", get_response),
    ("PATCH", "/responses/{response_id}", patch_response),
    ("GET", "/documents/{document_id}/responses", list_document_responses),
    ("POST", "/documents/{document_id}/responses/generate", generate_response),
    ("GET", "/documents/{document_id}/responses/{response_id}", get_response),
    ("PUT", "/documents/{document_id}/responses/{response_id}", patch_response),
    (
        "DELETE",
        "/documents/{document_id}/responses/{response_id}",
        delete_document_response,
    ),
]
