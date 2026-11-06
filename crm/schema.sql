-- Run once in Supabase: SQL editor > New query > paste > Run.
-- Row level security is ON with no public policies, so only the service key
-- (kept in Streamlit and GitHub secrets, never in the browser) can read or write.

create table if not exists clients (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique,
  company text default '',
  client_type text not null default 'Unsorted',
  created_at timestamptz default now()
);

create table if not exists deals (
  id uuid primary key default gen_random_uuid(),
  client_id uuid references clients(id) on delete cascade,
  title text not null default 'New inquiry',
  stage text not null default 'Unconfirmed deal',
  notes text default '',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists emails (
  id uuid primary key default gen_random_uuid(),
  client_id uuid references clients(id) on delete cascade,
  gmail_id text unique,
  subject text default '',
  received_at timestamptz,
  snippet text default '',
  created_at timestamptz default now()
);

alter table clients enable row level security;
alter table deals enable row level security;
alter table emails enable row level security;

-- Event feedback (thumbs up / down) for the AI curator.
create table if not exists feedback (
  event_key text primary key,
  vote smallint not null check (vote in (-1, 1)),
  note text default '',
  title text, description text, venue text, neighborhood text, cost text, category text, source text,
  model_score smallint, model_intent text,
  created_at timestamptz default now()
);
alter table feedback enable row level security;
