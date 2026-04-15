from fastapi import HTTPException

RAG_ENDPOINTS = [
    "POST /api/v1/rag/query",
    "GET /api/v1/documents/{id}/rag/history",
    "DELETE /api/v1/documents/{id}/rag/history",
]


async def rag_query(
    payload: dict[str, object], tenant_id: str | None = None
) -> dict[str, object]:
    from ..core import document_repository
    from ..services.embedding.hf_client import request_embeddings
    from ..services.rag.client import search_similar_chunks

    document_id = str(payload.get("document_id", ""))
    query = str(payload.get("query", ""))
    top_k_raw = payload.get("top_k", 5)
    if isinstance(top_k_raw, int):
        top_k = top_k_raw
    elif isinstance(top_k_raw, str) and top_k_raw.isdigit():
        top_k = int(top_k_raw)
    else:
        top_k = 5
    top_k = max(1, min(top_k, 20))

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    if not tenant_id:
        tenant_id = str(payload.get("tenant_id", ""))
    if not tenant_id:
        tenant_id = "00000000-0000-0000-0000-000000000001"

    document = document_repository.get_document(document_id, tenant_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    query_embeddings = request_embeddings([query])
    query_embedding = query_embeddings[0]

    chunks = search_similar_chunks(
        document_id=document_id,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    answer = "No relevant information found in the document for this query."
    sources = []
    if chunks:
        context_parts: list[str] = []
        for i, chunk in enumerate(chunks):
            content = str(chunk.get("content_translated") or chunk.get("content", ""))
            position = chunk.get("position", i)
            context_parts.append(f"[Excerpt {i + 1} - Position {position}]:\n{content}")
        context = "\n\n---\n\n".join(context_parts)

        try:
            from ..services.llm.client import generate_response

            answer = generate_response(
                query=query,
                context=context,
                temperature=0.3,
                max_tokens=800,
            )
            sources = [
                {
                    "page": chunk.get("page_number", 0) or 0,
                    "section": f"Position {chunk.get('position', i)}",
                    "excerpt": (
                        chunk.get("content_translated") or chunk.get("content", "")
                    )[:200],
                    "relevance": float(chunk.get("similarity", 0.0)),
                }
                for chunk in chunks
            ]
        except Exception as e:
            answer = f"Found {len(chunks)} relevant excerpts but could not generate an answer: {e}"

    return {
        "document_id": document_id,
        "query": query,
        "answer": answer,
        "sources": sources,
        "results": chunks,
        "total_results": len(chunks),
    }


def get_rag_history(document_id: str) -> dict[str, list[dict[str, object]]]:
    return {"messages": []}


def clear_rag_history(document_id: str) -> dict[str, str]:
    return {"status": "cleared"}


RAG_ROUTES = [
    ("POST", "/rag/query", rag_query),
    ("GET", "/documents/{document_id}/rag/history", get_rag_history),
    ("DELETE", "/documents/{document_id}/rag/history", clear_rag_history),
]
