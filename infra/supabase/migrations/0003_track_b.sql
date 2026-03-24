create table if not exists responses (
  id uuid primary key,
  document_id uuid not null references documents(id),
  content text not null,
  citations jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists exports (
  id uuid primary key,
  document_id uuid not null references documents(id),
  response_id uuid not null references responses(id),
  format text not null,
  file_path text not null,
  created_at timestamptz default now()
);
