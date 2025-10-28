# Supabase RLS Policy Fix for agent_results

## Problem
The backend FastAPI server cannot save `agent_results` to the `ad_analyses` table due to Row-Level Security (RLS) policy violations.

**Error**:
```
APIError: {'message': 'new row violates row-level security policy for table "ad_analyses"', 'code': '42501'}
```

## Root Cause
The existing RLS policies in `backend/sql/03_ad_analyses.sql` only allow operations where `auth.uid() = user_id`:

```sql
create policy "Users can insert their analyses"
  on public.ad_analyses for insert
  with check (auth.uid() = user_id);

create policy "Users can update their analyses"
  on public.ad_analyses for update
  using (auth.uid() = user_id);
```

However, the backend API uses the **service role key** (`SUPABASE_KEY` from `.env`), which doesn't have an authenticated user context. Therefore:
- `auth.uid()` is `null` for service role requests
- The policies reject all insert/update attempts from the backend

## Solution
Add separate RLS policies that allow the service role to insert and update records.

## How to Apply the Fix

### Option 1: Run SQL in Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard: https://app.supabase.com
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste the contents of `backend/sql/04_fix_ad_analyses_rls.sql`
5. Click **Run** to execute the SQL

### Option 2: Use Supabase CLI

```bash
# Install Supabase CLI if you haven't already
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref ltsnoprnomhaoilufuhb

# Run the migration
supabase db push
```

### Option 3: Manual SQL Execution

Connect to your Supabase PostgreSQL database and run:

```sql
-- Allow service role to insert records
create policy "Service role can insert ad_analyses"
  on public.ad_analyses for insert
  to service_role
  with check (true);

-- Allow service role to update records
create policy "Service role can update ad_analyses"
  on public.ad_analyses for update
  to service_role
  using (true);
```

## Verification

After applying the fix, test the ad analysis flow:

1. Upload an ad image in the frontend
2. Check EC2 logs for successful Supabase save:
   ```
   ✅ Successfully updated agent_results for ad_id: <uuid>
   ```
3. Verify in Supabase dashboard that `agent_results` column is populated with persona analysis data

## Security Considerations

**Q: Is it safe to allow service role full access?**

A: Yes, because:
1. The service role key (`SUPABASE_KEY`) is stored securely in the backend `.env` file (never exposed to frontend)
2. Only the backend FastAPI server has access to this key
3. The service role is meant for trusted backend operations
4. User-facing frontend requests still use the anon key with strict RLS policies

**Best Practice**: The service role should only be used in backend code, never in frontend/client-side code.

## What Changed

### Before (User-only policies)
- ✅ Frontend can create ad_analyses records (authenticated user context)
- ❌ Backend cannot update agent_results (no user context)

### After (Service role + User policies)
- ✅ Frontend can create ad_analyses records (authenticated user context)
- ✅ Backend can update agent_results (service role context)
- ✅ Users still cannot access other users' data (existing user policies remain)

## Related Files
- `backend/sql/03_ad_analyses.sql` - Original table schema with user-only RLS policies
- `backend/sql/04_fix_ad_analyses_rls.sql` - Fix to add service role policies
- `backend/api/routes/analyze.py` - Backend endpoint that saves agent_results
- `app/dashboard/page.tsx` - Frontend that creates initial ad_analyses records
