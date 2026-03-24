alter table if exists documents
  add column if not exists size_bytes bigint not null default 0,
  add column if not exists content_type text not null default 'application/octet-stream';
