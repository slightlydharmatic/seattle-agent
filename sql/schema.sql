-- Seattle Unlocked: what the team's work is saved in.
-- Run once: Supabase dashboard > SQL editor > New query > paste all of this > Run.
--
-- Row level security is ON with no policies, so the public API can't read or write
-- these tables. Only the service key (kept in Streamlit and GitHub secrets, never
-- in the browser or in git) can.

-- Thumbs up / down on events. Overrides the AI, teaches it, and measures it.
create table if not exists feedback (
  event_key text primary key,
  vote smallint not null check (vote in (-1, 1)),
  note text default '',
  title text, description text, venue text, neighborhood text, cost text, category text, source text,
  model_score smallint, model_intent text,
  created_at timestamptz default now()
);
alter table feedback enable row level security;

-- Team settings that must survive app restarts: filter rules, allowed events,
-- the AI operating point (all under "filters"), and hand-added events ("custom_events").
create table if not exists app_settings (
  name text primary key,
  value jsonb not null,
  updated_at timestamptz default now()
);
alter table app_settings enable row level security;

create or replace function touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
drop trigger if exists app_settings_touch on app_settings;
create trigger app_settings_touch before update on app_settings
  for each row execute function touch_updated_at();
