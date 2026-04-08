"""RAG client for vector similarity search using Supabase pgvector."""

import logging
from typing import Any

from ...core import document_repository
from ...core.supabase_client import get_supabase_settings


logger = logging.getLogger(__name__)


def _load_supabase_module():
    from importlib import import_module
    return import_module("supabase")


def _get_client():
    settings = get_supabase_settings()
    module = _load_supabase_module()
    create_client = getattr(module, "create_client")
    return create_client(settings.url, settings.service_role_key)


def _embedding_to_literal(embedding: list[float]) -> str:
    """Convert embedding vector to PostgreSQL literal format."""
    return "[" + ",".join(f"{value:.10f}" for value in embedding) + "]"


def search_similar_chunks(
    document_id: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, object]]:
    """Search for similar chunks using pgvector cosine similarity.
    
    Args:
        document_id: The document ID to search within
        query_embedding: The query embedding vector
        top_k: Number of results to return
        
    Returns:
        List of chunks with content and similarity scores
    """
    client = _get_client()
    
    # Use Supabase RPC for vector similarity search
    # The chunks table has an embedding column with vector(1536)
    embedding_literal = _embedding_to_literal(query_embedding)
    
    try:
        # Use raw SQL for pgvector similarity search
        result = client.rpc(
            "match_chunks",
            {
                "query_document_id": document_id,
                "query_embedding": embedding_literal,
                "match_count": top_k,
            }
        ).execute()
        
        data = getattr(result, "data", [])
        results: list[dict[str, object]] = []
        for item in data:
            results.append({
                "id": str(item.get("id", "")),
                "document_id": str(item.get("document_id", "")),
                "content": str(item.get("content", "")),
                "content_translated": str(item.get("content_translated", "")) if item.get("content_translated") else None,
                "position": int(item.get("position", 0)),
                "page_number": int(item.get("page_number", 0)) if item.get("page_number") else None,
                "similarity": float(item.get("similarity", 0.0)),
            })
        return results
    except Exception as error:
        logger.warning("RPC match_chunks failed: %s", error)
        
        # Fallback: manual similarity calculation using the embedding worker's pattern
        chunks = document_repository.list_document_chunks(document_id)
        if not chunks:
            return []
        
        # Get embeddings for all chunks
        chunk_ids = [chunk["id"] for chunk in chunks]
        chunk_embeddings = _get_chunk_embeddings(chunk_ids)
        
        # Calculate cosine similarity manually
        scored_chunks: list[tuple[dict[str, object], float]] = []
        for chunk in chunks:
            chunk_id = chunk["id"]
            embedding = chunk_embeddings.get(chunk_id)
            if embedding:
                similarity = _cosine_similarity(query_embedding, embedding)
                scored_chunks.append((dict(chunk), similarity))
        
        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k
        results: list[dict[str, object]] = []
        for chunk, similarity in scored_chunks[:top_k]:
            chunk["similarity"] = similarity
            results.append(chunk)
        
        return results


def _get_chunk_embeddings(chunk_ids: list[str]) -> dict[str, list[float]]:
    """Retrieve embeddings for given chunk IDs."""
    client = _get_client()
    result = (
        client.table("chunks")
        .select("id,embedding")
        .in_("id", chunk_ids)
        .execute()
    )
    data = getattr(result, "data", [])
    embeddings: dict[str, list[float]] = {}
    for item in data:
        chunk_id = str(item.get("id", ""))
        embedding_raw = item.get("embedding")
        if embedding_raw and isinstance(embedding_raw, (list, str)):
            if isinstance(embedding_raw, str):
                # Parse vector literal like "[0.1,0.2,...]"
                try:
                    import json
                    embedding = json.loads(embedding_raw)
                except Exception:
                    continue
            else:
                embedding = embedding_raw
            if isinstance(embedding, list) and len(embedding) > 0:
                embeddings[chunk_id] = [float(x) for x in embedding]
    return embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    
    if len(a) != len(b):
        return 0.0
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def retrieve_context_for_query(
    document_id: str,
    query: str,
    hf_client: Any | None = None,
    top_k: int = 5,
) -> list[dict[str, object]]:
    """Retrieve relevant context chunks for a query.
    
    Args:
        document_id: The document ID to search
        query: The user query
        hf_client: Optional HuggingFace client for generating query embedding
        top_k: Number of chunks to retrieve
        
    Returns:
        List of relevant chunks with similarity scores
    """
    if hf_client is None:
        # Lazy import to match Track A pattern
        from importlib import import_module
        embedding_module = import_module("apps.api.src.services.embedding.hf_client")
        request_embeddings = getattr(embedding_module, "request_embeddings")
        embeddings = request_embeddings([query])
        query_embedding = embeddings[0]
    else:
        query_embedding = hf_client.embed_query(query)
    
    return search_similar_chunks(document_id, query_embedding, top_k)


def format_chunks_as_context(chunks: list[dict[str, object]]) -> str:
    """Format chunks as context string for LLM prompt."""
    context_parts: list[str] = []
    for i, chunk in enumerate(chunks):
        content = str(chunk.get("content_translated") or chunk.get("content", ""))
        position = chunk.get("position", i)
        context_parts.append(f"[Excerpt {i + 1} - Position {position}]:\n{content}")
    
    return "\n\n---\n\n".join(context_parts)
