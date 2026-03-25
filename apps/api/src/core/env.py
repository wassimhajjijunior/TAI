import os
from pathlib import Path


def load_local_env_if_present() -> None:
  env_path = Path(__file__).resolve().parents[2] / ".env"
  if not env_path.exists():
    return

  for line in env_path.read_text(encoding="utf-8").splitlines():
    normalized = line.strip()
    if not normalized or normalized.startswith("#") or "=" not in normalized:
      continue
    key, value = normalized.split("=", 1)
    _ = os.environ.setdefault(key.strip(), value.strip())


def required_env(name: str) -> str:
  value = os.getenv(name)
  if not value:
    raise RuntimeError(f"Missing required environment variable: {name}")
  return value
