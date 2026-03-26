alter table if exists requirements
  add column if not exists requirement_code text,
  add column if not exists category text,
  add column if not exists weight numeric,
  add column if not exists met boolean,
  add column if not exists confidence numeric,
  add column if not exists actual_value text;

alter table if exists compliance_reports
  add column if not exists eligibility_score numeric,
  add column if not exists recommendation text;

create unique index if not exists compliance_reports_document_id_unique_idx
  on compliance_reports(document_id);

create unique index if not exists company_profiles_tenant_id_unique_idx
  on company_profiles(tenant_id);
