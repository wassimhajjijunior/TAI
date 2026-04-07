import re
from dataclasses import dataclass
from importlib import import_module

from .models import TextChunk
from .text_utils import tokenize


@dataclass(frozen=True)
class TextBlock:
  block_type: str
  text: str
  source_index: int


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


def segment_sentences(paragraph_text: str) -> list[str]:
  try:
    spacy_module = import_module("spacy")
    nlp = getattr(spacy_module, "blank")("fr")
    if "sentencizer" not in nlp.pipe_names:
      nlp.add_pipe("sentencizer")
    doc = nlp(paragraph_text)
    sentences = [str(sentence.text).strip() for sentence in doc.sents if str(sentence.text).strip()]
    if sentences:
      return sentences
  except Exception:
    pass

  fallback = [item.strip() for item in re.split(r"(?<=[.!?;:])\s+", paragraph_text) if item.strip()]
  return fallback if fallback else [paragraph_text]


def _is_heading(line: str) -> bool:
  if not line:
    return False
  normalized = line.strip()
  if normalized.startswith("#"):
    return True
  if re.match(r"^(?:\d+(?:\.\d+)*)[\).\-:]\s+", normalized):
    return True
  words = normalized.split()
  if len(words) <= 10 and normalized == normalized.upper() and any(char.isalpha() for char in normalized):
    return True
  return False


def _is_table_line(line: str) -> bool:
  normalized = line.strip()
  if not normalized:
    return False
  if normalized.count("|") >= 2:
    return True
  if re.match(r"^\s*\+[-+]+\+\s*$", normalized):
    return True
  return False


def _is_list_item(line: str) -> bool:
  normalized = line.strip()
  return bool(re.match(r"^(?:[-*•]|\d+[\).])\s+", normalized))


def split_structural_blocks(text: str) -> list[TextBlock]:
  lines = [line.rstrip() for line in text.split("\n")]
  blocks: list[TextBlock] = []
  current_lines: list[str] = []
  current_type = "paragraph"

  def flush_block() -> None:
    nonlocal current_lines, current_type
    content = "\n".join(line for line in current_lines if line.strip()).strip()
    if content:
      blocks.append(TextBlock(block_type=current_type, text=content, source_index=len(blocks)))
    current_lines = []
    current_type = "paragraph"

  for raw_line in lines:
    line = raw_line.strip()
    if not line:
      flush_block()
      continue

    line_type = "paragraph"
    if _is_heading(line):
      line_type = "heading"
    elif _is_table_line(line):
      line_type = "table"
    elif _is_list_item(line):
      line_type = "list"

    if current_lines and line_type != current_type:
      flush_block()

    if not current_lines:
      current_type = line_type
    current_lines.append(raw_line)

  flush_block()
  return blocks


def _split_table_block(block: TextBlock, max_rows_per_chunk: int) -> list[TextBlock]:
  rows = [line for line in block.text.split("\n") if line.strip()]
  if len(rows) <= max_rows_per_chunk:
    return [block]

  header_rows: list[str] = []
  body_rows = rows
  if len(rows) >= 2 and "|" in rows[0] and re.search(r"^\s*\|?\s*[:\- ]+\|", rows[1]):
    header_rows = rows[:2]
    body_rows = rows[2:]

  parts: list[TextBlock] = []
  effective_rows = max(1, max_rows_per_chunk - len(header_rows)) if header_rows else max(1, max_rows_per_chunk)
  for start in range(0, len(body_rows), effective_rows):
    chunk_rows = body_rows[start:start + effective_rows]
    full_rows = header_rows + chunk_rows if header_rows else chunk_rows
    piece = "\n".join(full_rows).strip()
    if piece:
      parts.append(TextBlock(block_type="table", text=piece, source_index=block.source_index))
  return parts


def segment_sentences_by_structure(block: TextBlock) -> list[str]:
  if block.block_type == "table":
    return [line.strip() for line in block.text.split("\n") if line.strip()]
  if block.block_type in {"heading", "list"}:
    lines = [line.strip() for line in block.text.split("\n") if line.strip()]
    if lines:
      return lines
  return segment_sentences(block.text)


def _token_set(text: str) -> set[str]:
  return {token.lower() for token in tokenize(text) if token.strip()}


def _jaccard_similarity(a: str, b: str) -> float:
  a_tokens = _token_set(a)
  b_tokens = _token_set(b)
  if not a_tokens or not b_tokens:
    return 1.0
  intersection = len(a_tokens & b_tokens)
  union = len(a_tokens | b_tokens)
  return intersection / union if union else 1.0


def _append_chunk(
  chunks: list[TextChunk],
  token_buffer: list[str],
  block_type: str,
  source_block_index: int,
) -> None:
  text = " ".join(token_buffer).strip()
  if not text:
    return
  chunks.append(
    TextChunk(
      index=len(chunks),
      text=text,
      structure_type=block_type,
      source_block_index=source_block_index,
    )
  )


def _enforce_chunk_budget(
  chunks: list[TextChunk],
  max_tokens: int,
  overlap_tokens: int,
) -> list[TextChunk]:
  safe_overlap = max(0, min(overlap_tokens, max_tokens - 1)) if max_tokens > 1 else 0
  normalized: list[TextChunk] = []

  def append_table_with_header(chunk: TextChunk) -> bool:
    rows = [line.strip() for line in chunk.text.split("\n") if line.strip()]
    if len(rows) < 3:
      return False
    if not ("|" in rows[0] and re.search(r"^\s*\|?\s*[:\- ]+\|", rows[1])):
      return False

    header_rows = rows[:2]
    body_rows = rows[2:]
    if not body_rows:
      return False

    current_body: list[str] = []
    for row in body_rows:
      candidate_rows = header_rows + current_body + [row]
      candidate_text = "\n".join(candidate_rows)
      if len(tokenize(candidate_text)) <= max_tokens:
        current_body.append(row)
        continue

      if current_body:
        piece = "\n".join(header_rows + current_body)
        normalized.append(
          TextChunk(
            index=len(normalized),
            text=piece,
            structure_type=chunk.structure_type,
            source_block_index=chunk.source_block_index,
          )
        )
        current_body = [row]
      else:
        return False

    if current_body:
      piece = "\n".join(header_rows + current_body)
      normalized.append(
        TextChunk(
          index=len(normalized),
          text=piece,
          structure_type=chunk.structure_type,
          source_block_index=chunk.source_block_index,
        )
      )
    return True

  for chunk in chunks:
    tokens = tokenize(chunk.text)
    if len(tokens) <= max_tokens:
      normalized.append(
        TextChunk(
          index=len(normalized),
          text=chunk.text,
          structure_type=chunk.structure_type,
          source_block_index=chunk.source_block_index,
        )
      )
      continue

    if chunk.structure_type == "table" and append_table_with_header(chunk):
      continue

    step = max(1, max_tokens - safe_overlap)
    start = 0
    while start < len(tokens):
      end = min(start + max_tokens, len(tokens))
      piece = tokens[start:end]
      if piece:
        normalized.append(
          TextChunk(
            index=len(normalized),
            text=" ".join(piece).strip(),
            structure_type=chunk.structure_type,
            source_block_index=chunk.source_block_index,
          )
        )
      if end >= len(tokens):
        break
      start += step

  return normalized


def build_hybrid_chunks(
  text: str,
  max_tokens: int,
  overlap_tokens: int,
  semantic_min_tokens: int,
  semantic_similarity_threshold: float,
  table_max_rows_per_chunk: int,
) -> list[TextChunk]:
  if max_tokens <= 0:
    return []
  safe_overlap = max(0, min(overlap_tokens, max_tokens - 1)) if max_tokens > 1 else 0
  semantic_enabled = semantic_min_tokens < max_tokens

  structural_blocks = split_structural_blocks(text)
  normalized_blocks: list[TextBlock] = []
  for block in structural_blocks:
    if block.block_type == "table":
      normalized_blocks.extend(_split_table_block(block, table_max_rows_per_chunk))
    else:
      normalized_blocks.append(block)

  chunks: list[TextChunk] = []
  token_buffer: list[str] = []
  buffer_structure_type = "paragraph"
  buffer_block_index = 0
  previous_sentence = ""

  def flush_with_overlap(keep_overlap: bool) -> None:
    nonlocal token_buffer
    if not token_buffer:
      return
    _append_chunk(chunks, token_buffer, buffer_structure_type, buffer_block_index)
    token_buffer = token_buffer[-safe_overlap:] if keep_overlap and safe_overlap > 0 else []

  for block in normalized_blocks:
    sentences = segment_sentences_by_structure(block)
    if not sentences:
      continue

    for sentence in sentences:
      sentence_tokens = tokenize(sentence)
      if not sentence_tokens:
        continue

      if not token_buffer:
        buffer_structure_type = block.block_type
        buffer_block_index = block.source_index

      force_boundary = False
      if token_buffer and (block.block_type != buffer_structure_type or block.source_index != buffer_block_index):
        force_boundary = True
      elif semantic_enabled and token_buffer and len(token_buffer) >= semantic_min_tokens and previous_sentence:
        similarity = _jaccard_similarity(previous_sentence, sentence)
        if similarity < semantic_similarity_threshold:
          force_boundary = True

      if force_boundary:
        keep_overlap: bool = block.block_type == buffer_structure_type and block.source_index == buffer_block_index
        flush_with_overlap(keep_overlap=keep_overlap)
        buffer_structure_type = block.block_type
        buffer_block_index = block.source_index

      if len(sentence_tokens) > max_tokens:
        flush_with_overlap(keep_overlap=False)
        step = max(1, max_tokens - safe_overlap)
        start = 0
        while start < len(sentence_tokens):
          end = min(start + max_tokens, len(sentence_tokens))
          piece = sentence_tokens[start:end]
          if piece:
            _append_chunk(chunks, piece, block.block_type, block.source_index)
          if end >= len(sentence_tokens):
            break
          start += step
        token_buffer = []
        previous_sentence = sentence
        continue

      if len(token_buffer) + len(sentence_tokens) > max_tokens:
        flush_with_overlap(keep_overlap=True)
        if not token_buffer:
          buffer_structure_type = block.block_type
          buffer_block_index = block.source_index

      token_buffer.extend(sentence_tokens)
      previous_sentence = sentence

  flush_with_overlap(keep_overlap=False)
  cleaned = [chunk for chunk in chunks if chunk.text]
  return _enforce_chunk_budget(cleaned, max_tokens, safe_overlap)
