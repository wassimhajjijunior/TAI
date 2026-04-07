import json
import os
import re
from datetime import datetime
from importlib import import_module

from .constants import FRENCH_MONTHS, HF_DEFAULT_MODEL, HF_ROUTER_URL, METADATA_TOP_CHUNKS, TASK_KEYWORDS
from .models import Candidate, TextChunk
from .text_utils import normalize_for_matching


def score_chunk_for_task(chunk: TextChunk, task_name: str) -> int:
  normalized = normalize_for_matching(chunk.text)
  keywords = TASK_KEYWORDS.get(task_name, [])
  score = 0
  for keyword in keywords:
    if keyword in normalized:
      score += 2
  if task_name == "deadline" and re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", normalized):
    score += 1
  if task_name == "budget" and re.search(r"\b\d[\d\s.,]*(?:€|eur|usd|mad|dzd|xof|xaf|tnd|dt|cad|chf|gbp|da|dh)\b", normalized):
    score += 1
  return score


def select_relevant_chunks(chunks: list[TextChunk], task_name: str, top_n: int) -> list[TextChunk]:
  scored = [(chunk, score_chunk_for_task(chunk, task_name)) for chunk in chunks]
  scored.sort(key=lambda item: (item[1], -item[0].index), reverse=True)
  selected = [item[0] for item in scored[:top_n] if item[1] > 0]
  if selected:
    return selected
  return chunks[:top_n]


def parse_date_to_iso(raw_date: str) -> str | None:
  cleaned = normalize_for_matching(raw_date)
  iso_match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", cleaned)
  if iso_match:
    try:
      return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))).date().isoformat()
    except Exception:
      return None

  dmy_match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$", cleaned)
  if dmy_match:
    year = int(dmy_match.group(3))
    if year < 100:
      year += 2000
    try:
      return datetime(year, int(dmy_match.group(2)), int(dmy_match.group(1))).date().isoformat()
    except Exception:
      return None

  month_match = re.match(r"^(\d{1,2})(?:er)?\s+([a-zA-Zéèêëàâîïôöùûüç]+)\s+(\d{4})$", cleaned)
  if month_match:
    month = FRENCH_MONTHS.get(month_match.group(2))
    if month is None:
      return None
    try:
      return datetime(int(month_match.group(3)), month, int(month_match.group(1))).date().isoformat()
    except Exception:
      return None
  return None


def extract_deadline_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  pattern = re.compile(
    r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:er)?\s+[a-zA-Zéèêëàâîïôöùûüç]+\s+\d{4})",
    re.IGNORECASE,
  )
  candidates: list[Candidate] = []
  for chunk in chunks:
    normalized = normalize_for_matching(chunk.text)
    for match in pattern.finditer(normalized):
      parsed = parse_date_to_iso(match.group(1))
      if not parsed:
        continue
      left = normalized[max(0, match.start() - 120):match.start()]
      score = 0.6
      if any(keyword in left for keyword in TASK_KEYWORDS["deadline"]):
        score = 0.88
      candidates.append(
        Candidate(
          value=parsed,
          score=score,
          evidence_text=chunk.text[:500],
          source_chunk_index=chunk.index,
          metadata_source="rules",
        )
      )
  return candidates


def normalize_amount(amount_token: str) -> str:
  compact = re.sub(r"\s+", "", amount_token)
  if "," in compact and "." in compact:
    return compact.replace(".", "").replace(",", ".")
  if "," in compact:
    return compact.replace(",", ".")
  return compact


def normalize_currency_unit(currency_token: str) -> str:
  normalized = normalize_for_matching(currency_token)
  normalized = normalized.replace("d.t", "dt")
  compact = re.sub(r"[^a-z0-9]+", "", normalized)

  if compact in {"dt", "tnd"}:
    return "DT"
  if compact == "mdt":
    return "DT"
  if "dinar" in normalized and "tunis" in normalized:
    return "DT"
  if normalized in {"dinar", "dinars"}:
    return "DT"

  currency_map = {
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "$": "USD",
    "usd": "USD",
    "mad": "MAD",
    "dh": "MAD",
    "dzd": "DZD",
    "da": "DZD",
    "tnd": "DT",
    "dt": "DT",
    "xof": "XOF",
    "xaf": "XAF",
    "cad": "CAD",
    "chf": "CHF",
    "gbp": "GBP",
    "dirham": "MAD",
    "dirhams": "MAD",
  }
  return currency_map.get(normalized, currency_token.upper())


def parse_budget_value(raw_value: str) -> tuple[str, str] | None:
  normalized = normalize_for_matching(raw_value)
  normalized = normalized.replace("d.t", "dt")

  tunisia_keyword_pattern = re.compile(
    r"(?:dinar(?:s)?\s+tunis(?:ien|iens|ienne|iennes)|dinars?|dt|tnd|mdt)",
    re.IGNORECASE,
  )
  tunisian_keyword_match = tunisia_keyword_pattern.search(normalized)
  if tunisian_keyword_match:
    before = normalized[:tunisian_keyword_match.start()]
    after = normalized[tunisian_keyword_match.end():]
    amount_pattern = re.compile(r"\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?")
    before_matches = list(amount_pattern.finditer(before))
    amount_match = amount_pattern.search(after) or (before_matches[-1] if before_matches else None)
    if amount_match:
      amount_raw = normalize_amount(amount_match.group(0))
      factor = 1
      if re.sub(r"[^a-z0-9]+", "", tunisian_keyword_match.group(0).lower()) == "mdt":
        factor = 1_000_000
      try:
        numeric = float(amount_raw) * factor
        amount_normalized = str(int(numeric)) if numeric.is_integer() else f"{numeric:.2f}"
      except Exception:
        amount_normalized = amount_raw
      return amount_normalized, "DT"

  amount_token = r"(?P<amount>\d+(?:[.,]\d{1,2})?|\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d{1,2})?)"
  multiplier_token = r"(?P<mult>k|m|mn|mille|million|millions|md|milliard|milliards)?"
  currency_token = (
    r"(?P<cur>€|eur|euro|euros|usd|\$|mad|dzd|xof|xaf|tnd|dt|cad|chf|gbp|"
    r"da|dh|dirham|dirhams|dinar|dinars|dinar[s]?\s+tunis(?:ien|iens)?|"
    r"d\s*\.?\s*t|mdt)"
  )

  patterns = [
    re.compile(rf"{amount_token}\s*{multiplier_token}\s*(?:de\s+)?{currency_token}", re.IGNORECASE),
    re.compile(rf"{currency_token}\s*{amount_token}\s*{multiplier_token}", re.IGNORECASE),
    re.compile(
      rf"(?P<prefix>budget|montant|enveloppe|prix|valeur|co[uû]t)[^\d\n]{{0,30}}"
      rf"(?P<cur>dinar[s]?\s+tunis(?:ien|iens)?|dinar|dinars|dt|tnd|mdt)\s*[:\-]?\s*"
      rf"(?P<amount>\d{{1,3}}(?:[\s.,]\d{{3}})+(?:[.,]\d{{1,2}})?|\d+(?:[.,]\d{{1,2}})?)"
      rf"\s*(?P<mult>k|m|mn|mille|million|millions|md|milliard|milliards)?",
      re.IGNORECASE,
    ),
  ]

  for pattern in patterns:
    match = pattern.search(normalized)
    if not match:
      continue

    amount = normalize_amount(match.group("amount"))
    multiplier = (match.group("mult") or "").lower()
    factor = 1
    if multiplier in {"k", "mille"}:
      factor = 1000
    elif multiplier in {"m", "mn", "million", "millions"}:
      factor = 1_000_000
    elif multiplier in {"md", "milliard", "milliards"}:
      factor = 1_000_000_000

    try:
      numeric = float(amount) * factor
      currency_token_raw = str(match.group("cur"))
      if re.sub(r"[^a-z0-9]+", "", normalize_for_matching(currency_token_raw)) == "mdt" and factor == 1:
        numeric *= 1_000_000
      amount_normalized = str(int(numeric)) if numeric.is_integer() else f"{numeric:.2f}"
    except Exception:
      amount_normalized = amount

    currency = normalize_currency_unit(match.group("cur"))
    return amount_normalized, currency

  return None


def normalize_budget_value(value: str) -> str:
  parsed = parse_budget_value(value)
  if parsed is None:
    return ""
  amount, currency = parsed
  return f"{amount} {currency}"


def has_budget_unit(value: str) -> bool:
  normalized = normalize_for_matching(value)
  return bool(
    re.search(r"\b(?:eur|usd|mad|dzd|dt|xof|xaf|cad|chf|gbp)\b", normalized)
    or "€" in value
    or "$" in value
  )


def extract_budget_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  amount_token = r"(?P<amount>\d+(?:[.,]\d{1,2})?|\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d{1,2})?)"
  multiplier_token = r"(?P<mult>k|m|mn|mille|million|millions|md|milliard|milliards)?"
  currency_token = (
    r"(?P<cur>€|eur|euro|euros|usd|\$|mad|dzd|xof|xaf|tnd|dt|cad|chf|gbp|"
    r"da|dh|dirham|dirhams|dinar|dinars|dinar[s]?\s+tunis(?:ien|iens)?|"
    r"d\s*\.?\s*t|mdt)"
  )
  patterns = [
    re.compile(rf"{amount_token}\s*{multiplier_token}\s*(?:de\s+)?{currency_token}", re.IGNORECASE),
    re.compile(rf"{currency_token}\s*{amount_token}\s*{multiplier_token}", re.IGNORECASE),
  ]

  candidates: list[Candidate] = []
  contexts: list[tuple[int, str]] = []
  for index, chunk in enumerate(chunks):
    contexts.append((chunk.index, chunk.text))
    if index + 1 < len(chunks):
      contexts.append((chunk.index, f"{chunk.text} {chunks[index + 1].text}"))

  for source_chunk_index, context_text in contexts:
    normalized = normalize_for_matching(context_text)
    matched_in_context = False
    for pattern in patterns:
      for match in pattern.finditer(normalized):
        parsed = parse_budget_value(match.group(0))
        if parsed is None:
          continue
        amount_normalized, currency = parsed
        value = f"{amount_normalized} {currency}"
        left = normalized[max(0, match.start() - 120):match.start()]
        score = 0.62
        if any(keyword in left for keyword in TASK_KEYWORDS["budget"]):
          score = 0.9
        candidates.append(
          Candidate(
            value=value,
            score=score,
            evidence_text=context_text[:500],
            source_chunk_index=source_chunk_index,
            metadata_source="rules",
          )
        )
        matched_in_context = True

    if not matched_in_context:
      parsed_context = parse_budget_value(normalized)
      if parsed_context is not None:
        amount_normalized, currency = parsed_context
        context_score = 0.9 if any(keyword in normalized for keyword in TASK_KEYWORDS["budget"]) else 0.7
        candidates.append(
          Candidate(
            value=f"{amount_normalized} {currency}",
            score=context_score,
            evidence_text=context_text[:500],
            source_chunk_index=source_chunk_index,
            metadata_source="rules",
          )
        )
  return candidates


def extract_country_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  patterns: dict[str, list[str]] = {
    "france": [r"\bfrance\b", r"\bfrancais\b", r"\brepublique francaise\b"],
    "algeria": [r"\balgerie\b", r"\balgeria\b"],
    "morocco": [r"\bmaroc\b", r"\bmorocco\b"],
    "tunisia": [r"\btunisie\b", r"\btunisia\b"],
    "senegal": [r"\bsenegal\b"],
    "canada": [r"\bcanada\b", r"\bquebec\b"],
    "ivory_coast": [r"\bcote d ivoire\b"],
    "cameroon": [r"\bcameroun\b", r"\bcameroon\b"],
  }
  candidates: list[Candidate] = []
  for chunk in chunks:
    normalized = normalize_for_matching(chunk.text)
    for country, country_patterns in patterns.items():
      if any(re.search(pattern, normalized) for pattern in country_patterns):
        candidates.append(
          Candidate(
            value=country,
            score=0.84,
            evidence_text=chunk.text[:500],
            source_chunk_index=chunk.index,
            metadata_source="rules",
          )
        )
  return candidates


def category_from_text(text: str) -> tuple[str, float]:
  normalized = normalize_for_matching(text)
  categories = {
    "construction": ["construction", "batiment", "travaux", "chantier", "genie civil"],
    "it_services": ["informatique", "logiciel", "software", "cloud", "reseau", "cyber"],
    "consulting": ["conseil", "consulting", "audit", "assistance technique"],
    "logistics": ["transport", "logistique", "livraison", "fret"],
    "health": ["sante", "hospital", "medical", "medicament"],
    "education": ["education", "formation", "school", "universite"],
  }
  best_category = "general"
  best_score = 0
  for category, keywords in categories.items():
    score = sum(1 for keyword in keywords if keyword in normalized)
    if score > best_score:
      best_category = category
      best_score = score
  confidence = 0.55 if best_category == "general" else min(0.95, 0.6 + (best_score * 0.1))
  return best_category, confidence


def extract_category_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  candidates: list[Candidate] = []
  for chunk in chunks:
    category, confidence = category_from_text(chunk.text)
    candidates.append(
      Candidate(
        value=category,
        score=confidence,
        evidence_text=chunk.text[:500],
        source_chunk_index=chunk.index,
        metadata_source="rules",
      )
    )
  return candidates


def dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
  seen: set[str] = set()
  ordered: list[Candidate] = []
  for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
    key = candidate.value
    if key in seen:
      continue
    seen.add(key)
    ordered.append(candidate)
  return ordered


def is_ambiguous(candidates: list[Candidate]) -> bool:
  if len(candidates) < 2:
    return False
  sorted_candidates = sorted(candidates, key=lambda item: item.score, reverse=True)
  return abs(sorted_candidates[0].score - sorted_candidates[1].score) <= 0.06


def extract_json_object(raw_text: str) -> dict[str, object] | None:
  stripped = raw_text.strip()
  if stripped.startswith("```"):
    stripped = stripped.replace("```json", "").replace("```", "").strip()
  try:
    parsed = json.loads(stripped)
    if isinstance(parsed, dict):
      return parsed
  except Exception:
    pass
  match = re.search(r"\{.*\}", stripped, re.DOTALL)
  if not match:
    return None
  try:
    parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else None
  except Exception:
    return None


def resolve_with_hf(task_name: str, relevant_chunks: list[TextChunk], candidates: list[Candidate]) -> Candidate | None:
  hf_token = os.getenv("HF_TOKEN", "").strip()
  if not hf_token:
    return None
  requests_module = import_module("requests")
  post = getattr(requests_module, "post")
  model_name = os.getenv("HF_METADATA_MODEL", HF_DEFAULT_MODEL).strip() or HF_DEFAULT_MODEL

  payload = {
    "task": task_name,
    "candidate_values": [candidate.value for candidate in candidates],
    "chunks": [{"index": chunk.index, "text": chunk.text[:800]} for chunk in relevant_chunks],
    "rules": "Choose the best value by contextual evidence. Return strict JSON with keys value, confidence, evidence_text, source_chunk_index.",
  }

  try:
    response = post(
      HF_ROUTER_URL,
      headers={"Authorization": f"Bearer {hf_token}"},
      json={
        "model": model_name,
        "messages": [
          {
            "role": "system",
            "content": "You return only JSON. No markdown. No explanation.",
          },
          {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
          },
        ],
        "temperature": 0.0,
        "max_tokens": 220,
      },
      timeout=20,
    )
    if not bool(getattr(response, "ok", False)):
      return None
    response_payload = response.json()
    choices = response_payload.get("choices", []) if isinstance(response_payload, dict) else []
    if not choices:
      return None
    first_choice = choices[0]
    message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
    content = str(message.get("content", "")) if isinstance(message, dict) else ""
    parsed = extract_json_object(content)
    if not parsed:
      return None

    value = str(parsed.get("value", "")).strip()
    if not value:
      return None
    confidence_raw = parsed.get("confidence", 0.75)
    confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float, str)) else 0.75
    evidence_text = str(parsed.get("evidence_text", "")).strip() or relevant_chunks[0].text[:500]
    source_chunk_raw = parsed.get("source_chunk_index", relevant_chunks[0].index)
    source_chunk_index = int(source_chunk_raw) if isinstance(source_chunk_raw, (int, float, str)) else relevant_chunks[0].index

    if task_name == "deadline":
      parsed_date = parse_date_to_iso(value)
      value = parsed_date if parsed_date else value
    if task_name == "budget":
      value = normalize_budget_value(value)

    return Candidate(
      value=value,
      score=max(0.0, min(1.0, confidence)),
      evidence_text=evidence_text[:500],
      source_chunk_index=source_chunk_index,
      metadata_source="hf_llm",
    )
  except Exception:
    return None


def metadata_item(value: str | None, confidence: float, evidence_text: str, source_chunk_index: int | None, metadata_source: str) -> dict[str, object]:
  return {
    "value": value,
    "confidence": round(max(0.0, min(1.0, confidence)), 4),
    "evidence_text": evidence_text,
    "source_chunk_index": source_chunk_index,
    "metadata_source": metadata_source,
  }


def resolve_task(task_name: str, relevant_chunks: list[TextChunk], all_chunks: list[TextChunk]) -> dict[str, object]:
  extractor_map = {
    "deadline": extract_deadline_candidates,
    "budget": extract_budget_candidates,
    "country": extract_country_candidates,
    "category": extract_category_candidates,
  }
  extractor = extractor_map[task_name]
  candidates = dedupe_candidates(extractor(relevant_chunks))

  if not candidates:
    fallback_candidates = dedupe_candidates(extractor(all_chunks))
    if not fallback_candidates:
      return metadata_item(None, 0.0, "", None, "rules_fallback")
    best_fallback = fallback_candidates[0]
    if task_name == "budget":
      fallback_value = normalize_budget_value(best_fallback.value)
      if not fallback_value:
        return metadata_item(None, 0.0, "", None, "rules_fallback")
      return metadata_item(
        fallback_value,
        best_fallback.score,
        best_fallback.evidence_text,
        best_fallback.source_chunk_index,
        "rules_fallback",
      )
    return metadata_item(
      best_fallback.value,
      best_fallback.score,
      best_fallback.evidence_text,
      best_fallback.source_chunk_index,
      "rules_fallback",
    )

  if is_ambiguous(candidates):
    llm_choice = resolve_with_hf(task_name, relevant_chunks, candidates)
    if llm_choice is not None:
      if task_name == "budget":
        llm_value = normalize_budget_value(llm_choice.value)
        if llm_value:
          return metadata_item(
            llm_value,
            llm_choice.score,
            llm_choice.evidence_text,
            llm_choice.source_chunk_index,
            llm_choice.metadata_source,
          )
      else:
        return metadata_item(
          llm_choice.value,
          llm_choice.score,
          llm_choice.evidence_text,
          llm_choice.source_chunk_index,
          llm_choice.metadata_source,
        )

  if task_name == "budget":
    budget_candidates = [candidate for candidate in candidates if has_budget_unit(candidate.value)]
    if budget_candidates:
      best_budget = budget_candidates[0]
      best_budget_value = normalize_budget_value(best_budget.value)
      if best_budget_value:
        return metadata_item(
          best_budget_value,
          best_budget.score,
          best_budget.evidence_text,
          best_budget.source_chunk_index,
          best_budget.metadata_source,
        )

    fallback_budget_candidates = dedupe_candidates(extract_budget_candidates(all_chunks))
    if fallback_budget_candidates:
      fallback_budget = fallback_budget_candidates[0]
      fallback_budget_value = normalize_budget_value(fallback_budget.value)
      if fallback_budget_value:
        return metadata_item(
          fallback_budget_value,
          fallback_budget.score,
          fallback_budget.evidence_text,
          fallback_budget.source_chunk_index,
          "rules_fallback",
        )
    return metadata_item(None, 0.0, "", None, "rules_fallback")

  best = candidates[0]
  return metadata_item(best.value, best.score, best.evidence_text, best.source_chunk_index, best.metadata_source)


def build_metadata(chunks: list[TextChunk], language: str, confidence: float) -> dict[str, object]:
  deadline_chunks = select_relevant_chunks(chunks, "deadline", METADATA_TOP_CHUNKS)
  budget_chunks = select_relevant_chunks(chunks, "budget", METADATA_TOP_CHUNKS)
  country_chunks = select_relevant_chunks(chunks, "country", METADATA_TOP_CHUNKS)
  category_chunks = select_relevant_chunks(chunks, "category", METADATA_TOP_CHUNKS)

  return {
    "language": {
      "value": language,
      "confidence": round(confidence, 4),
      "metadata_source": "langdetect",
    },
    "deadline": resolve_task("deadline", deadline_chunks, chunks),
    "budget": resolve_task("budget", budget_chunks, chunks),
    "country": resolve_task("country", country_chunks, chunks),
    "category": resolve_task("category", category_chunks, chunks),
  }
