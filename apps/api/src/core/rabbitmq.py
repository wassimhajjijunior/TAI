import json
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from .pipeline_events import (
    EVENT_COMPLIANCE_COMPLETED,
    EVENT_EMBEDDING_COMPLETE,
    EVENT_EXCHANGE,
    EVENT_EXCHANGE_TYPE,
    EVENT_EXPORT_COMPLETE,
    EVENT_GENERATION_COMPLETE,
    EVENT_LLM_GENERATION,
    EVENT_NLP_COMPLETED,
    EVENT_OCR_COMPLETE,
    EVENT_DOCUMENT_UPLOADED,
    QUEUE_COMPLIANCE,
    QUEUE_EMBEDDING,
    QUEUE_EXPORT,
    QUEUE_LLM_GENERATION,
    QUEUE_NLP,
    QUEUE_NOTIFICATION,
    QUEUE_OCR,
    QUEUE_RAG,
)


@dataclass(frozen=True)
class RabbitMqSettings:
    url: str
    heartbeat_seconds: int
    socket_timeout_seconds: float
    blocked_connection_timeout_seconds: float
    connection_attempts: int
    retry_delay_seconds: float


logger = logging.getLogger(__name__)


class SettlementChannelError(RuntimeError):
    pass


def _is_reconnect_required_error(error: Exception) -> bool:
    reconnect_error_names = {
        "StreamLostError",
        "ChannelWrongStateError",
        "ConnectionWrongStateError",
        "AMQPConnectionError",
        "AMQPChannelError",
        "ConnectionClosed",
        "ChannelClosed",
        "ConnectionClosedByBroker",
    }
    if type(error).__name__ in reconnect_error_names:
        return True

    message = str(error).lower()
    reconnect_markers = [
        "stream connection lost",
        "channel is closed",
        "connection is closed",
        "connection reset",
        "connection aborted",
    ]
    return any(marker in message for marker in reconnect_markers)


def get_rabbitmq_settings() -> RabbitMqSettings:
    heartbeat_raw = os.getenv("RABBITMQ_HEARTBEAT_SECONDS", "900").strip()
    socket_timeout_raw = os.getenv("RABBITMQ_SOCKET_TIMEOUT_SECONDS", "900").strip()
    blocked_timeout_raw = os.getenv("RABBITMQ_BLOCKED_TIMEOUT_SECONDS", "900").strip()
    attempts_raw = os.getenv("RABBITMQ_CONNECTION_ATTEMPTS", "3").strip()
    retry_delay_raw = os.getenv("RABBITMQ_RETRY_DELAY_SECONDS", "2").strip()

    try:
        heartbeat_seconds = max(0, int(heartbeat_raw))
    except Exception:
        heartbeat_seconds = 900

    try:
        socket_timeout_seconds = max(5.0, float(socket_timeout_raw))
    except Exception:
        socket_timeout_seconds = 900.0

    try:
        blocked_connection_timeout_seconds = max(5.0, float(blocked_timeout_raw))
    except Exception:
        blocked_connection_timeout_seconds = 900.0

    try:
        connection_attempts = max(1, int(attempts_raw))
    except Exception:
        connection_attempts = 3

    try:
        retry_delay_seconds = max(0.0, float(retry_delay_raw))
    except Exception:
        retry_delay_seconds = 2.0

    return RabbitMqSettings(
        url=os.getenv("RABBITMQ_URL", "amqp://admin:***@localhost:5672/%2F"),
        heartbeat_seconds=heartbeat_seconds,
        socket_timeout_seconds=socket_timeout_seconds,
        blocked_connection_timeout_seconds=blocked_connection_timeout_seconds,
        connection_attempts=connection_attempts,
        retry_delay_seconds=retry_delay_seconds,
    )


def _pika_module() -> Any:
    return import_module("pika")


def _connect_blocking(timeout_seconds: float | None = None) -> Any:
    pika_module = _pika_module()
    settings = get_rabbitmq_settings()
    parameters = getattr(pika_module, "URLParameters")(settings.url)

    parameters.heartbeat = settings.heartbeat_seconds
    parameters.socket_timeout = settings.socket_timeout_seconds
    parameters.blocked_connection_timeout = settings.blocked_connection_timeout_seconds
    parameters.connection_attempts = settings.connection_attempts
    parameters.retry_delay = settings.retry_delay_seconds

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
            "rag": QUEUE_RAG,
            "llm_generation": QUEUE_LLM_GENERATION,
            "export": QUEUE_EXPORT,
        },
        "event_flow": [
            EVENT_DOCUMENT_UPLOADED,
            EVENT_OCR_COMPLETE,
            EVENT_NLP_COMPLETED,
            EVENT_EMBEDDING_COMPLETE,
            EVENT_COMPLIANCE_COMPLETED,
            EVENT_LLM_GENERATION,
            EVENT_GENERATION_COMPLETE,
            EVENT_EXPORT_COMPLETE,
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
        (QUEUE_RAG, EVENT_COMPLIANCE_COMPLETED),
        (QUEUE_LLM_GENERATION, EVENT_LLM_GENERATION),
        (QUEUE_EXPORT, EVENT_GENERATION_COMPLETE),
    ]

    for queue_name, routing_key in bindings:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(
            exchange=EVENT_EXCHANGE, queue=queue_name, routing_key=routing_key
        )


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
        try:
            connection.close()
        except Exception:
            pass


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
    max_workers_raw = os.getenv("RABBITMQ_CONSUMER_WORKERS", "2").strip()
    try:
        max_workers = max(1, int(max_workers_raw))
    except Exception:
        max_workers = 2

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            connection: Any | None = None
            in_flight_delivery_tags: set[str] = set()
            try:
                connection = _connect_blocking()
                if connection is None:
                    raise RuntimeError("Failed to open RabbitMQ connection")
                active_connection = connection

                reconnect_delay_seconds = 1.0
                channel = connection.channel()
                declare_topology(channel)
                channel.basic_qos(prefetch_count=1)

                def _safe_ack(ch: Any, delivery_tag: Any) -> None:
                    try:
                        ch.basic_ack(delivery_tag=delivery_tag)
                    except Exception as error:
                        logger.warning(
                            "ACK failed on queue '%s' (delivery_tag=%s); connection/channel likely closed",
                            queue_name,
                            delivery_tag,
                            exc_info=True,
                        )
                        if _is_reconnect_required_error(error):
                            raise SettlementChannelError(
                                "ACK failed due to closed/lost connection"
                            ) from error
                        raise

                def _safe_nack(ch: Any, delivery_tag: Any, requeue: bool) -> None:
                    try:
                        ch.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
                    except Exception as error:
                        logger.warning(
                            "NACK failed on queue '%s' (delivery_tag=%s, requeue=%s); connection/channel likely closed",
                            queue_name,
                            delivery_tag,
                            requeue,
                            exc_info=True,
                        )
                        if _is_reconnect_required_error(error):
                            raise SettlementChannelError(
                                "NACK failed due to closed/lost connection"
                            ) from error
                        raise

                def _schedule_settlement(
                    delivery_tag: Any, success: bool, redelivered: bool
                ) -> None:
                    delivery_tag_key = str(delivery_tag)

                    def _settle() -> None:
                        try:
                            if connection is None:
                                return
                            if success:
                                _safe_ack(channel, delivery_tag)
                            else:
                                requeue = not redelivered
                                _safe_nack(channel, delivery_tag, requeue)
                        finally:
                            in_flight_delivery_tags.discard(delivery_tag_key)

                    try:
                        active_connection.add_callback_threadsafe(_settle)
                    except Exception:
                        in_flight_delivery_tags.discard(delivery_tag_key)
                        raise

                def _process_message(
                    delivery_tag: Any, redelivered: bool, body: bytes
                ) -> None:
                    try:
                        payload = json.loads(body.decode("utf-8"))
                        callback(payload)
                    except Exception:
                        logger.exception(
                            "Message processing failed on queue '%s'", queue_name
                        )
                        _schedule_settlement(
                            delivery_tag, success=False, redelivered=redelivered
                        )
                    else:
                        _schedule_settlement(
                            delivery_tag, success=True, redelivered=redelivered
                        )

                def _wrapped(
                    ch: Any, method: Any, properties: Any, body: bytes
                ) -> None:
                    _ = (ch, properties)
                    delivery_tag = getattr(method, "delivery_tag", None)
                    if delivery_tag is None:
                        return

                    delivery_tag_key = str(delivery_tag)
                    if delivery_tag_key in in_flight_delivery_tags:
                        return
                    in_flight_delivery_tags.add(delivery_tag_key)

                    redelivered = bool(getattr(method, "redelivered", False))
                    executor.submit(_process_message, delivery_tag, redelivered, body)

                channel.basic_consume(
                    queue=queue_name, on_message_callback=_wrapped, auto_ack=False
                )
                channel.start_consuming()
            except (KeyboardInterrupt, SystemExit):
                logger.info(
                    "Consumer for queue '%s' stopping due to shutdown signal",
                    queue_name,
                )
                raise
            except Exception:
                logger.exception(
                    "Consumer loop error on queue '%s'; reconnecting in %.1f second(s)",
                    queue_name,
                    reconnect_delay_seconds,
                )
                sleep_seconds = reconnect_delay_seconds + random.uniform(0, 0.5)
                time.sleep(sleep_seconds)
                reconnect_delay_seconds = min(
                    reconnect_delay_seconds * 2, max_reconnect_delay_seconds
                )
            finally:
                try:
                    in_flight_delivery_tags.clear()
                    if connection is not None:
                        connection.close()
                except Exception:
                    pass
