from importlib import import_module
from pathlib import Path
from typing import Any

from ...core import document_repository
from ...core.file_storage import save_ocr_artifact
from ...core.pipeline_events import EVENT_OCR_COMPLETE, QUEUE_OCR, build_event
from ...core.rabbitmq import consume, publish_event

    
def _load_ocr_helpers() -> tuple[Any, Any, Any]:
  client_module = import_module("apps.api.src.services.ocr.client")
  serializer_module = import_module("apps.api.src.services.ocr.serializer")
  create_mistral_client = getattr(client_module, "create_mistral_client")
  build_ocr_artifact = getattr(serializer_module, "build_ocr_artifact")
  extract_markdown_text = getattr(serializer_module, "extract_markdown_text")
  return create_mistral_client, build_ocr_artifact, extract_markdown_text


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

  create_mistral_client, build_ocr_artifact, extract_markdown_text = _load_ocr_helpers()
  client = create_mistral_client()
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

  ocr_text = extract_markdown_text(ocr_response)
  artifact_payload = build_ocr_artifact(document_id, tenant_id, filename, ocr_response, ocr_text)
  ocr_json_path = save_ocr_artifact(document_id, artifact_payload)
  completion_event = build_event(
    EVENT_OCR_COMPLETE,
    {
      "document_id": document_id,
      "tenant_id": tenant_id,
      "filename": filename,
      "ocr_text": ocr_text,
      "ocr_json_path": ocr_json_path,
      "status": "ocr_complete",
    },
  )
  _ = document_repository.update_document_status(document_id, tenant_id, "ocr_complete")
  publish_event(EVENT_OCR_COMPLETE, completion_event)


def run_ocr_worker() -> None:
  consume(QUEUE_OCR, process_document_uploaded)
