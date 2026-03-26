import json
import os
import re
import unicodedata
from datetime import datetime
from importlib import import_module
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_NLP_COMPLETED, QUEUE_NLP, build_event
from ...core.rabbitmq import consume, publish_event


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
MAX_CHUNK_TOKENS = 300
CHUNK_OVERLAP_TOKENS = 50
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
HF_DEFAULT_MODEL = "Qwen/Qwen2.5-14B-Instruct:featherless-ai"

FRENCH_MONTHS = {
  "janvier": 1,
  "fevrier": 2,
  "février": 2,
  "mars": 3,
  "avril": 4,
  "mai": 5,
  "juin": 6,
  "juillet": 7,
  "aout": 8,
  "août": 8,
  "septembre": 9,
  "octobre": 10,
  "novembre": 11,
  "decembre": 12,
  "décembre": 12,
}

DEADLINE_KEYWORDS = [
  "date limite",
  "date limite de remise",
  "date limite de depot",
  "date limite de dépôt",
  "date de remise",
  "depot des offres",
  "dépôt des offres",
  "remise des offres",
  "soumission avant",
  "au plus tard",
  "avant le",
  "deadline",
  "submission deadline",
  "closing date",
]

BUDGET_KEYWORDS = [
  "budget",
  "montant",
  "montant estime",
  "montant estimé",
  "valeur estimee",
  "valeur estimée",
  "prix estime",
  "prix estimé",
  "cout total",
  "coût total",
  "enveloppe",
]


def _strip_diacritics(value: str) -> str:
  normalized = unicodedata.normalize("NFD", value)
  return "".join(character for character in normalized if unicodedata.category(character) != "Mn")


def _normalize_for_matching(value: str) -> str:
  lowered = value.lower()
  without_diacritics = _strip_diacritics(lowered)
  return re.sub(r"\s+", " ", without_diacritics).strip()


def _clean_text(raw_text: str) -> str:
  text = raw_text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
  text = unicodedata.normalize("NFC", text)
  text = text.replace("\ufeff", " ").replace("\x0c", " ")
  text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
  text = re.sub(r"[\|_]{2,}", " ", text)
  text = re.sub(r"\s+", " ", text)
  return text.strip()


def _detect_language(text: str) -> tuple[str, float]:
  if not text:
    return "unknown", 0.0

  langdetect_module = import_module("langdetect")
  detect_langs = getattr(langdetect_module, "detect_langs")
  detections = detect_langs(text[:5000])
  if not detections:
    return "unknown", 0.0
  top = detections[0]
  return str(getattr(top, "lang", "unknown")), float(getattr(top, "prob", 0.0))


def _sentence_segments(text: str) -> list[str]:
  if not text:
    return []

  spacy_module = import_module("spacy")
  nlp = getattr(spacy_module, "blank")("fr")
  if "sentencizer" not in nlp.pipe_names:
    nlp.add_pipe("sentencizer")

  doc = nlp(text)
  return [str(sentence.text).strip() for sentence in doc.sents if str(sentence.text).strip()]


def _tokenize(text: str) -> list[str]:
  return [token for token in text.split(" ") if token]


def _chunk_sentences(sentences: list[str], max_tokens: int, overlap_tokens: int) -> list[str]:
  chunks: list[str] = []
  current_tokens: list[str] = []

  def flush_chunk() -> None:
    nonlocal current_tokens
    if not current_tokens:
      return
    chunks.append(" ".join(current_tokens).strip())
    current_tokens = current_tokens[-overlap_tokens:] if overlap_tokens > 0 else []

  for sentence in sentences:
    sentence_tokens = _tokenize(sentence)
    if not sentence_tokens:
      continue

    if len(sentence_tokens) > max_tokens:
      flush_chunk()
      step = max(1, max_tokens - overlap_tokens)
      start = 0
      while start < len(sentence_tokens):
        end = min(start + max_tokens, len(sentence_tokens))
        chunk_tokens = sentence_tokens[start:end]
        if chunk_tokens:
          chunks.append(" ".join(chunk_tokens))
        if end >= len(sentence_tokens):
          break
        start += step
      continue

    if len(current_tokens) + len(sentence_tokens) > max_tokens:
      flush_chunk()

    current_tokens.extend(sentence_tokens)

  if current_tokens:
    chunks.append(" ".join(current_tokens).strip())

  return [chunk for chunk in chunks if chunk]


def _translate_chunks_to_english(chunks: list[str], source_lang: str) -> list[str]:
  if not chunks:
    return []

  deep_translator_module = import_module("deep_translator")
  google_translator = getattr(deep_translator_module, "GoogleTranslator")
  source = "fr" if source_lang.startswith("fr") else "auto"
  translator = google_translator(source=source, target="en")

  translated: list[str] = []
  for chunk in chunks:
    try:
      translated_chunk = translator.translate(chunk)
      translated.append(str(translated_chunk) if translated_chunk is not None else chunk)
    except Exception:
      translated.append(chunk)
  return translated


def _extract_country(text: str) -> str | None:
  normalized = _normalize_for_matching(text)
  country_patterns = {
    "france": [r"\bfrance\b", r"\bfrancais\b", r"\brepublique francaise\b"],
    "algeria": [r"\balgerie\b", r"\balgeria\b"],
    "morocco": [r"\bmaroc\b", r"\bmorocco\b"],
    "tunisia": [r"\btunisie\b", r"\btunisia\b"],
    "senegal": [r"\bsenegal\b"],
    "canada": [r"\bcanada\b", r"\bquebec\b"],
    "ivory_coast": [r"\bcote d ivoire\b", r"\bivoire\b"],
    "cameroon": [r"\bcameroun\b", r"\bcameroon\b"],
  }

  for country, patterns in country_patterns.items():
    if any(re.search(pattern, normalized) for pattern in patterns):
      return country
  return None


def _normalize_amount_token(amount_token: str, multiplier_token: str | None) -> str:
  compact = re.sub(r"\s+", "", amount_token)
  if "," in compact and "." in compact:
    normalized = compact.replace(".", "").replace(",", ".")
  elif "," in compact:
    normalized = compact.replace(",", ".")
  else:
    normalized = compact

  multiplier = (multiplier_token or "").lower().strip()
  factor = 1
  if multiplier in {"k", "mille"}:
    factor = 1_000
  elif multiplier in {"m", "mn", "million", "millions"}:
    factor = 1_000_000
  elif multiplier in {"md", "milliard", "milliards"}:
    factor = 1_000_000_000

  try:
    amount_value = float(normalized)
    computed = amount_value * factor
    if computed.is_integer():
      return str(int(computed))
    return f"{computed:.2f}"
  except Exception:
    return normalized


def _extract_budget_candidates(text: str) -> list[str]:
  normalized = _normalize_for_matching(text)
  amount_pattern = re.compile(
    r"(?P<amount>\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*"
    r"(?P<multiplier>k|m|mn|mille|million|millions|md|milliard|milliards)?\s*"
    r"(?P<currency>€|eur|euro|euros|usd|\$|mad|dzd|xof|xaf|tnd|cad|chf|gbp|da|dh)",
    re.IGNORECASE,
  )

  candidates: list[tuple[int, str]] = []
  for match in amount_pattern.finditer(normalized):
    start = max(0, match.start() - 100)
    context_window = normalized[start:match.start()]
    context_score = 2 if any(keyword in context_window for keyword in BUDGET_KEYWORDS) else 0
    amount_value = _normalize_amount_token(match.group("amount"), match.group("multiplier"))
    currency = str(match.group("currency")).upper()
    formatted = f"{amount_value} {currency}"
    candidates.append((context_score, formatted))

  context_amount_pattern = re.compile(
    r"(?:budget|montant|valeur|prix\s+estime|prix\s+estimé|enveloppe)\D{0,35}"
    r"(\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
  )
  context_match = context_amount_pattern.search(normalized)
  if context_match:
    candidates.append((1, _normalize_amount_token(context_match.group(1), None)))

  if not candidates:
    return []

  candidates.sort(key=lambda item: item[0], reverse=True)
  seen: set[str] = set()
  ordered: list[str] = []
  for _, value in candidates:
    if value not in seen:
      seen.add(value)
      ordered.append(value)
  return ordered[:5]


def _parse_date_to_iso(raw_date: str) -> str | None:
  cleaned = _normalize_for_matching(raw_date)
  iso_match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", cleaned)
  if iso_match:
    year, month, day = (int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
    try:
      return datetime(year, month, day).date().isoformat()
    except Exception:
      return None

  dmy_match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$", cleaned)
  if dmy_match:
    day, month, year = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
    if year < 100:
      year += 2000
    try:
      return datetime(year, month, day).date().isoformat()
    except Exception:
      return None

  month_name_match = re.match(r"^(\d{1,2})(?:er)?\s+([a-zA-Zéèêëàâîïôöùûüç]+)\s+(\d{4})$", cleaned)
  if month_name_match:
    day = int(month_name_match.group(1))
    month_name = month_name_match.group(2)
    year = int(month_name_match.group(3))
    month = FRENCH_MONTHS.get(month_name)
    if month is None:
      return None
    try:
      return datetime(year, month, day).date().isoformat()
    except Exception:
      return None

  return None


def _extract_deadline_candidates(text: str) -> list[str]:
  normalized = _normalize_for_matching(text)
  date_pattern = re.compile(
    r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:er)?\s+[a-zA-Zéèêëàâîïôöùûüç]+\s+\d{4})",
    re.IGNORECASE,
  )

  candidates: list[tuple[int, str]] = []
  for match in date_pattern.finditer(normalized):
    start = max(0, match.start() - 120)
    context_window = normalized[start:match.start()]
    score = 3 if any(keyword in context_window for keyword in DEADLINE_KEYWORDS) else 0
    parsed = _parse_date_to_iso(match.group(1))
    if parsed:
      candidates.append((score, parsed))

  keyword_date_pattern = re.compile(
    r"(?:date\s+limite|au\s+plus\s+tard|avant\s+le|soumission\s+avant|remise\s+des\s+offres)\D{0,40}"
    r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:er)?\s+[a-zA-Zéèêëàâîïôöùûüç]+\s+\d{4})",
    re.IGNORECASE,
  )
  keyword_match = keyword_date_pattern.search(normalized)
  if keyword_match:
    parsed = _parse_date_to_iso(keyword_match.group(1))
    if parsed:
      candidates.append((4, parsed))

  if not candidates:
    return []

  candidates.sort(key=lambda item: item[0], reverse=True)
  seen: set[str] = set()
  ordered: list[str] = []
  for _, value in candidates:
    if value not in seen:
      seen.add(value)
      ordered.append(value)
  return ordered[:5]


def _classify_category(text: str) -> str:
  normalized = _normalize_for_matching(text)
  categories = {
    "construction": ["construction", "batiment", "travaux", "chantier", "genie civil"],
    "it_services": ["informatique", "logiciel", "software", "cloud", "reseau", "cyber"],
    "consulting": ["conseil", "consulting", "audit", "assistance technique"],
    "logistics": ["transport", "logistique", "livraison", "fret"],
    "health": ["sante", "hospital", "medical", "medicament"],
    "education": ["education", "formation", "school", "universite"],
  }

  scored: dict[str, int] = {}
  for category, keywords in categories.items():
    score = sum(1 for keyword in keywords if keyword in normalized)
    if score > 0:
      scored[category] = score

  if not scored:
    return "general"
  return max(scored.items(), key=lambda item: item[1])[0]


def _extract_json_object(raw_text: str) -> dict[str, object] | None:
  stripped = raw_text.strip()
  if stripped.startswith("```"):
    stripped = stripped.replace("```json", "").replace("```", "").strip()

  try:
    parsed = json.loads(stripped)
    if isinstance(parsed, dict):
      return parsed
    return None
  except Exception:
    pass

  match = re.search(r"\{.*\}", stripped, re.DOTALL)
  if not match:
    return None

  try:
    parsed = json.loads(match.group(0))
    if isinstance(parsed, dict):
      return parsed
  except Exception:
    return None
  return None


def _refine_metadata_with_hf(
  cleaned_text: str,
  base_metadata: dict[str, object],
  deadline_candidates: list[str],
  budget_candidates: list[str],
) -> dict[str, object]:
  hf_token = os.getenv("HF_TOKEN", "").strip()
  if not hf_token:
    return base_metadata

  requests_module = import_module("requests")
  post = getattr(requests_module, "post")
  model_name = os.getenv("HF_METADATA_MODEL", HF_DEFAULT_MODEL).strip() or HF_DEFAULT_MODEL

  prompt_payload = {
    "base_metadata": base_metadata,
    "deadline_candidates": deadline_candidates,
    "budget_candidates": budget_candidates,
    "rules": {
      "deadline_format": "YYYY-MM-DD or null",
      "country": "lowercase country code-like label or null",
      "category": "one of construction,it_services,consulting,logistics,health,education,general",
      "budget": "normalized string with currency when available or null",
    },
    "text_excerpt": cleaned_text[:9000],
  }

  messages = [
    {
      "role": "system",
      "content": (
        "You extract tender metadata from French procurement text. "
        "Return only strict JSON object with keys: country, budget, deadline, category. "
        "Do not add extra text."
      ),
    },
    {
      "role": "user",
      "content": json.dumps(prompt_payload, ensure_ascii=False),
    },
  ]

  try:
    response = post(
      HF_ROUTER_URL,
      headers={"Authorization": f"Bearer {hf_token}"},
      json={
        "model": model_name,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 220,
      },
      timeout=20,
    )
    if not bool(getattr(response, "ok", False)):
      return base_metadata

    response_payload = response.json()
    choices = response_payload.get("choices", []) if isinstance(response_payload, dict) else []
    if not choices:
      return base_metadata

    first_choice = choices[0]
    message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
    content = str(message.get("content", "")) if isinstance(message, dict) else ""
    parsed = _extract_json_object(content)
    if not parsed:
      return base_metadata

    merged = dict(base_metadata)

    parsed_deadline = parsed.get("deadline")
    if isinstance(parsed_deadline, str) and parsed_deadline.strip():
      normalized_deadline = _parse_date_to_iso(parsed_deadline.strip()) or parsed_deadline.strip()
      merged["deadline"] = normalized_deadline

    parsed_budget = parsed.get("budget")
    if isinstance(parsed_budget, str) and parsed_budget.strip():
      merged["budget"] = parsed_budget.strip()

    parsed_country = parsed.get("country")
    if isinstance(parsed_country, str) and parsed_country.strip():
      merged["country"] = _normalize_for_matching(parsed_country.strip()).replace(" ", "_")

    parsed_category = parsed.get("category")
    if isinstance(parsed_category, str) and parsed_category.strip():
      category = _normalize_for_matching(parsed_category.strip())
      allowed_categories = {
        "construction",
        "it_services",
        "consulting",
        "logistics",
        "health",
        "education",
        "general",
      }
      merged["category"] = category if category in allowed_categories else str(base_metadata.get("category", "general"))

    merged["metadata_source"] = "rules_plus_hf"
    return merged
  except Exception:
    return base_metadata


def _build_metadata(cleaned_text: str, language: str, confidence: float) -> dict[str, object]:
  deadline_candidates = _extract_deadline_candidates(cleaned_text)
  budget_candidates = _extract_budget_candidates(cleaned_text)

  base_metadata: dict[str, object] = {
    "language": {
      "code": language,
      "confidence": round(confidence, 4),
    },
    "country": _extract_country(cleaned_text),
    "budget": budget_candidates[0] if budget_candidates else None,
    "deadline": deadline_candidates[0] if deadline_candidates else None,
    "category": _classify_category(cleaned_text),
    "candidates": {
      "deadline": deadline_candidates,
      "budget": budget_candidates,
    },
    "metadata_source": "rules",
  }

  return _refine_metadata_with_hf(cleaned_text, base_metadata, deadline_candidates, budget_candidates)


def process_ocr_complete(event_payload: dict[str, Any]) -> None:
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", DEFAULT_TENANT_ID))
  filename = str(payload.get("filename", "uploaded-file"))
  ocr_text = str(payload.get("ocr_text", ""))

  if not document_id:
    raise RuntimeError("ocr_complete event missing document_id")

  cleaned_text = _clean_text(ocr_text)
  language, confidence = _detect_language(cleaned_text)
  sentences = _sentence_segments(cleaned_text)
  chunks = _chunk_sentences(sentences, MAX_CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)
  translated_chunks = _translate_chunks_to_english(chunks, language)
  metadata = _build_metadata(cleaned_text, language, confidence)

  document_repository.replace_document_chunks(document_id, chunks, translated_chunks)
  _ = document_repository.update_document_nlp_result(
    document_id=document_id,
    tenant_id=tenant_id,
    status="nlp_completed",
    chunk_count=len(chunks),
    metadata=metadata,
  )

  completion_event = build_event(
    EVENT_NLP_COMPLETED,
    {
      "document_id": document_id,
      "tenant_id": tenant_id,
      "filename": filename,
      "status": "nlp_completed",
      "chunk_count": len(chunks),
      "metadata": metadata,
    },
  )
  publish_event(EVENT_NLP_COMPLETED, completion_event)


def run_nlp_worker() -> None:
  consume(QUEUE_NLP, process_ocr_complete)
