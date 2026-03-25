import os
from importlib import import_module
from pathlib import Path
from typing import Any

from ...core import document_repository
from ...core.env import load_local_env_if_present
from ...core.pipeline_events import EVENT_OCR_COMPLETE, QUEUE_OCR, build_event
from ...core.rabbitmq import consume, publish_event


def _mistral_client() -> Any:
  load_local_env_if_present()
  api_key = os.getenv("MISTRAL_API_KEY")
  if not api_key:
    raise RuntimeError("Missing required environment variable: MISTRAL_API_KEY")

  mistral_module = import_module("mistralai")
  mistral_class = getattr(mistral_module, "Mistral", None)
  if mistral_class is None:
    mistral_client_module = import_module("mistralai.client")
    mistral_class = getattr(mistral_client_module, "Mistral", None)
  if mistral_class is None:
    raise RuntimeError("Unsupported mistralai package: Mistral client class not found")
  return mistral_class(api_key=api_key)


def _extract_markdown_text(ocr_response: Any) -> str:
  pages = getattr(ocr_response, "pages", [])
  markdown_parts: list[str] = []
  for page in pages:
    markdown = page.get("markdown") if isinstance(page, dict) else getattr(page, "markdown", "")
    if markdown:
      markdown_parts.append(str(markdown))
  return "\n\n".join(markdown_parts)


def process_document_uploaded(event_payload: dict[str, Any]) -> None:
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", "00000000-0000-0000-0000-000000000001"))
  storage_path = str(payload.get("storage_path", ""))
  filename = str(payload.get("filename", "uploaded-file"))

  if not document_id:
    raise RuntimeError("document_uploaded event missing document_id")

  if not storage_path:
    _ = document_repository.update_document_status(document_id, tenant_id, "ocr_failed")
    raise RuntimeError("document_uploaded event missing storage_path")

  file_path = Path(storage_path)
  if not file_path.exists():
    _ = document_repository.update_document_status(document_id, tenant_id, "ocr_failed")
    raise RuntimeError(f"OCR storage path not found: {storage_path}")

  client = _mistral_client()
  uploaded_file = client.files.upload(
    file={
      "file_name": filename,
      "content": file_path.read_bytes(),
    },
    purpose="ocr",
  )

  signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
  ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
      "type": "document_url",
      "document_url": signed_url.url,
    },
    table_format="markdown",
    extract_header=True,
    extract_footer=True,
  )

  ocr_text = _extract_markdown_text(ocr_response)
  completion_event = build_event(
    EVENT_OCR_COMPLETE,
    {
      "document_id": document_id,
      "tenant_id": tenant_id,
      "filename": filename,
      "ocr_text": ocr_text,
      "status": "ocr_complete",
    },
  )
  _ = document_repository.update_document_status(document_id, tenant_id, "ocr_complete")
  publish_event(EVENT_OCR_COMPLETE, completion_event)


def run_ocr_worker() -> None:
  consume(QUEUE_OCR, process_document_uploaded)
