from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
  index: int
  text: str
  structure_type: str = "paragraph"
  source_block_index: int = 0


@dataclass(frozen=True)
class Candidate:
  value: str
  score: float
  evidence_text: str
  source_chunk_index: int
  metadata_source: str
