import os
import html
from importlib import import_module
from typing import Any

from ...core import document_repository
from ...core.env import load_local_env_if_present
from ...core.pipeline_events import QUEUE_NOTIFICATION
from ...core.rabbitmq import consume


TEMPLATE_NAME = "compliance_report_high_score"
SUBJECT = "High Match"
DEFAULT_CHANNEL = "email"


def _required_env(name: str) -> str:
  load_local_env_if_present()
  value = os.getenv(name, "").strip()
  if not value:
    raise RuntimeError(f"Missing required environment variable: {name}")
  return value


def _build_email_html(payload: dict[str, Any]) -> str:
  score = html.escape(str(payload.get("eligibility_score", "N/A")))
  budget = html.escape(str(payload.get("budget", "N/A")))
  deadline = html.escape(str(payload.get("deadline", "N/A")))
  category = html.escape(str(payload.get("category", "N/A")))
  filename = html.escape(str(payload.get("document_filename", "Tender document")))

  link_raw = str(payload.get("document_link", "")).strip()
  link_value = link_raw if link_raw.startswith("http://") or link_raw.startswith("https://") else ""
  document_link = html.escape(link_value)

  return f"""
  <html>
    <body style=\"font-family: Arial, sans-serif; color: #111827;\"> 
      <h2>Compliance Report: High Match</h2>
      <p><strong>Document:</strong> {filename}</p>
      <p><strong>Eligibility score:</strong> {score}</p>
      <p><strong>Budget:</strong> {budget}</p>
      <p><strong>Deadline:</strong> {deadline}</p>
      <p><strong>Category:</strong> {category}</p>
      <p><a href=\"{document_link}\" target=\"_blank\" rel=\"noreferrer\">Open document compliance report</a></p>
    </body>
  </html>
  """.strip()


def _send_sendgrid_email(recipient_email: str, html_body: str) -> None:
  sendgrid_module = import_module("sendgrid")
  mail_module = import_module("sendgrid.helpers.mail")

  sendgrid_client_class = getattr(sendgrid_module, "SendGridAPIClient")
  mail_class = getattr(mail_module, "Mail")

  api_key = _required_env("SENDGRID_API_KEY")
  sender_email = _required_env("SENDGRID_FROM_EMAIL")

  message = mail_class(
    from_email=sender_email,
    to_emails=recipient_email,
    subject=SUBJECT,
    html_content=html_body,
  )

  client = sendgrid_client_class(api_key)
  response = client.send(message)
  status_code = getattr(response, "status_code", 0)
  if status_code < 200 or status_code >= 300:
    body = getattr(response, "body", "")
    raise RuntimeError(f"SendGrid send failed with status {status_code}: {body}")


def _is_permanent_delivery_error(error: Exception) -> bool:
  error_name = type(error).__name__.lower()
  if "forbidden" in error_name:
    return True
  if "unauthorized" in error_name:
    return True
  message = str(error)
  if " 400" in message or " 401" in message or " 403" in message or " 404" in message:
    return True
  return False


def process_compliance_completed(event_payload: dict[str, Any]) -> None:
  load_local_env_if_present()
  event_id = str(event_payload.get("event_id", "")).strip()
  if not event_id:
    raise RuntimeError("compliance_completed event missing event_id")

  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", ""))

  if not document_id:
    raise RuntimeError("compliance_completed event missing document_id")
  if not tenant_id:
    raise RuntimeError("compliance_completed event missing tenant_id")

  recipient_from_payload = str(payload.get("notification_recipient_email", "")).strip()
  recipient_email = recipient_from_payload or _required_env("NOTIFICATION_RECIPIENT_EMAIL")

  existing = document_repository.get_notification_by_event(event_id, TEMPLATE_NAME, recipient_email)
  if existing is not None and existing["status"] in {"sent", "pending"}:
    return

  html_body = _build_email_html(payload if isinstance(payload, dict) else {})

  if existing is not None:
    notification = existing
    _ = document_repository.update_notification_status(notification["id"], "pending")
  else:
    notification = document_repository.create_notification(
      event_id=event_id,
      document_id=document_id,
      tenant_id=tenant_id,
      recipient_email=recipient_email,
      template_name=TEMPLATE_NAME,
      channel=DEFAULT_CHANNEL,
      status="pending",
      subject=SUBJECT,
      payload={
        "event_id": event_id,
        "event_name": event_payload.get("event_name"),
        "html": html_body,
        "raw_payload": payload,
      },
    )

  try:
    _send_sendgrid_email(recipient_email, html_body)
    _ = document_repository.update_notification_status(notification["id"], "sent")
  except Exception as error:
    _ = document_repository.update_notification_status(notification["id"], "failed")
    if _is_permanent_delivery_error(error):
      return
    raise


def run_notification_worker() -> None:
  consume(QUEUE_NOTIFICATION, process_compliance_completed)
