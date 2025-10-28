-- Table for storing per-user ad analyses (input and output payloads)
-- Ensure gen_random_uuid() is available
create extension if not exists pgcrypto;

create table if not exists public.ad_analyses (
  id uuid primary key default gen_random_uuid(),
  created_at timestamp with time zone not null default now(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  title text,
  input jsonb not null,
  output jsonb,
  feature_output jsonb,
  brandmeta_output jsonb,
  agent_results jsonb
);

alter table public.ad_analyses enable row level security;

-- Ensure new columns exist when re-running
alter table public.ad_analyses add column if not exists feature_output jsonb;
alter table public.ad_analyses add column if not exists brandmeta_output jsonb;
alter table public.ad_analyses add column if not exists agent_results jsonb;

-- Re-create policies idempotently
drop policy if exists "Users can select their analyses" on public.ad_analyses;
drop policy if exists "Users can insert their analyses" on public.ad_analyses;
drop policy if exists "Users can update their analyses" on public.ad_analyses;

create policy "Users can select their analyses"
  on public.ad_analyses for select
  using (auth.uid() = user_id);

create policy "Users can insert their analyses"
  on public.ad_analyses for insert
  with check (auth.uid() = user_id);

create policy "Users can update their analyses"
  on public.ad_analyses for update
  using (auth.uid() = user_id);


