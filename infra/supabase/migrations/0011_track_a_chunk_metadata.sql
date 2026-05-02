alter table if exists chunks
  add column if not exists metadata jsonb;
