import os
import re
from dataclasses import dataclass
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_COMPLIANCE_COMPLETED, build_event
from ...core.rabbitmq import publish_event



DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class RuleCheck:
  code: str
  requirement: str
  weight: float
  met: bool
  confidence: float
  actual: str


def _extract_entities(full_text: str) -> dict[str, str | None]:
  text = full_text
  reference = re.search(r"\b(?:AO|A0)[-\s:]?\d{4}[-\s:]?\d+\b", text, re.IGNORECASE)
  deadline = re.search(r"\b\d{1,2}\s+[A-Za-zéèêëàâîïôöùûüç]+\s+\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
  budget = re.search(r"\b\d[\d\s.,]*(?:MAD|DZD|EUR|USD|DT|€|\$)\b", text, re.IGNORECASE)
  organization = re.search(r"(?:Ministry|Minist[eè]re|Office|Agence)[^\n,.]{0,120}", text, re.IGNORECASE)
  location = re.search(r"(?:Location|Lieu|Ville)\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
  duration = re.search(r"\b\d+\s*(?:months|mois|ans|years)\b", text, re.IGNORECASE)
  category = re.search(r"(?:Category|Cat[eé]gorie)\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
  contact = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+?\d[\d\-\s]{7,}", text)

  return {
    "reference": reference.group(0).strip() if reference else None,
    "deadline": deadline.group(0).strip() if deadline else None,
    "budget": budget.group(0).strip() if budget else None,
    "organization": organization.group(0).strip() if organization else None,
    "location": location.group(1).strip() if location else None,
    "duration": duration.group(0).strip() if duration else None,
    "category": category.group(1).strip() if category else None,
    "contact": contact.group(0).strip() if contact else None,
  }


def _extract_revenue_mad(profile: dict[str, object]) -> float:
  revenue_raw = str(profile.get("annual_revenue", profile.get("Annual Revenue", "0")))
  digits = re.sub(r"[^\d.]", "", revenue_raw.replace(",", ""))
  if not digits:
    return 0.0
  try:
    value = float(digits)
  except Exception:
    return 0.0

  normalized = revenue_raw.lower()
  if "b" in normalized and "billion" in normalized:
    return value * 1_000_000_000
  if "m" in normalized or "million" in normalized:
    return value * 1_000_000
  return value


def _extract_years_experience(profile: dict[str, object]) -> float:
  raw = str(profile.get("experience", profile.get("Experience", "0")))
  match = re.search(r"\d+(?:\.\d+)?", raw)
  if not match:
    return 0.0
  try:
    return float(match.group(0))
  except Exception:
    return 0.0


def _extract_team_size(profile: dict[str, object]) -> int:
  raw = str(profile.get("team_size", profile.get("Team Size", "0")))
  match = re.search(r"\d+", raw)
  if not match:
    return 0
  try:
    return int(match.group(0))
  except Exception:
    return 0


def _extract_certifications(profile: dict[str, object]) -> str:
  certs = profile.get("certifications", profile.get("Certifications", ""))
  if isinstance(certs, list):
    return " ".join(str(item) for item in certs)
  return str(certs)


def _evaluate_rules(profile: dict[str, object], entities: dict[str, str | None]) -> list[RuleCheck]:
  certifications = _extract_certifications(profile).lower()
  years_experience = _extract_years_experience(profile)
  revenue_mad = _extract_revenue_mad(profile)
  team_size = _extract_team_size(profile)
  document_has_budget = entities.get("budget") is not None

  checks = [
    RuleCheck(
      code="iso_9001",
      requirement="ISO 9001 certification present",
      weight=0.30,
      met="iso 9001" in certifications,
      confidence=0.95 if "iso 9001" in certifications else 0.8,
      actual=certifications,
    ),
    RuleCheck(
      code="experience_gt_10",
      requirement="Experience greater than 10 years",
      weight=0.25,
      met=years_experience >= 10,
      confidence=0.92,
      actual=f"{years_experience} years",
    ),
    RuleCheck(
      code="revenue_gt_100m_mad",
      requirement="Annual revenue greater than 100M MAD",
      weight=0.25,
      met=revenue_mad >= 100_000_000,
      confidence=0.9,
      actual=f"{revenue_mad:.0f} MAD",
    ),
    RuleCheck(
      code="technical_team",
      requirement="Technical team has at least 5 members",
      weight=0.20,
      met=team_size >= 5,
      confidence=0.88,
      actual=f"{team_size} members",
    ),
  ]

  if not document_has_budget:
    checks.append(
      RuleCheck(
        code="doc_budget_detected",
        requirement="Tender budget is detectable in document",
        weight=0.05,
        met=False,
        confidence=0.7,
        actual="missing",
      )
    )

  return checks


def _compute_report(checks: list[RuleCheck], entities: dict[str, str | None]) -> dict[str, Any]:
  if not checks:
    return {
      "eligibility_score": 0.0,
      "recommendation": "not_eligible",
      "requirements_met": [],
      "requirements_not_met": [],
      "warnings": ["No requirements evaluated"],
      "entities": entities,
    }

  total_weight = sum(check.weight for check in checks)
  achieved_weight = sum(check.weight for check in checks if check.met)
  score = round((achieved_weight / total_weight) * 100, 2) if total_weight > 0 else 0.0

  met_items = [
    {
      "code": check.code,
      "requirement": check.requirement,
      "weight": check.weight,
      "met": check.met,
      "confidence": check.confidence,
      "actual": check.actual,
    }
    for check in checks if check.met
  ]
  not_met_items = [
    {
      "code": check.code,
      "requirement": check.requirement,
      "weight": check.weight,
      "met": check.met,
      "confidence": check.confidence,
      "actual": check.actual,
    }
    for check in checks if not check.met
  ]

  warnings: list[str] = []
  for key in ["reference", "deadline", "budget", "organization", "location", "duration", "category", "contact"]:
    if entities.get(key) is None:
      warnings.append(f"Missing entity: {key}")

  recommendation = "eligible" if score >= 70 else "review_required" if score >= 50 else "not_eligible"

  return {
    "eligibility_score": score,
    "recommendation": recommendation,
    "requirements_met": met_items,
    "requirements_not_met": not_met_items,
    "warnings": warnings,
    "entities": entities,
  }


def process_embedding_complete(event_payload: dict[str, Any]) -> None:
  event_id = str(event_payload.get("event_id", ""))
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", DEFAULT_TENANT_ID))

  if not document_id:
    raise RuntimeError("embedding_complete event missing document_id")

  document = document_repository.get_document(document_id, tenant_id)
  if document is None:
    return

  if document.status == "compliance_completed":
    return

  if not document_repository.update_document_status_if_current(
    document_id,
    tenant_id,
    "embedding_complete",
    "compliance_processing",
  ):
    latest = document_repository.get_document(document_id, tenant_id)
    if latest is None or latest.status in {"compliance_completed", "compliance_processing"}:
      return
    _ = document_repository.update_document_status(document_id, tenant_id, "compliance_processing")

  chunks = document_repository.list_document_chunks(document_id)
  full_text = "\n\n".join(str(chunk.get("content", "")) for chunk in chunks if str(chunk.get("content", "")).strip())

  profile_row = document_repository.get_company_profile(tenant_id)
  profile = profile_row["profile"] if profile_row else {}

  entities = _extract_entities(full_text)
  checks = _evaluate_rules(profile, entities)
  report = _compute_report(checks, entities)
  requirements_met = report.get("requirements_met")
  requirements_not_met = report.get("requirements_not_met")

  met_list = requirements_met if isinstance(requirements_met, list) else []
  not_met_list = requirements_not_met if isinstance(requirements_not_met, list) else []

  requirements_payload: list[dict[str, object]] = []
  for item in [*met_list, *not_met_list]:
    if not isinstance(item, dict):
      continue
    requirement_text = item.get("requirement")
    requirement_code = item.get("code")
    weight = item.get("weight")
    met = item.get("met")
    confidence = item.get("confidence")
    actual = item.get("actual")
    requirements_payload.append(
      {
        "requirement_text": str(requirement_text) if requirement_text is not None else "",
        "requirement_code": str(requirement_code) if requirement_code is not None else None,
        "category": "compliance",
        "weight": float(weight) if isinstance(weight, (int, float)) else None,
        "met": bool(met) if isinstance(met, bool) else None,
        "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
        "actual_value": str(actual) if actual is not None else None,
      }
    )

  document_repository.replace_requirements(document_id, requirements_payload)
  eligibility_score_raw = report.get("eligibility_score", 0.0)
  if isinstance(eligibility_score_raw, (int, float)):
    eligibility_score = float(eligibility_score_raw)
  else:
    eligibility_score = 0.0

  recommendation_raw = report.get("recommendation", "review_required")
  recommendation = str(recommendation_raw)

  _ = document_repository.upsert_compliance_report(
    document_id=document_id,
    eligibility_score=eligibility_score,
    recommendation=recommendation,
    report={
      **report,
      "event_id": event_id if event_id else None,
      "company_profile_snapshot": profile,
    },
  )

  _ = document_repository.update_document_status(document_id, tenant_id, "compliance_completed")

  metadata = document.metadata if isinstance(document.metadata, dict) else {}
  budget_raw = metadata.get("budget")
  budget_entry: dict[str, object] = budget_raw if isinstance(budget_raw, dict) else {}
  deadline_raw = metadata.get("deadline")
  deadline_entry: dict[str, object] = deadline_raw if isinstance(deadline_raw, dict) else {}
  category_raw = metadata.get("category")
  category_entry: dict[str, object] = category_raw if isinstance(category_raw, dict) else {}

  web_base_url = os.getenv("WEB_BASE_URL", "http://localhost:3000")
  compliance_event = build_event(
    EVENT_COMPLIANCE_COMPLETED,
    {
      "document_id": document_id,
      "tenant_id": tenant_id,
      "document_filename": document.filename,
      "status": "compliance_completed",
      "eligibility_score": eligibility_score,
      "recommendation": recommendation,
      "budget": budget_entry.get("value"),
      "deadline": deadline_entry.get("value"),
      "category": category_entry.get("value"),
      "document_link": f"{web_base_url}/documents/{document_id}/compliance",
      "report": report,
    },
  )
  publish_event(EVENT_COMPLIANCE_COMPLETED, compliance_event)
