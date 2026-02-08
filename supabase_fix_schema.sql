-- 🔧 FIX: Missing Columns and RLS for installations table
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/YOUR_PROJECT/sql)

-- 1. Add missing columns to installations table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='installations' AND column_name='shutdown_time') THEN
        ALTER TABLE public.installations ADD COLUMN shutdown_time text;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='installations' AND column_name='store_active') THEN
        ALTER TABLE public.installations ADD COLUMN store_active boolean DEFAULT true;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='installations' AND column_name='pharmacy_active') THEN
        ALTER TABLE public.installations ADD COLUMN pharmacy_active boolean DEFAULT true;
    END IF;
END $$;

-- 2. Configure RLS (Row Level Security)
-- Option A: Disable RLS for installations (easiest for small operations)
-- ALTER TABLE public.installations DISABLE ROW LEVEL SECURITY;

-- Option B: Keep RLS but add permissive policies (more secure)
-- Allow anyone with the key (service role or publishable) to read/update
-- Note: Service role key bypasses this anyway, but this helps if using publishable key.
DROP POLICY IF EXISTS "Enable read access for all users" ON public.installations;
CREATE POLICY "Enable read access for all users" ON public.installations FOR SELECT USING (true);

DROP POLICY IF EXISTS "Enable update for all users" ON public.installations;
CREATE POLICY "Enable update for all users" ON public.installations FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Enable insert for all users" ON public.installations;
CREATE POLICY "Enable insert for all users" ON public.installations FOR INSERT WITH CHECK (true);

-- 3. Verify the columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'installations' 
AND column_name IN ('shutdown_time', 'store_active', 'pharmacy_active');
