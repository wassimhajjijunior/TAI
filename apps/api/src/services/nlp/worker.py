import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from typing import Any

from ...core import document_repository
from ...core.pipeline_events import EVENT_NLP_COMPLETED, QUEUE_NLP, build_event
from ...core.rabbitmq import consume, publish_event


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
MAX_CHUNK_TOKENS = 300
CHUNK_OVERLAP_TOKENS = 50
METADATA_TOP_CHUNKS = 6
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

TASK_KEYWORDS: dict[str, list[str]] = {
  "deadline": [
    "date limite",
    "date limite de remise",
    "date de remise",
    "soumission avant",
    "au plus tard",
    "avant le",
    "deadline",
    "closing date",
  ],
  "budget": [
    "budget",
    "montant",
    "montant estime",
    "valeur estimee",
    "prix estime",
    "enveloppe",
    "cout total",
  ],
  "country": [
    "france",
    "algerie",
    "maroc",
    "tunisie",
    "senegal",
    "canada",
    "cote d ivoire",
    "cameroun",
  ],
  "category": [
    "construction",
    "travaux",
    "informatique",
    "logiciel",
    "consulting",
    "conseil",
    "transport",
    "logistique",
    "sante",
    "formation",
  ],
}


@dataclass(frozen=True)
class TextChunk:
  index: int
  text: str


@dataclass(frozen=True)
class Candidate:
  value: str
  score: float
  evidence_text: str
  source_chunk_index: int
  metadata_source: str


def _strip_diacritics(value: str) -> str:
  normalized = unicodedata.normalize("NFD", value)
  return "".join(character for character in normalized if unicodedata.category(character) != "Mn")


def _normalize_for_matching(value: str) -> str:
  lowered = value.lower()
  without_diacritics = _strip_diacritics(lowered)
  return re.sub(r"\s+", " ", without_diacritics).strip()


def _clean_text_preserve_structure(raw_text: str) -> str:
  text = raw_text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
  text = unicodedata.normalize("NFC", text)
  text = text.replace("\r\n", "\n").replace("\r", "\n")
  text = text.replace("\ufeff", "").replace("\x0c", "\n")
  text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)

  cleaned_lines: list[str] = []
  blank_count = 0
  for raw_line in text.split("\n"):
    line = re.sub(r"[\t ]+", " ", raw_line).strip()
    if not line:
      blank_count += 1
      if blank_count <= 2:
        cleaned_lines.append("")
      continue
    blank_count = 0
    cleaned_lines.append(line)

  cleaned = "\n".join(cleaned_lines).strip()
  return cleaned


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


def _split_paragraphs(text: str) -> list[str]:
  if not text:
    return []
  parts = re.split(r"\n\s*\n+", text)
  return [part.strip() for part in parts if part.strip()]


def _tokenize(text: str) -> list[str]:
  return [token for token in text.split(" ") if token]


def _segment_sentences(paragraph_text: str) -> list[str]:
  spacy_module = import_module("spacy")
  nlp = getattr(spacy_module, "blank")("fr")
  if "sentencizer" not in nlp.pipe_names:
    nlp.add_pipe("sentencizer")
  doc = nlp(paragraph_text)
  sentences = [str(sentence.text).strip() for sentence in doc.sents if str(sentence.text).strip()]
  return sentences if sentences else [paragraph_text]


def _build_chunks(paragraphs: list[str], max_tokens: int, overlap_tokens: int) -> list[TextChunk]:
  chunks: list[TextChunk] = []
  current_tokens: list[str] = []

  def flush_chunk() -> None:
    nonlocal current_tokens
    if not current_tokens:
      return
    chunks.append(TextChunk(index=len(chunks), text=" ".join(current_tokens).strip()))
    current_tokens = current_tokens[-overlap_tokens:] if overlap_tokens > 0 else []

  for paragraph in paragraphs:
    for sentence in _segment_sentences(paragraph):
      sentence_tokens = _tokenize(sentence)
      if not sentence_tokens:
        continue

      if len(sentence_tokens) > max_tokens:
        flush_chunk()
        step = max(1, max_tokens - overlap_tokens)
        start = 0
        while start < len(sentence_tokens):
          end = min(start + max_tokens, len(sentence_tokens))
          piece = sentence_tokens[start:end]
          if piece:
            chunks.append(TextChunk(index=len(chunks), text=" ".join(piece).strip()))
          if end >= len(sentence_tokens):
            break
          start += step
        continue

      if len(current_tokens) + len(sentence_tokens) > max_tokens:
        flush_chunk()

      current_tokens.extend(sentence_tokens)

  flush_chunk()
  return [chunk for chunk in chunks if chunk.text]


def _translate_chunks_to_english(chunks: list[TextChunk], source_lang: str) -> list[str]:
  if not chunks:
    return []

  deep_translator_module = import_module("deep_translator")
  google_translator = getattr(deep_translator_module, "GoogleTranslator")
  source = "fr" if source_lang.startswith("fr") else "auto"
  translator = google_translator(source=source, target="en")

  translated: list[str] = []
  for chunk in chunks:
    try:
      translated_text = translator.translate(chunk.text)
      translated.append(str(translated_text) if translated_text is not None else chunk.text)
    except Exception:
      translated.append(chunk.text)
  return translated


def _score_chunk_for_task(chunk: TextChunk, task_name: str) -> int:
  normalized = _normalize_for_matching(chunk.text)
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


def _select_relevant_chunks(chunks: list[TextChunk], task_name: str, top_n: int) -> list[TextChunk]:
  scored = [(chunk, _score_chunk_for_task(chunk, task_name)) for chunk in chunks]
  scored.sort(key=lambda item: (item[1], -item[0].index), reverse=True)
  selected = [item[0] for item in scored[:top_n] if item[1] > 0]
  if selected:
    return selected
  return chunks[:top_n]


def _parse_date_to_iso(raw_date: str) -> str | None:
  cleaned = _normalize_for_matching(raw_date)
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


def _extract_deadline_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  pattern = re.compile(
    r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:er)?\s+[a-zA-Zéèêëàâîïôöùûüç]+\s+\d{4})",
    re.IGNORECASE,
  )
  candidates: list[Candidate] = []
  for chunk in chunks:
    normalized = _normalize_for_matching(chunk.text)
    for match in pattern.finditer(normalized):
      parsed = _parse_date_to_iso(match.group(1))
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


def _normalize_amount(amount_token: str) -> str:
  compact = re.sub(r"\s+", "", amount_token)
  if "," in compact and "." in compact:
    return compact.replace(".", "").replace(",", ".")
  if "," in compact:
    return compact.replace(",", ".")
  return compact


def _normalize_currency_unit(currency_token: str) -> str:
  normalized = _normalize_for_matching(currency_token)
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
  }
  return currency_map.get(normalized, currency_token.upper())


def _normalize_budget_value(value: str) -> str:
  normalized = _normalize_for_matching(value)
  pattern = re.compile(
    r"(?P<amount>\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*"
    r"(?P<cur>€|eur|euro|euros|usd|\$|mad|dzd|xof|xaf|tnd|dt|cad|chf|gbp|da|dh)",
    re.IGNORECASE,
  )
  match = pattern.search(normalized)
  if not match:
    return ""
  amount = _normalize_amount(match.group("amount"))
  currency = _normalize_currency_unit(match.group("cur"))
  return f"{amount} {currency}"


def _has_budget_unit(value: str) -> bool:
  normalized = _normalize_for_matching(value)
  return bool(
    re.search(r"\b(?:eur|usd|mad|dzd|dt|xof|xaf|cad|chf|gbp)\b", normalized)
    or "€" in value
    or "$" in value
  )


def _extract_budget_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  pattern = re.compile(
    r"(?P<amount>\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*"
    r"(?P<mult>k|m|mn|mille|million|millions|md|milliard|milliards)?\s*"
    r"(?P<cur>€|eur|euro|euros|usd|\$|mad|dzd|xof|xaf|tnd|dt|cad|chf|gbp|da|dh)",
    re.IGNORECASE,
  )
  candidates: list[Candidate] = []
  for chunk in chunks:
    normalized = _normalize_for_matching(chunk.text)
    for match in pattern.finditer(normalized):
      amount = _normalize_amount(match.group("amount"))
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
        amount_normalized = str(int(numeric)) if numeric.is_integer() else f"{numeric:.2f}"
      except Exception:
        amount_normalized = amount
      value = f"{amount_normalized} {_normalize_currency_unit(match.group('cur'))}"
      left = normalized[max(0, match.start() - 100):match.start()]
      score = 0.62
      if any(keyword in left for keyword in TASK_KEYWORDS["budget"]):
        score = 0.9
      candidates.append(
        Candidate(
          value=value,
          score=score,
          evidence_text=chunk.text[:500],
          source_chunk_index=chunk.index,
          metadata_source="rules",
        )
      )
  return candidates


def _extract_country_candidates(chunks: list[TextChunk]) -> list[Candidate]:
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
    normalized = _normalize_for_matching(chunk.text)
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


def _category_from_text(text: str) -> tuple[str, float]:
  normalized = _normalize_for_matching(text)
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


def _extract_category_candidates(chunks: list[TextChunk]) -> list[Candidate]:
  candidates: list[Candidate] = []
  for chunk in chunks:
    category, confidence = _category_from_text(chunk.text)
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


def _dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
  seen: set[str] = set()
  ordered: list[Candidate] = []
  for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
    key = candidate.value
    if key in seen:
      continue
    seen.add(key)
    ordered.append(candidate)
  return ordered


def _is_ambiguous(candidates: list[Candidate]) -> bool:
  if len(candidates) < 2:
    return False
  sorted_candidates = sorted(candidates, key=lambda item: item.score, reverse=True)
  return abs(sorted_candidates[0].score - sorted_candidates[1].score) <= 0.06


def _extract_json_object(raw_text: str) -> dict[str, object] | None:
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


def _resolve_with_hf(task_name: str, relevant_chunks: list[TextChunk], candidates: list[Candidate]) -> Candidate | None:
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
    parsed = _extract_json_object(content)
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
      parsed_date = _parse_date_to_iso(value)
      value = parsed_date if parsed_date else value
    if task_name == "budget":
      value = _normalize_budget_value(value)

    return Candidate(
      value=value,
      score=max(0.0, min(1.0, confidence)),
      evidence_text=evidence_text[:500],
      source_chunk_index=source_chunk_index,
      metadata_source="hf_llm",
    )
  except Exception:
    return None


def _metadata_item(value: str | None, confidence: float, evidence_text: str, source_chunk_index: int | None, metadata_source: str) -> dict[str, object]:
  return {
    "value": value,
    "confidence": round(max(0.0, min(1.0, confidence)), 4),
    "evidence_text": evidence_text,
    "source_chunk_index": source_chunk_index,
    "metadata_source": metadata_source,
  }


def _resolve_task(task_name: str, relevant_chunks: list[TextChunk], all_chunks: list[TextChunk]) -> dict[str, object]:
  extractor_map = {
    "deadline": _extract_deadline_candidates,
    "budget": _extract_budget_candidates,
    "country": _extract_country_candidates,
    "category": _extract_category_candidates,
  }
  extractor = extractor_map[task_name]
  candidates = _dedupe_candidates(extractor(relevant_chunks))

  if not candidates:
    fallback_candidates = _dedupe_candidates(extractor(all_chunks))
    if not fallback_candidates:
      return _metadata_item(None, 0.0, "", None, "rules_fallback")
    best_fallback = fallback_candidates[0]
    if task_name == "budget":
      fallback_value = _normalize_budget_value(best_fallback.value)
      if not fallback_value:
        return _metadata_item(None, 0.0, "", None, "rules_fallback")
      return _metadata_item(
        fallback_value,
        best_fallback.score,
        best_fallback.evidence_text,
        best_fallback.source_chunk_index,
        "rules_fallback",
      )
    return _metadata_item(
      best_fallback.value,
      best_fallback.score,
      best_fallback.evidence_text,
      best_fallback.source_chunk_index,
      "rules_fallback",
    )

  if _is_ambiguous(candidates):
    llm_choice = _resolve_with_hf(task_name, relevant_chunks, candidates)
    if llm_choice is not None:
      if task_name == "budget":
        llm_value = _normalize_budget_value(llm_choice.value)
        if llm_value:
          return _metadata_item(
            llm_value,
            llm_choice.score,
            llm_choice.evidence_text,
            llm_choice.source_chunk_index,
            llm_choice.metadata_source,
          )
      else:
        return _metadata_item(
          llm_choice.value,
          llm_choice.score,
          llm_choice.evidence_text,
          llm_choice.source_chunk_index,
          llm_choice.metadata_source,
        )

  if task_name == "budget":
    budget_candidates = [candidate for candidate in candidates if _has_budget_unit(candidate.value)]
    if budget_candidates:
      best_budget = budget_candidates[0]
      best_budget_value = _normalize_budget_value(best_budget.value)
      if best_budget_value:
        return _metadata_item(
          best_budget_value,
          best_budget.score,
          best_budget.evidence_text,
          best_budget.source_chunk_index,
          best_budget.metadata_source,
        )

    fallback_budget_candidates = _dedupe_candidates(_extract_budget_candidates(all_chunks))
    if fallback_budget_candidates:
      fallback_budget = fallback_budget_candidates[0]
      fallback_budget_value = _normalize_budget_value(fallback_budget.value)
      if fallback_budget_value:
        return _metadata_item(
          fallback_budget_value,
          fallback_budget.score,
          fallback_budget.evidence_text,
          fallback_budget.source_chunk_index,
          "rules_fallback",
        )
    return _metadata_item(None, 0.0, "", None, "rules_fallback")

  best = candidates[0]
  return _metadata_item(best.value, best.score, best.evidence_text, best.source_chunk_index, best.metadata_source)


def _build_metadata(chunks: list[TextChunk], language: str, confidence: float) -> dict[str, object]:
  deadline_chunks = _select_relevant_chunks(chunks, "deadline", METADATA_TOP_CHUNKS)
  budget_chunks = _select_relevant_chunks(chunks, "budget", METADATA_TOP_CHUNKS)
  country_chunks = _select_relevant_chunks(chunks, "country", METADATA_TOP_CHUNKS)
  category_chunks = _select_relevant_chunks(chunks, "category", METADATA_TOP_CHUNKS)

  return {
    "language": {
      "value": language,
      "confidence": round(confidence, 4),
      "metadata_source": "langdetect",
    },
    "deadline": _resolve_task("deadline", deadline_chunks, chunks),
    "budget": _resolve_task("budget", budget_chunks, chunks),
    "country": _resolve_task("country", country_chunks, chunks),
    "category": _resolve_task("category", category_chunks, chunks),
  }


def process_ocr_complete(event_payload: dict[str, Any]) -> None:
  payload = event_payload.get("payload", event_payload)
  document_id = str(payload.get("document_id", ""))
  tenant_id = str(payload.get("tenant_id", DEFAULT_TENANT_ID))
  filename = str(payload.get("filename", "uploaded-file"))
  ocr_text = str(payload.get("ocr_text", ""))

  if not document_id:
    raise RuntimeError("ocr_complete event missing document_id")

  cleaned_text = _clean_text_preserve_structure(ocr_text)
  language, lang_confidence = _detect_language(cleaned_text)
  paragraphs = _split_paragraphs(cleaned_text)
  chunks = _build_chunks(paragraphs, MAX_CHUNK_TOKENS, CHUNK_OVERLAP_TOKENS)
  translated_chunks = _translate_chunks_to_english(chunks, language)
  metadata = _build_metadata(chunks, language, lang_confidence)

  chunk_texts = [chunk.text for chunk in chunks]
  document_repository.replace_document_chunks(document_id, chunk_texts, translated_chunks)
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
