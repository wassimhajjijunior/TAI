GENERATE_ENDPOINTS = [
  "POST /api/v1/generate/response",
  "GET /api/v1/responses/{id}",
  "PATCH /api/v1/responses/{id}",
]


def generate_response() -> dict[str, str]:
  return {"status": "generated"}


def get_response(response_id: str) -> dict[str, str]:
  return {"id": response_id, "content": ""}


def patch_response(response_id: str) -> dict[str, str]:
  return {"id": response_id, "status": "updated"}


GENERATE_ROUTES = [
  ("POST", "/generate/response", generate_response),
  ("GET", "/responses/{response_id}", get_response),
  ("PATCH", "/responses/{response_id}", patch_response),
]
