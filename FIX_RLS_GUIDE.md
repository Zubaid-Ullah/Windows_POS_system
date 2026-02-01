# 🔧 FIX: Authorized Persons Table Empty Issue

## Problem
Your `authorized_persons` table has data but queries return empty results.

## Root Cause
**Row Level Security (RLS)** is enabled on the table, blocking anonymous reads.

## Solution Options

### Option 1: Disable RLS (Recommended for Development)

1. **Open Supabase Dashboard**
   - Go to your project: https://supabase.com/dashboard/project/YOUR_PROJECT

2. **Navigate to Table**
   - Go to **Database** → **Tables**
   - Click on `authorized_persons` table

3. **Disable RLS**
   - Go to **Authentication** tab
   - Toggle **Row Level Security** to **OFF**

### Option 2: Create RLS Policy (Production Approach)

Run this SQL in **SQL Editor**:

```sql
-- Allow anonymous reads for installer authentication
CREATE POLICY "Allow anonymous read authorized_persons" ON authorized_persons
FOR SELECT USING (true);
```

### Option 3: Use Service Role Key

Ensure your `.env` file has:
```
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

Service role keys bypass RLS completely.

## Verification

After applying the fix:

1. **Run the app**:
   ```bash
   cd /Users/apple/Documents/GitHub/POS_system
   python3 main.py
   ```

2. **Check console output** - you should see:
   ```
   🔑 Using SERVICE ROLE key (bypasses RLS)
   🔍 Raw response from authorized_persons: [{'id': '...', 'names': 'installer1'}, ...]
   ✅ Found 1 valid installer names: ['installer1']
   ```

3. **Registration should work**!

## Quick SQL Verification

Run in Supabase SQL Editor:
```sql
-- Check RLS status
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'authorized_persons';

-- Check data
SELECT COUNT(*) as total_installers FROM authorized_persons;
SELECT names FROM authorized_persons LIMIT 5;
```