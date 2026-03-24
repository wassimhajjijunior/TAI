# API (FastAPI) Scaffold

This folder is the backend service split by feature ownership.

## Run locally

Use the Python 3.11 environment from repo root:

```bash
.venv311/Scripts/python -m uvicorn apps.api.src.main:app --reload --port 8100
```

Health check:

```bash
GET http://localhost:8100/health
```
