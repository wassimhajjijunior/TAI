from importlib import import_module

from .models import TextChunk


def detect_language(text: str) -> tuple[str, float]:
  if not text:
    return "unknown", 0.0

  langdetect_module = import_module("langdetect")
  detect_langs = getattr(langdetect_module, "detect_langs")
  detections = detect_langs(text[:5000])
  if not detections:
    return "unknown", 0.0
  top = detections[0]
  return str(getattr(top, "lang", "unknown")), float(getattr(top, "prob", 0.0))


def _normalize_text_for_sentence_chunking(text: str) -> str:
  normalized = text.replace("\r\n", "\n").replace("\r", "\n")
  lines = [line.strip() for line in normalized.split("\n")]
  compact_lines = [line for line in lines if line]
  return "\n".join(compact_lines)


def _fallback_sentence_chunks(text: str, max_characters: int) -> list[str]:
  import re

  if not text.strip():
    return []

  sentences = [segment.strip() for segment in re.split(r"(?<=[.!?;:])\s+", text) if segment.strip()]
  if not sentences:
    return [text.strip()]

  chunks: list[str] = []
  buffer = ""
  for sentence in sentences:
    if not buffer:
      buffer = sentence
      continue
    candidate = f"{buffer} {sentence}".strip()
    if len(candidate) <= max_characters:
      buffer = candidate
    else:
      chunks.append(buffer)
      buffer = sentence

  if buffer:
    chunks.append(buffer)
  return chunks


def build_chonkie_chunks(text: str, max_tokens: int) -> list[TextChunk]:
  if max_tokens <= 0:
    return []

  normalized_text = _normalize_text_for_sentence_chunking(text)
  if not normalized_text:
    return []

  sentence_chunks: list[str] = []
  try:
    chonkie_module = import_module("chonkie")
    sentence_chunker_class = getattr(chonkie_module, "SentenceChunker")
    chunker = sentence_chunker_class(
      chunk_size=max_tokens,
      chunk_overlap=0,
      min_sentences_per_chunk=1,
    )
    raw_chunks = chunker.chunk(normalized_text)

    for chunk in raw_chunks:
      if isinstance(chunk, str):
        chunk_text = chunk.strip()
      else:
        text_attr = getattr(chunk, "text", "")
        chunk_text = str(text_attr).strip()
      if chunk_text:
        sentence_chunks.append(chunk_text)
  except Exception:
    sentence_chunks = _fallback_sentence_chunks(normalized_text, max_characters=max_tokens * 6)

  return [
    TextChunk(index=index, text=chunk_text, structure_type="sentence", source_block_index=index)
    for index, chunk_text in enumerate(sentence_chunks)
    if chunk_text
  ]
