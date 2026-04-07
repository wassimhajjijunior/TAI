import os
from importlib import import_module

from .constants import EMBEDDING_DIMENSION, HF_DEFAULT_EMBEDDING_MODEL


def hf_embedding_endpoint() -> str:
  configured = os.getenv("HF_EMBEDDING_API_URL", "").strip()
  if configured:
    return configured

  model_name = os.getenv("HF_EMBEDDING_MODEL", HF_DEFAULT_EMBEDDING_MODEL).strip() or HF_DEFAULT_EMBEDDING_MODEL
  return f"https://router.huggingface.co/hf-inference/models/{model_name}/pipeline/feature-extraction"


def hf_token() -> str:
  token = os.getenv("HF_TOKEN", "").strip()
  if not token:
    raise RuntimeError("Missing required environment variable: HF_TOKEN")
  return token


def coerce_embeddings(payload: object, expected_count: int) -> list[list[float]]:
  if isinstance(payload, dict):
    embeddings_value = payload.get("embeddings") if isinstance(payload.get("embeddings"), list) else None
    if embeddings_value is not None:
      payload = embeddings_value

  if isinstance(payload, list) and payload and all(isinstance(item, (int, float)) for item in payload):
    vectors = [[float(value) for value in payload]]
  elif isinstance(payload, list) and all(isinstance(item, list) for item in payload):
    vectors = [[float(value) for value in row if isinstance(value, (int, float))] for row in payload]
  else:
    raise RuntimeError("Unexpected embedding payload shape from Hugging Face endpoint")

  if len(vectors) != expected_count:
    raise RuntimeError(
      f"Embedding payload count mismatch: expected {expected_count}, got {len(vectors)}"
    )

  for vector in vectors:
    if len(vector) != EMBEDDING_DIMENSION:
      raise RuntimeError(
        f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(vector)}"
      )

  return vectors


def request_embeddings(texts: list[str]) -> list[list[float]]:
  requests_module = import_module("requests")
  post = getattr(requests_module, "post")

  response = post(
    hf_embedding_endpoint(),
    headers={"Authorization": f"Bearer {hf_token()}"},
    json={
      "inputs": texts,
      "options": {"wait_for_model": True},
    },
    timeout=45,
  )
  if not bool(getattr(response, "ok", False)):
    response_text = str(getattr(response, "text", ""))
    raise RuntimeError(f"HF embedding request failed: {getattr(response, 'status_code', 'unknown')} {response_text}")

  payload = response.json()
  if isinstance(payload, dict) and "error" in payload:
    raise RuntimeError(f"HF embedding error: {payload['error']}")

  return coerce_embeddings(payload, len(texts))
