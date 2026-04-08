RAG_ENDPOINTS = [
    "POST /api/v1/rag/query",
]


async def rag_query(
    payload: dict[str, object], tenant_id: str | None = None
) -> dict[str, object]:
    """Query similar chunks using RAG.

    Args:
        payload: Request body with document_id, query, and optional top_k
        tenant_id: Tenant ID for the request

    Returns:
        List of similar chunks with scores
    """
    from importlib import import_module
    from typing import cast

    from ..core import document_repository
    from ..services.embedding.hf_client import request_embeddings
    from ..services.rag.client import search_similar_chunks

    document_id = str(payload.get("document_id", ""))
    query = str(payload.get("query", ""))
    top_k = int(cast(object, payload.get("top_k", 5)))

    if not document_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="document_id is required")

    if not query:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="query is required")

    if not tenant_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="tenant_id is required")

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Document not found")

    query_embeddings = request_embeddings([query])
    query_embedding = query_embeddings[0]

    chunks = search_similar_chunks(
        document_id=document_id,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    return {
        "document_id": document_id,
        "query": query,
        "results": chunks,
        "total_results": len(chunks),
    }


RAG_ROUTES = [
    ("POST", "/rag/query", rag_query),
]
