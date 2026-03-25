alter table if exists documents
  add column if not exists chunk_count integer not null default 0,
  add column if not exists metadata jsonb;
