import os
from importlib import import_module
from typing import Any

from ...core.env import load_local_env_if_present


def create_mistral_client() -> Any:
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
