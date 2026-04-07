DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
MAX_CHUNK_TOKENS = 300
CHUNK_OVERLAP_TOKENS = 50
SEMANTIC_MIN_TOKENS = 120
SEMANTIC_SIMILARITY_THRESHOLD = 0.18
TABLE_MAX_ROWS_PER_CHUNK = 12
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
