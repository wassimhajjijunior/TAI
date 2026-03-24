from dataclasses import dataclass

from .env import load_local_env_if_present, required_env


@dataclass(frozen=True)
class SupabaseSettings:
  url: str
  anon_key: str
  service_role_key: str


def get_supabase_settings() -> SupabaseSettings:
  load_local_env_if_present()
  return SupabaseSettings(
    required_env("SUPABASE_URL"),
    required_env("SUPABASE_ANON_KEY"),
    required_env("SUPABASE_SERVICE_ROLE_KEY"),
  )
