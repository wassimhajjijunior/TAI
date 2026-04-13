alter table if exists chunks
  alter column metadata set default '{}'::jsonb;

update chunks
set metadata = '{}'::jsonb
where metadata is null;

alter table if exists chunks
  alter column metadata set not null;
