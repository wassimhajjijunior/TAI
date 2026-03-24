create table if not exists documents (
  id uuid primary key,
  tenant_id uuid not null references tenants(id),
  filename text not null,
  status text not null,
  created_at timestamptz default now()
);

create table if not exists chunks (
  id uuid primary key,
  document_id uuid not null references documents(id),
  content text not null,
  content_translated text,
  embedding vector(1536),
  position int not null,
  page_number int,
  created_at timestamptz default now()
);

create table if not exists requirements (
  id uuid primary key,
  document_id uuid not null references documents(id),
  requirement_text text not null,
  created_at timestamptz default now()
);

create table if not exists compliance_reports (
  id uuid primary key,
  document_id uuid not null references documents(id),
  score numeric,
  report jsonb,
  created_at timestamptz default now()
);

create table if not exists company_profiles (
  id uuid primary key,
  tenant_id uuid not null references tenants(id),
  profile jsonb not null,
  created_at timestamptz default now()
);

create table if not exists annexes (
  id uuid primary key,
  tenant_id uuid not null references tenants(id),
  name text not null,
  storage_path text not null,
  created_at timestamptz default now()
);
