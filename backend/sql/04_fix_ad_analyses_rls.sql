-- Fix RLS policies to allow backend service role to insert/update ad_analyses records
-- This allows the FastAPI backend (using service role key) to save agent_results

-- Add policies for service role to insert and update
drop policy if exists "Service role can insert ad_analyses" on public.ad_analyses;
drop policy if exists "Service role can update ad_analyses" on public.ad_analyses;

-- Allow service role to insert records
-- Service role is identified by having no auth.uid() but having elevated permissions
create policy "Service role can insert ad_analyses"
  on public.ad_analyses for insert
  to service_role
  with check (true);

-- Allow service role to update records
create policy "Service role can update ad_analyses"
  on public.ad_analyses for update
  to service_role
  using (true);

-- Optional: Also allow authenticated users to update their own records
-- (This policy already exists from 03_ad_analyses.sql but including for completeness)
create policy "Authenticated users can update their analyses"
  on public.ad_analyses for update
  to authenticated
  using (auth.uid() = user_id);
