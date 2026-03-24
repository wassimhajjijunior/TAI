from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


EVENT_DOCUMENT_UPLOADED = "document_uploaded"
EVENT_OCR_COMPLETE = "ocr_complete"
EVENT_NLP_COMPLETED = "nlp_completed"
EVENT_EMBEDDING_COMPLETE = "embedding_complete"

EVENT_EXCHANGE = "p2m.events"
EVENT_EXCHANGE_TYPE = "topic"

QUEUE_OCR = "track_a.ocr.queue"
QUEUE_NLP = "track_a.nlp.queue"
QUEUE_EMBEDDING = "track_a.embedding.queue"
QUEUE_COMPLIANCE = "track_a.compliance.queue"


@dataclass(frozen=True)
class EventEnvelope:
  event_id: str
  event_name: str
  occurred_at: str
  payload: dict[str, Any]


def build_event(event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
  envelope = EventEnvelope(
    event_id=str(uuid4()),
    event_name=event_name,
    occurred_at=datetime.now(timezone.utc).isoformat(),
    payload=payload,
  )
  return {
    "event_id": envelope.event_id,
    "event_name": envelope.event_name,
    "occurred_at": envelope.occurred_at,
    "payload": envelope.payload,
  }
