from importlib import import_module
from typing import Any

from ..core import document_repository


fastapi_module = import_module("fastapi")
Body = getattr(fastapi_module, "Body")

COMPANY_ENDPOINTS = [
  "GET /api/v1/company/profile",
  "PUT /api/v1/company/profile",
  "GET /api/v1/company/annexes",
  "POST /api/v1/company/annexes",
]


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_company_profile() -> dict[str, object]:
  profile_row = document_repository.get_company_profile(DEFAULT_TENANT_ID)
  if profile_row is None:
    return {"profile": {}}
  return {"profile": profile_row["profile"]}


def update_company_profile(payload: dict[str, Any] = Body(...)) -> dict[str, object]:
  profile_value = payload.get("profile")
  if isinstance(profile_value, dict):
    profile = {str(key): value for key, value in profile_value.items()}
  else:
    profile = {str(key): value for key, value in payload.items()}

  stored = document_repository.upsert_company_profile(DEFAULT_TENANT_ID, profile)
  return {
    "status": "updated",
    "profile": stored["profile"],
  }


def list_company_annexes() -> dict[str, list[dict[str, str]]]:
  return {"items": []}


def create_company_annex() -> dict[str, str]:
  return {"status": "created"}


COMPANY_ROUTES = [
  ("GET", "/company/profile", get_company_profile),
  ("PUT", "/company/profile", update_company_profile),
  ("GET", "/company/annexes", list_company_annexes),
  ("POST", "/company/annexes", create_company_annex),
]
