import os
from importlib import import_module
from typing import Any

from ...core.env import load_local_env_if_present
from .constants import EMBEDDING_DIMENSION, LANGCHAIN_DEFAULT_EMBEDDING_MODEL


def _load_langchain_hf_endpoint_embeddings_class():
  module = import_module("langchain_huggingface")
  return getattr(module, "HuggingFaceEndpointEmbeddings")


def _embedding_model_name() -> str:
  return os.getenv("LANGCHAIN_EMBEDDING_MODEL", LANGCHAIN_DEFAULT_EMBEDDING_MODEL).strip() or LANGCHAIN_DEFAULT_EMBEDDING_MODEL


def _huggingface_token() -> str:
  load_local_env_if_present()
  return os.getenv("HF_TOKEN", "").strip()


def _resolve_embeddings_model() -> Any:
  load_local_env_if_present()
  token = _huggingface_token()
  if not token:
    raise RuntimeError("Missing required environment variable: HF_TOKEN")

  model_name = _embedding_model_name()
  EndpointEmbeddingsClass = _load_langchain_hf_endpoint_embeddings_class()
  return EndpointEmbeddingsClass(
    model=model_name,
    repo_id=model_name,
    huggingfacehub_api_token=token,
    task="feature-extraction",
  )


def request_embeddings(texts: list[str]) -> list[list[float]]:
  if not texts:
    return []

  embeddings_model = _resolve_embeddings_model()
  try:
    vectors = embeddings_model.embed_documents(texts)
  except Exception as error:
    raise RuntimeError(f"LangChain embedding request failed: {error}") from error

  normalized_vectors: list[list[float]] = []
  for vector in vectors:
    normalized_vectors.append([float(value) for value in vector])

  if len(normalized_vectors) != len(texts):
    raise RuntimeError(
      f"Embedding payload count mismatch: expected {len(texts)}, got {len(normalized_vectors)}"
    )

  for vector in normalized_vectors:
    if len(vector) != EMBEDDING_DIMENSION:
      raise RuntimeError(
        f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(vector)}"
      )

  return normalized_vectors
