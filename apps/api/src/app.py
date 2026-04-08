import logging
import os
from collections.abc import Callable, Sequence
from importlib import import_module

from .routers.company import COMPANY_ROUTES
from .routers.compliance import COMPLIANCE_ROUTES
from .routers.documents import DOCUMENT_ROUTES
from .routers.export import EXPORT_ROUTES
from .routers.generate import GENERATE_ROUTES
from .routers.live import register_websocket_routes
from .routers.rag import RAG_ROUTES
from .routers.system import SYSTEM_ROUTES
from .core.rabbitmq import ensure_topology


fastapi_module = import_module("fastapi")
middleware_module = import_module("fastapi.middleware.cors")
FastAPI = getattr(fastapi_module, "FastAPI")
CORSMiddleware = getattr(middleware_module, "CORSMiddleware")

app = FastAPI(title="P2M-TAI API", version="0.1.0")
logger = logging.getLogger(__name__)


def _get_allowed_origins() -> list[str]:
  raw = os.getenv("API_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
  return [origin.strip() for origin in raw.split(",") if origin.strip()]

app.add_middleware(
  CORSMiddleware,
  allow_origins=_get_allowed_origins(),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

try:
  ensure_topology()
except Exception as error:
  logger.warning("RabbitMQ topology bootstrap skipped: %s", error)


@app.get("/health")
def health() -> dict[str, str]:
  return {"status": "ok"}


RouteHandler = Callable[..., object]
RouteDef = tuple[str, str, RouteHandler]


def _register_routes(route_definitions: Sequence[RouteDef]) -> None:
  for method, path, handler in route_definitions:
    app.add_api_route(
      f"/api/v1{path}",
      handler,
      methods=[method],
    )


for route_group in [
    DOCUMENT_ROUTES,
    COMPLIANCE_ROUTES,
    COMPANY_ROUTES,
    RAG_ROUTES,
    GENERATE_ROUTES,
    EXPORT_ROUTES,
    SYSTEM_ROUTES,
]:
    _register_routes(route_group)


# Track B worker entry points for CLI
@app.get("/workers/rag")
def get_rag_worker():
    from .services.rag.worker import run_rag_worker
    return {"status": "manual_trigger_required", "note": "Use 'python -m apps.api.src.services.rag.worker' to run"}


@app.get("/workers/llm")
def get_llm_worker():
    from .services.llm.worker import run_llm_worker
    return {"status": "manual_trigger_required", "note": "Use 'python -m apps.api.src.services.llm.worker' to run"}


@app.get("/workers/export")
def get_export_worker():
    from .services.export.worker import run_export_worker
    return {"status": "manual_trigger_required", "note": "Use 'python -m apps.api.src.services.export.worker' to run"}


register_websocket_routes(app)
