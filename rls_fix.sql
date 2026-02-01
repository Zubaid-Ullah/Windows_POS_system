-- Fix Row Level Security for authorized_persons table
-- Run this in Supabase SQL Editor

-- Disable RLS on authorized_persons table
ALTER TABLE authorized_persons DISABLE ROW LEVEL SECURITY;

-- OR create a policy that allows anonymous reads (alternative approach)
-- DROP POLICY IF EXISTS "Allow anonymous read on authorized_persons" ON authorized_persons;
-- CREATE POLICY "Allow anonymous read on authorized_persons" ON authorized_persons
-- FOR SELECT USING (true);

-- Verify the table has data
SELECT COUNT(*) as total_records FROM authorized_persons;

-- Show sample data
SELECT id, names, created_at FROM authorized_persons LIMIT 5;