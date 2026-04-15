-- Add performance indexes for frequently queried columns
-- Addresses REVIEW_REPORT.md issue #7

-- Tenant-scoped indexes
CREATE INDEX IF NOT EXISTS documents_tenant_id_idx ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS annexes_tenant_id_idx ON annexes(tenant_id);
CREATE INDEX IF NOT EXISTS company_profiles_tenant_id_idx ON company_profiles(tenant_id);

-- Document-scoped indexes for foreign key lookups
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);
CREATE INDEX IF NOT EXISTS requirements_document_id_idx ON requirements(document_id);
CREATE INDEX IF NOT EXISTS responses_document_id_idx ON responses(document_id);
CREATE INDEX IF NOT EXISTS exports_document_id_idx ON exports(document_id);

-- Vector index for embedding similarity search
-- Uses HNSW with cosine distance operator (vector_cosine_ops)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);

-- Add tenant_id to compliance_reports for proper tenant isolation
-- Addresses REVIEW_REPORT.md issue #29
ALTER TABLE compliance_reports ADD COLUMN IF NOT EXISTS tenant_id uuid;

-- Backfill tenant_id from documents table
UPDATE compliance_reports cr
SET tenant_id = d.tenant_id
FROM documents d
WHERE cr.document_id = d.id AND cr.tenant_id IS NULL;

-- Add foreign key constraint for tenant_id
ALTER TABLE compliance_reports
ADD CONSTRAINT fk_compliance_reports_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id)
ON DELETE CASCADE;

-- Add index for compliance_reports tenant queries
CREATE INDEX IF NOT EXISTS compliance_reports_tenant_id_idx ON compliance_reports(tenant_id);
