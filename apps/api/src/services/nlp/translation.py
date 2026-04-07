from importlib import import_module

from .models import TextChunk


def translate_chunks_to_english(chunks: list[TextChunk], source_lang: str) -> list[str]:
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
