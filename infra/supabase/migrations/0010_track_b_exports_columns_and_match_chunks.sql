alter table if exists exports
  add column if not exists status text default 'processing';

alter table if exists exports
  add column if not exists tenant_id uuid references tenants(id);

create index if not exists exports_tenant_id_idx on exports(tenant_id);
create index if not exists exports_document_id_idx on exports(document_id);

create or replace function match_chunks(
  query_document_id uuid,
  query_embedding vector,
  match_count int default 5
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  content_translated text,
  "position" int,
  page_number int,
  similarity double precision
)
language sql
stable
as $$
  select
    c.id,
    c.document_id,
    c.content,
    c.content_translated,
    c.position as "position",
    c.page_number,
    1 - (c.embedding <=> query_embedding) as similarity
  from chunks c
  where c.document_id = query_document_id
    and c.embedding is not null
  order by c.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;
