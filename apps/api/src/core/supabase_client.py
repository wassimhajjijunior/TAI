import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SupabaseSettings:
  url: str
  anon_key: str
  service_role_key: str


def _load_local_env_if_present() -> None:
  env_path = Path(__file__).resolve().parents[2] / ".env"
  if not env_path.exists():
    return

  for line in env_path.read_text(encoding="utf-8").splitlines():
    normalized = line.strip()
    if not normalized or normalized.startswith("#") or "=" not in normalized:
      continue
    key, value = normalized.split("=", 1)
    _ = os.environ.setdefault(key.strip(), value.strip())


def _required_env(name: str) -> str:
  value = os.getenv(name)
  if not value:
    raise RuntimeError(f"Missing required environment variable: {name}")
  return value


def get_supabase_settings() -> SupabaseSettings:
  _load_local_env_if_present()
  return SupabaseSettings(
    _required_env("SUPABASE_URL"),
    _required_env("SUPABASE_ANON_KEY"),
    _required_env("SUPABASE_SERVICE_ROLE_KEY"),
  )
