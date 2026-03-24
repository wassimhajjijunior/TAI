COMPLIANCE_ENDPOINTS = [
  "GET /api/v1/documents/{id}/compliance",
]


def get_document_compliance(document_id: str) -> dict[str, object]:
  return {"id": document_id, "score": None, "requirements": []}


COMPLIANCE_ROUTES = [
  ("GET", "/documents/{document_id}/compliance", get_document_compliance),
]
