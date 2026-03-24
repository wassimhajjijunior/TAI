from .routers.company import COMPANY_ENDPOINTS
from .routers.compliance import COMPLIANCE_ENDPOINTS
from .routers.documents import DOCUMENT_ENDPOINTS
from .routers.export import EXPORT_ENDPOINTS
from .routers.generate import GENERATE_ENDPOINTS
from .routers.rag import RAG_ENDPOINTS
from .core.supabase_client import get_supabase_settings
from .app import app


ALL_ENDPOINTS = {
  "documents": DOCUMENT_ENDPOINTS,
  "compliance": COMPLIANCE_ENDPOINTS,
  "company": COMPANY_ENDPOINTS,
  "rag": RAG_ENDPOINTS,
  "generate": GENERATE_ENDPOINTS,
  "export": EXPORT_ENDPOINTS,
}

SUPABASE_CLIENT_FACTORIES = {
  "settings": get_supabase_settings,
}

APP = app
