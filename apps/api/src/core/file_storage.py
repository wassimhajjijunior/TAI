from pathlib import Path


def get_storage_root() -> Path:
  return Path(__file__).resolve().parents[2] / "storage" / "documents"


def save_uploaded_file(document_id: str, filename: str, content: bytes) -> str:
  storage_root = get_storage_root()
  storage_root.mkdir(parents=True, exist_ok=True)

  safe_name = Path(filename).name
  destination = storage_root / f"{document_id}__{safe_name}"
  destination.write_bytes(content)
  return str(destination.resolve())
