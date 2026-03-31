import json
import logging
import os
import random
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from .pipeline_events import (
  EVENT_COMPLIANCE_COMPLETED,
  EVENT_EMBEDDING_COMPLETE,
  EVENT_EXCHANGE,
  EVENT_EXCHANGE_TYPE,
  EVENT_NLP_COMPLETED,
  EVENT_OCR_COMPLETE,
  EVENT_DOCUMENT_UPLOADED,
  QUEUE_COMPLIANCE,
  QUEUE_EMBEDDING,
  QUEUE_NLP,
  QUEUE_NOTIFICATION,
  QUEUE_OCR,
)


@dataclass(frozen=True)
class RabbitMqSettings:
  url: str


logger = logging.getLogger(__name__)


def get_rabbitmq_settings() -> RabbitMqSettings:
  return RabbitMqSettings(
    url=os.getenv("RABBITMQ_URL", "amqp://admin:admin@localhost:5672/%2F"),
  )


def _pika_module() -> Any:
  return import_module("pika")


def _connect_blocking(timeout_seconds: float | None = None) -> Any:
  pika_module = _pika_module()
  settings = get_rabbitmq_settings()
  parameters = getattr(pika_module, "URLParameters")(settings.url)
  if timeout_seconds is not None:
    parameters.socket_timeout = timeout_seconds
    parameters.blocked_connection_timeout = timeout_seconds
    parameters.connection_attempts = 1
    parameters.retry_delay = 0
  connection = getattr(pika_module, "BlockingConnection")(parameters)
  return connection


def can_connect() -> tuple[bool, str]:
  try:
    connection = _connect_blocking(timeout_seconds=3.0)
    connection.close()
    return True, "connected"
  except Exception as error:
    return False, f"{type(error).__name__}: {error}"


def get_topology_metadata() -> dict[str, object]:
  return {
    "exchange": EVENT_EXCHANGE,
    "exchange_type": EVENT_EXCHANGE_TYPE,
    "queues": {
      "ocr": QUEUE_OCR,
      "nlp": QUEUE_NLP,
      "embedding": QUEUE_EMBEDDING,
      "compliance": QUEUE_COMPLIANCE,
      "notification": QUEUE_NOTIFICATION,
    },
    "event_flow": [
      EVENT_DOCUMENT_UPLOADED,
      EVENT_OCR_COMPLETE,
      EVENT_NLP_COMPLETED,
      EVENT_EMBEDDING_COMPLETE,
      EVENT_COMPLIANCE_COMPLETED,
    ],
  }


def declare_topology(channel: Any) -> None:
  channel.exchange_declare(
    exchange=EVENT_EXCHANGE,
    exchange_type=EVENT_EXCHANGE_TYPE,
    durable=True,
  )

  bindings = [
    (QUEUE_OCR, EVENT_DOCUMENT_UPLOADED),
    (QUEUE_NLP, EVENT_OCR_COMPLETE),
    (QUEUE_EMBEDDING, EVENT_NLP_COMPLETED),
    (QUEUE_COMPLIANCE, EVENT_EMBEDDING_COMPLETE),
    (QUEUE_NOTIFICATION, EVENT_COMPLIANCE_COMPLETED),
  ]

  for queue_name, routing_key in bindings:
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=EVENT_EXCHANGE, queue=queue_name, routing_key=routing_key)


def publish_event(event_name: str, payload: dict[str, Any]) -> None:
  connection = _connect_blocking()
  try:
    channel = connection.channel()
    declare_topology(channel)

    body = json.dumps(payload).encode("utf-8")
    pika_module = _pika_module()
    properties = getattr(pika_module, "BasicProperties")(delivery_mode=2)
    channel.basic_publish(
      exchange=EVENT_EXCHANGE,
      routing_key=event_name,
      body=body,
      properties=properties,
    )
  finally:
    connection.close()


def ensure_topology() -> None:
  connection = _connect_blocking()
  try:
    channel = connection.channel()
    declare_topology(channel)
  finally:
    connection.close()


def consume(queue_name: str, callback: Any) -> None:
  reconnect_delay_seconds = 1.0
  max_reconnect_delay_seconds = 30.0

  while True:
    connection: Any | None = None
    try:
      connection = _connect_blocking()
      if connection is None:
        raise RuntimeError("Failed to open RabbitMQ connection")

      reconnect_delay_seconds = 1.0
      channel = connection.channel()
      declare_topology(channel)
      channel.basic_qos(prefetch_count=1)

      def _wrapped(ch: Any, method: Any, properties: Any, body: bytes) -> None:
        try:
          payload = json.loads(body.decode("utf-8"))
          callback(payload)
          ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
          logger.exception("Message processing failed on queue '%s'", queue_name)
          requeue = not getattr(method, "redelivered", False)
          ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)

      channel.basic_consume(queue=queue_name, on_message_callback=_wrapped, auto_ack=False)
      channel.start_consuming()
    except (KeyboardInterrupt, SystemExit):
      logger.info("Consumer for queue '%s' stopping due to shutdown signal", queue_name)
      raise
    except Exception:
      logger.exception(
        "Consumer loop error on queue '%s'; reconnecting in %.1f second(s)",
        queue_name,
        reconnect_delay_seconds,
      )
      sleep_seconds = reconnect_delay_seconds + random.uniform(0, 0.5)
      time.sleep(sleep_seconds)
      reconnect_delay_seconds = min(reconnect_delay_seconds * 2, max_reconnect_delay_seconds)
    finally:
      try:
        if connection is not None:
          connection.close()
      except Exception:
        pass
