create extension if not exists vector;

create table if not exists tenants (
  id uuid primary key,
  name text not null,
  created_at timestamptz default now()
);

create table if not exists users (
  id uuid primary key,
  tenant_id uuid not null references tenants(id),
  email text not null unique,
  created_at timestamptz default now()
);
