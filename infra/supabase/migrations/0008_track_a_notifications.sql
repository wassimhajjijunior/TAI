create table if not exists notifications (
  id uuid primary key,
  document_id uuid not null references documents(id),
  tenant_id uuid not null references tenants(id),
  recipient_email text not null,
  template_name text not null,
  channel text not null,
  status text not null,
  subject text not null,
  payload jsonb,
  created_at timestamptz default now()
);

create index if not exists notifications_document_id_idx on notifications(document_id);
create index if not exists notifications_tenant_id_idx on notifications(tenant_id);
