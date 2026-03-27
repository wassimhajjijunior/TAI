import asyncio
import json
import logging
from typing import Any

from ..core import document_repository


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
logger = logging.getLogger(__name__)


def serialize_documents() -> list[dict[str, object]]:
  return [
    document_repository.to_dict(item)
    for item in document_repository.list_documents(DEFAULT_TENANT_ID)
  ]


async def websocket_documents(websocket: Any) -> None:
  await websocket.accept()
  previous_payload = ""

  try:
    initial_message = {
      "type": "documents.updated",
      "items": serialize_documents(),
    }
    await websocket.send_json(initial_message)
    previous_payload = json.dumps(initial_message, sort_keys=True, ensure_ascii=False)

    while True:
      await asyncio.sleep(1.5)
      message = {
        "type": "documents.updated",
        "items": serialize_documents(),
      }
      serialized = json.dumps(message, sort_keys=True, ensure_ascii=False)
      if serialized != previous_payload:
        await websocket.send_json(message)
        previous_payload = serialized
  except Exception as error:
    error_name = type(error).__name__
    if error_name in {"WebSocketDisconnect", "ClientDisconnected"}:
      return

    error_text = str(error)
    if "ConnectionClosed" in error_name or "close message has been sent" in error_text:
      return

    logger.debug("Live websocket ended with non-fatal error: %s", error)
    return


def register_websocket_routes(app: Any) -> None:
  app.router.add_websocket_route("/api/v1/live/documents", websocket_documents)
