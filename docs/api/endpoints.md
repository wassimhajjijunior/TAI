# API Endpoint Ownership

## Track A

- POST `/api/v1/documents`
- GET `/api/v1/documents`
- GET `/api/v1/documents/{id}`
- GET `/api/v1/documents/{id}/status`
- GET `/api/v1/documents/{id}/requirements`
- GET `/api/v1/documents/{id}/compliance`
- GET `/api/v1/system/messaging`
- GET/PUT `/api/v1/company/profile`
- GET/POST `/api/v1/company/annexes`

### POST `/api/v1/documents` (current first-step implementation)

- Content-Type: `multipart/form-data`
- Field: `file`
- Accepted MIME types: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`
- Max file size: `20 MB`
- Response: `{ document: UploadedDocument }`
- Side effect: publishes RabbitMQ event `document_uploaded`

### GET `/api/v1/system/messaging`

- Response includes:
  - RabbitMQ connectivity (`connected`, `detail`)
  - Topology metadata (`exchange`, `exchange_type`, queue names)
  - Pipeline flow events in order (`document_uploaded` → `ocr_complete` → `nlp_completed` → `embedding_complete`)

## Track B

- POST `/api/v1/rag/query`
- POST `/api/v1/generate/response`
- GET `/api/v1/responses/{id}`
- PATCH `/api/v1/responses/{id}`
- POST `/api/v1/documents/{id}/export`
- GET `/api/v1/exports/{id}/download`

## Shared Payload Contracts

The payload contracts are centralized in `packages/shared-types/src/index.ts`.

### POST `/api/v1/rag/query`

- Request: `RagQueryRequest`
- Response: `RagQueryResponse`

### POST `/api/v1/generate/response`

- Request: `GenerateResponseRequest`
- Response: `ResponseRecord`

### GET `/api/v1/responses/{id}`

- Response: `ResponseRecord`

### PATCH `/api/v1/responses/{id}`

- Request: `UpdateResponseRequest`
- Response: `ResponseRecord`

### POST `/api/v1/documents/{id}/export`

- Request: `ExportRequest`
- Response: `ExportRecord`

### GET `/api/v1/exports/{id}/download`

- Response: `ExportRecord`

## Event-Driven Pipeline (Track A)

The ingestion flow is event-driven through RabbitMQ:

`document_uploaded` → `ocr_complete` → `nlp_completed` → `embedding_complete`

- Exchange: `p2m.events` (topic, durable)
- Queues:
  - `track_a.ocr.queue`
  - `track_a.nlp.queue`
  - `track_a.embedding.queue`
  - `track_a.compliance.queue`
