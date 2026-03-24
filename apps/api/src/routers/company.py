COMPANY_ENDPOINTS = [
  "GET /api/v1/company/profile",
  "PUT /api/v1/company/profile",
  "GET /api/v1/company/annexes",
  "POST /api/v1/company/annexes",
]


def get_company_profile() -> dict[str, object]:
  return {"profile": {}}


def update_company_profile() -> dict[str, str]:
  return {"status": "updated"}


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
