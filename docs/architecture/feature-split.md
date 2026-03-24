# Feature Split Architecture

## Track A

- Document upload and storage
- OCR and NLP processing
- Requirements extraction
- Compliance scoring and matrix

## Track B

- RAG retrieval from processed chunks
- Response generation with LLM
- Editor and citation workflow
- Export and download pipeline

## Shared Integration Contract

- Producer: Track A writes to `chunks`
- Consumer: Track B queries `chunks` through `/api/v1/rag/query`
