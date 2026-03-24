# API Endpoint Ownership

## Track A

- POST `/api/v1/documents`
- GET `/api/v1/documents`
- GET `/api/v1/documents/{id}`
- GET `/api/v1/documents/{id}/status`
- GET `/api/v1/documents/{id}/requirements`
- GET `/api/v1/documents/{id}/compliance`
- GET/PUT `/api/v1/company/profile`
- GET/POST `/api/v1/company/annexes`

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
