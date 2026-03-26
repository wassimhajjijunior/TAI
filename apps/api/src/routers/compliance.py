from importlib import import_module

from ..core import document_repository


fastapi_module = import_module("fastapi")
HTTPException = getattr(fastapi_module, "HTTPException")

COMPLIANCE_ENDPOINTS = [
  "GET /api/v1/documents/{id}/compliance",
]


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_document_compliance(document_id: str) -> dict[str, object]:
  document = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
  if document is None:
    raise HTTPException(status_code=404, detail="Document not found")

  report = document_repository.get_compliance_report(document_id)
  requirements = document_repository.list_requirements(document_id)

  if report is None:
    return {
      "id": document_id,
      "eligibility_score": None,
      "recommendation": None,
      "requirements": requirements,
      "report": None,
    }

  return {
    "id": document_id,
    "eligibility_score": report["eligibility_score"],
    "recommendation": report["recommendation"],
    "requirements": requirements,
    "report": report["report"],
  }


COMPLIANCE_ROUTES = [
  ("GET", "/documents/{document_id}/compliance", get_document_compliance),
]
