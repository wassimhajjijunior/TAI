EXPORT_ENDPOINTS = [
    "POST /api/v1/documents/{id}/export",
    "GET /api/v1/exports/{id}/download",
]


async def export_document(
    document_id: str,
    payload: dict[str, object],
    tenant_id: str | None = None,
) -> dict[str, object]:
    """Export a document response to DOCX.

    Args:
        document_id: Document ID
        payload: Request with response_id and format
        tenant_id: Tenant ID for validation

    Returns:
        Export metadata with download URL
    """
    from importlib import import_module

    from ..core import document_repository
    from ..services.export.worker import export_to_docx

    response_id = str(payload.get("response_id", ""))
    format_type = str(payload.get("format", "docx"))

    if not response_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="response_id is required")

    if format_type != "docx":
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'docx'")

    response = document_repository.get_response(response_id)
    if response is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Response not found")

    if response["document_id"] != document_id:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(
            status_code=400, detail="Response does not belong to this document"
        )

    file_path, export_id = export_to_docx(response_id, tenant_id=tenant_id)
    export = document_repository.get_export(export_id)
    if export is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=500, detail="Failed to create export record")

    return {
        "export_id": export["id"],
        "document_id": document_id,
        "response_id": response_id,
        "format": format_type,
        "file_path": str(file_path),
        "status": "completed",
        "download_url": f"/api/v1/exports/{export['id']}/download",
    }


def download_export(export_id: str) -> object:
    """Download an exported file.

    Returns:
        FileResponse for download
    """
    from pathlib import Path

    from importlib import import_module

    responses_module = import_module("fastapi.responses")
    FileResponse = getattr(responses_module, "FileResponse")

    from ..core import document_repository

    export = document_repository.get_export(export_id)
    if export is None:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Export not found")

    file_path = export.get("file_path", "")
    if not file_path:
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Export file not ready")

    path = Path(file_path)
    if not path.exists():
        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=404, detail="Export file not found")

    format_type = export.get("format", "docx")
    content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    filename = f"response_{export['document_id'][:8]}.{format_type}"

    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
    )


def list_document_exports(
    document_id: str, tenant_id: str | None = None
) -> dict[str, object]:
    """List all exports for a document."""
    if not tenant_id:
        from importlib import import_module

        fastapi = import_module("fastapi")
        HTTPException = getattr(fastapi, "HTTPException")
        raise HTTPException(status_code=400, detail="tenant_id is required")

    from ..core import document_repository

    exports = document_repository.list_exports(document_id, tenant_id)

    return {
        "document_id": document_id,
        "exports": exports,
        "total": len(exports),
    }


EXPORT_ROUTES = [
    ("POST", "/documents/{document_id}/export", export_document),
    ("GET", "/exports/{export_id}/download", download_export),
    ("GET", "/documents/{document_id}/exports", list_document_exports),
]
