import re
import unicodedata


def strip_diacritics(value: str) -> str:
  normalized = unicodedata.normalize("NFD", value)
  return "".join(character for character in normalized if unicodedata.category(character) != "Mn")


def normalize_for_matching(value: str) -> str:
  lowered = value.lower()
  without_diacritics = strip_diacritics(lowered)
  return re.sub(r"\s+", " ", without_diacritics).strip()


def clean_text_preserve_structure(raw_text: str) -> str:
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


def split_paragraphs(text: str) -> list[str]:
  if not text:
    return []
  parts = re.split(r"\n\s*\n+", text)
  return [part.strip() for part in parts if part.strip()]


def tokenize(text: str) -> list[str]:
  return [token for token in text.split(" ") if token]
