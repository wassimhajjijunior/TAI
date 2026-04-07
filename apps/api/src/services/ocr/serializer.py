from typing import Any


def extract_markdown_text(ocr_response: Any) -> str:
  pages = getattr(ocr_response, "pages", [])
  markdown_parts: list[str] = []
  for page in pages:
    markdown = page.get("markdown") if isinstance(page, dict) else getattr(page, "markdown", "")
    if markdown:
      markdown_parts.append(str(markdown))
  return "\n\n".join(markdown_parts)


def to_plain_object(value: Any) -> Any:
  if isinstance(value, (str, int, float, bool)) or value is None:
    return value
  if isinstance(value, dict):
    return {str(key): to_plain_object(item) for key, item in value.items()}
  if isinstance(value, list):
    return [to_plain_object(item) for item in value]
  if isinstance(value, tuple):
    return [to_plain_object(item) for item in value]
  model_dump = getattr(value, "model_dump", None)
  if callable(model_dump):
    try:
      return to_plain_object(model_dump())
    except Exception:
      pass
  dict_method = getattr(value, "dict", None)
  if callable(dict_method):
    try:
      return to_plain_object(dict_method())
    except Exception:
      pass
  vars_method = getattr(value, "__dict__", None)
  if isinstance(vars_method, dict):
    return to_plain_object(vars_method)
  return str(value)


def build_ocr_artifact(document_id: str, tenant_id: str, filename: str, ocr_response: Any, ocr_text: str) -> dict[str, Any]:
  raw_response = to_plain_object(ocr_response)
  pages_raw = raw_response.get("pages", []) if isinstance(raw_response, dict) else []
  page_summaries: list[dict[str, Any]] = []

  for index, page in enumerate(pages_raw if isinstance(pages_raw, list) else []):
    page_obj = page if isinstance(page, dict) else {}
    markdown = page_obj.get("markdown")
    images = page_obj.get("images")
    dimensions = page_obj.get("dimensions")
    page_summaries.append(
      {
        "page_index": index,
        "markdown": str(markdown) if isinstance(markdown, str) else "",
        "images": images if isinstance(images, list) else [],
        "dimensions": dimensions if isinstance(dimensions, dict) else None,
        "raw": page_obj,
      }
    )

  return {
    "document_id": document_id,
    "tenant_id": tenant_id,
    "filename": filename,
    "model": "mistral-ocr-latest",
    "table_format": "markdown",
    "text": ocr_text,
    "pages": page_summaries,
    "raw_response": raw_response,
  }
