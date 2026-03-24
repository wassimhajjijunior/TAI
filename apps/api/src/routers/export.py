EXPORT_ENDPOINTS = [
  "POST /api/v1/documents/{id}/export",
  "GET /api/v1/exports/{id}/download",
]


def export_document(document_id: str) -> dict[str, str]:
  return {"document_id": document_id, "status": "queued"}


def download_export(export_id: str) -> dict[str, str]:
  return {"export_id": export_id, "status": "ready"}


EXPORT_ROUTES = [
  ("POST", "/documents/{document_id}/export", export_document),
  ("GET", "/exports/{export_id}/download", download_export),
]
