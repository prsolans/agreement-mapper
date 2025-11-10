# Supabase Storage Setup Guide

This guide explains how to configure Supabase for persistent storage of company analyses in Agreement Map.

## Why Supabase?

Supabase provides production-ready PostgreSQL storage with these benefits:
- **Cloud-compatible**: Works seamlessly with Streamlit Cloud (unlike local JSON files)
- **Reliable**: ACID-compliant PostgreSQL database
- **Fast**: Indexed queries for quick retrieval
- **Flexible**: JSONB storage adapts to schema changes
- **Scalable**: No row/cell limits like Google Sheets

## Quick Setup

### 1. Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up for a free account
3. Create a new project

### 2. Create the Database Table

In your Supabase project dashboard:

1. Go to the SQL Editor
2. Run this SQL command to create the `analyses` table:

```sql
CREATE TABLE analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    analysis_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX idx_analyses_company_name ON analyses(company_name);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
```

### 3. Get Your API Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Find these two values:
   - **Project URL** (e.g., `https://your-project-id.supabase.co`)
   - **anon/public key** (long string starting with `eyJ...`)

### 4. Configure Agreement Map

Option A: **Using secrets.toml (Recommended for local development)**

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Edit `.streamlit/secrets.toml` and add your Supabase credentials:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   key = "your-supabase-anon-key-here"
   ```

3. **Important**: `.streamlit/secrets.toml` is gitignored - never commit it!

Option B: **Using Streamlit Cloud**

1. Go to your app settings in Streamlit Cloud
2. Under "Secrets", add:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   key = "your-supabase-anon-key-here"
   ```

## Testing Your Setup

1. Start Agreement Map:
   ```bash
   ./start.sh
   ```

2. Run an analysis on any company

3. Check the sidebar - you should see:
   - "Supabase not configured" → Your credentials are incorrect or missing
   - List of saved analyses → Success! Your analyses are being saved

4. Verify in Supabase:
   - Go to your Supabase dashboard → Table Editor → `analyses`
   - You should see your saved analyses with timestamps

## Troubleshooting

### "Supabase not configured" message

**Cause**: Credentials not found or incorrect

**Fix**:
- Verify `.streamlit/secrets.toml` exists and has correct format
- Check URL doesn't have trailing slash
- Verify the anon key is complete (starts with `eyJ...`)
- Restart Agreement Map after adding credentials

### Table doesn't exist error

**Cause**: Haven't run the SQL command to create the table

**Fix**:
- Go to Supabase SQL Editor
- Run the CREATE TABLE command from Step 2 above

### Row Level Security (RLS) errors

**Cause**: Supabase has RLS enabled by default

**Fix**: For development/testing, you can disable RLS:
```sql
ALTER TABLE analyses DISABLE ROW LEVEL SECURITY;
```

**For production**, set up proper RLS policies:
```sql
-- Allow anonymous inserts and reads (read-only public access)
CREATE POLICY "Allow anonymous access" ON analyses
    FOR ALL
    USING (true)
    WITH CHECK (true);
```

## Migration from Google Sheets

If you have existing analyses in Google Sheets:

1. Export your analyses as JSON from the old system
2. Load the JSON files and re-save them (the app will auto-save to Supabase)
3. Or bulk import using the Supabase SQL Editor

## Features

Once configured, Supabase provides:

- ✅ **Auto-save**: Every analysis automatically saves to Supabase
- ✅ **Load**: Click any saved analysis in the sidebar to reload it
- ✅ **Delete**: Remove unwanted analyses with one click
- ✅ **Search**: Find analyses by company name
- ✅ **Timestamps**: Track when each analysis was created/updated
- ✅ **Persistent**: Your data is safe in the cloud

## Database Schema

The `analyses` table structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Unique identifier (auto-generated) |
| `company_name` | TEXT | Name of analyzed company |
| `timestamp` | TIMESTAMPTZ | Analysis timestamp |
| `analysis_json` | JSONB | Complete analysis data |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

The `analysis_json` JSONB column stores the entire analysis structure, including:
- Company profile
- Business units
- Strategic priorities
- Executive quotes (with confidence scores)
- Opportunity analysis
- Executive summary
- Discovery questions
- Product recommendations

## Security Notes

- **Anon key is public**: The anon key can be safely embedded in client-side code
- **RLS policies**: Use Row Level Security for multi-user environments
- **No sensitive data**: Don't store API keys or credentials in analyses
- **Backup**: Supabase free tier includes automatic backups

## Need Help?

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord Community](https://discord.supabase.com)
- Check `supabase_storage.py` for implementation details
