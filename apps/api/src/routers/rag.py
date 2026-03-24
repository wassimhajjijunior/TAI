RAG_ENDPOINTS = [
  "POST /api/v1/rag/query",
]


def rag_query() -> dict[str, list[dict[str, object]]]:
  return {"results": []}


RAG_ROUTES = [
  ("POST", "/rag/query", rag_query),
]
