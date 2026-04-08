import json
from pathlib import Path
from typing import Any


def get_storage_root() -> Path:
  return Path(__file__).resolve().parents[2] / "storage" / "documents"


def save_uploaded_file(document_id: str, filename: str, content: bytes) -> str:
  storage_root = get_storage_root()
  storage_root.mkdir(parents=True, exist_ok=True)

  safe_name = Path(filename).name
  destination = storage_root / f"{document_id}__{safe_name}"
  destination.write_bytes(content)
  return str(destination.resolve())


def get_document_artifact_dir(document_id: str) -> Path:
  artifact_root = Path(__file__).resolve().parents[2] / "storage" / "artifacts"
  destination = artifact_root / document_id
  destination.mkdir(parents=True, exist_ok=True)
  return destination


def save_ocr_artifact(document_id: str, payload: dict[str, Any]) -> str:
  artifact_dir = get_document_artifact_dir(document_id)
  destination = artifact_dir / "ocr_result.json"
  destination.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  return str(destination.resolve())


def load_ocr_artifact(document_id: str) -> dict[str, Any] | None:
  artifact_dir = Path(__file__).resolve().parents[2] / "storage" / "artifacts" / document_id
  source = artifact_dir / "ocr_result.json"
  if not source.exists():
    return None
  try:
    parsed = json.loads(source.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return None
  return parsed if isinstance(parsed, dict) else None


def delete_ocr_artifact(document_id: str) -> bool:
    artifact_dir = Path(__file__).resolve().parents[2] / "storage" / "artifacts" / document_id
    source = artifact_dir / "ocr_result.json"
    removed = False
    if source.exists():
        source.unlink()
        removed = True
    if artifact_dir.exists() and not any(artifact_dir.iterdir()):
        artifact_dir.rmdir()
    return removed


def get_response_artifact_dir(response_id: str) -> Path:
    """Get directory for response artifacts."""
    artifact_root = Path(__file__).resolve().parents[2] / "storage" / "responses"
    destination = artifact_root / response_id
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def save_response_artifact(response_id: str, payload: dict[str, Any]) -> str:
    """Save response artifact to JSON file."""
    artifact_dir = get_response_artifact_dir(response_id)
    destination = artifact_dir / "response.json"
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(destination.resolve())


def load_response_artifact(response_id: str) -> dict[str, Any] | None:
    """Load response artifact from JSON file."""
    artifact_dir = Path(__file__).resolve().parents[2] / "storage" / "responses" / response_id
    source = artifact_dir / "response.json"
    if not source.exists():
        return None
    try:
        parsed = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def get_export_storage_path(export_id: str, extension: str = ".docx") -> Path:
    """Get storage path for export file."""
    export_root = Path(__file__).resolve().parents[2] / "storage" / "exports"
    export_root.mkdir(parents=True, exist_ok=True)
    return export_root / f"{export_id}{extension}"


def delete_response_artifact(response_id: str) -> bool:
    """Delete response artifact."""
    artifact_dir = Path(__file__).resolve().parents[2] / "storage" / "responses" / response_id
    source = artifact_dir / "response.json"
    removed = False
    if source.exists():
        source.unlink()
        removed = True
    if artifact_dir.exists() and not any(artifact_dir.iterdir()):
        artifact_dir.rmdir()
    return removed


def delete_export_file(export_id: str, extension: str = ".docx") -> bool:
    """Delete export file."""
    export_root = Path(__file__).resolve().parents[2] / "storage" / "exports"
    source = export_root / f"{export_id}{extension}"
    if source.exists():
        source.unlink()
        return True
    return False
