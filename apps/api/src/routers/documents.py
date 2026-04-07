from importlib import import_module
from pathlib import Path
from typing import Any, cast

from ..core import document_repository
from ..core.file_storage import delete_ocr_artifact, load_ocr_artifact
from ..services.ingestion.constants import DEFAULT_TENANT_ID
from ..services.ingestion.worker import ingest_uploaded_document


fastapi_module = import_module("fastapi")
starlette_concurrency_module = import_module("starlette.concurrency")
UploadFile = getattr(fastapi_module, "UploadFile")
File = getattr(fastapi_module, "File")
HTTPException = getattr(fastapi_module, "HTTPException")
run_in_threadpool = getattr(starlette_concurrency_module, "run_in_threadpool")

DOCUMENT_ENDPOINTS = [
  "POST /api/v1/documents",
  "GET /api/v1/documents",
  "GET /api/v1/documents/{id}",
  "DELETE /api/v1/documents/{id}",
  "GET /api/v1/documents/{id}/status",
  "GET /api/v1/documents/{id}/requirements",
  "GET /api/v1/documents/{id}/ocr-artifact",
]

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
}
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
def _get_file_metadata(file_obj: Any, fallback_content: bytes) -> tuple[str, int, str]:
  filename = getattr(file_obj, "filename", None) or "uploaded-file"
  content_type = getattr(file_obj, "content_type", None) or "application/octet-stream"
  size = len(fallback_content)
  return filename, size, content_type


def _validate_file(filename: str, size_bytes: int, content_type: str) -> None:
  if size_bytes <= 0:
    raise HTTPException(status_code=400, detail="Empty file is not allowed")
  if size_bytes > MAX_FILE_SIZE_BYTES:
    raise HTTPException(status_code=413, detail="File too large")
  extension = Path(filename).suffix.lower()
  is_known_extension = extension in ALLOWED_EXTENSIONS
  is_known_mime = content_type in ALLOWED_CONTENT_TYPES
  if not is_known_mime and not is_known_extension:
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
  if not filename.strip():
    raise HTTPException(status_code=400, detail="Invalid filename")


async def upload_document(file: Any = File(...)) -> dict[str, object]:
  read_fn = getattr(file, "read", None)
  if read_fn is None or not callable(read_fn):
    raise HTTPException(status_code=400, detail="File payload is missing")

  content = await cast(Any, read_fn)()
  filename, size_bytes, content_type = _get_file_metadata(file, content)
  _validate_file(filename, size_bytes, content_type)
  return await run_in_threadpool(ingest_uploaded_document, filename, size_bytes, content_type, content)


def list_documents() -> dict[str, list[dict[str, Any]]]:
  return {
    "items": [
      document_repository.to_dict(item)
      for item in document_repository.list_documents(DEFAULT_TENANT_ID)
    ],
  }


def get_document(document_id: str) -> dict[str, Any]:
  stored = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
  if stored is None:
    raise HTTPException(status_code=404, detail="Document not found")
  return {
    "document": document_repository.to_dict(stored),
  }


def get_document_status(document_id: str) -> dict[str, str]:
  stored = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
  if stored is None:
    raise HTTPException(status_code=404, detail="Document not found")
  return {
    "id": stored.id,
    "status": stored.status,
  }


def delete_document(document_id: str) -> dict[str, str]:
  deleted = document_repository.delete_document(document_id, DEFAULT_TENANT_ID)
  if not deleted:
    raise HTTPException(status_code=404, detail="Document not found")
  _ = delete_ocr_artifact(document_id)
  return {
    "id": document_id,
    "status": "deleted",
  }


def get_document_requirements(document_id: str) -> dict[str, object]:
  stored = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
  if stored is None:
    raise HTTPException(status_code=404, detail="Document not found")
  requirements = document_repository.list_requirements(document_id)
  return {
    "id": document_id,
    "requirements": requirements,
  }


def get_document_ocr_artifact(document_id: str) -> dict[str, object]:
  stored = document_repository.get_document(document_id, DEFAULT_TENANT_ID)
  if stored is None:
    raise HTTPException(status_code=404, detail="Document not found")

  artifact = load_ocr_artifact(document_id)
  if artifact is None:
    raise HTTPException(status_code=404, detail="OCR artifact not found for this document")

  return {
    "id": document_id,
    "artifact": artifact,
  }


DOCUMENT_ROUTES = [
  ("POST", "/documents", upload_document),
  ("GET", "/documents", list_documents),
  ("GET", "/documents/{document_id}", get_document),
  ("DELETE", "/documents/{document_id}", delete_document),
  ("GET", "/documents/{document_id}/status", get_document_status),
  ("GET", "/documents/{document_id}/requirements", get_document_requirements),
  ("GET", "/documents/{document_id}/ocr-artifact", get_document_ocr_artifact),
]
