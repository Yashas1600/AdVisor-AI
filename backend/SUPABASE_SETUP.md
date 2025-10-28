# Supabase Setup Guide

## Installation

Supabase SDK is already installed. Dependencies are in `requirements.txt`.

## Configuration

### 1. Get Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and create a project
2. Navigate to Settings > API
3. Copy your:
   - Project URL
   - Anon/Public Key

### 2. Update Environment Variables

Edit `.env` in the project root:

```bash
SUPABASE_URL=your_project_url_here
SUPABASE_KEY=your_anon_key_here
```

## Usage

### Basic Client Usage

```python
from config import get_client

# Get Supabase client
supabase = get_client()

# Insert data
response = supabase.table('table_name').insert({"key": "value"}).execute()

# Query data
response = supabase.table('table_name').select("*").execute()

# Update data
response = supabase.table('table_name').update({"key": "new_value"}).eq('id', 1).execute()

# Delete data
response = supabase.table('table_name').delete().eq('id', 1).execute()
```

### Examples

See `examples/supabase_example.py` for detailed examples of:
- Inserting Reddit posts
- Querying with filters
- Upserting features
- Working with author profiles

## Database Schema Suggestions

### Table: reddit_posts
```sql
CREATE TABLE reddit_posts (
  id BIGSERIAL PRIMARY KEY,
  post_id TEXT UNIQUE NOT NULL,
  title TEXT,
  url TEXT,
  author TEXT,
  community TEXT,
  upvotes INTEGER,
  num_comments INTEGER,
  content TEXT,
  created_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: post_comments
```sql
CREATE TABLE post_comments (
  id BIGSERIAL PRIMARY KEY,
  post_id TEXT REFERENCES reddit_posts(post_id),
  comment_id TEXT UNIQUE,
  author TEXT,
  content TEXT,
  upvotes INTEGER,
  parent_id TEXT,
  created_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: author_profiles
```sql
CREATE TABLE author_profiles (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  profile_url TEXT,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  last_updated TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: post_features
```sql
CREATE TABLE post_features (
  id BIGSERIAL PRIMARY KEY,
  post_id TEXT UNIQUE REFERENCES reddit_posts(post_id),
  sentiment_score FLOAT,
  emotion_tags TEXT[],
  visual_features JSONB,
  audio_features JSONB,
  text_complexity FLOAT,
  extracted_at TIMESTAMPTZ DEFAULT NOW()
);
```

## API Reference

### Common Operations

#### Select with Filters
```python
supabase.table('posts').select("*").eq('community', 'fitness').execute()
```

#### Ordering
```python
supabase.table('posts').select("*").order('upvotes', desc=True).execute()
```

#### Limit and Pagination
```python
supabase.table('posts').select("*").range(0, 9).execute()  # First 10 rows
```

#### Greater Than / Less Than
```python
supabase.table('posts').select("*").gte('upvotes', 100).execute()
supabase.table('posts').select("*").lte('upvotes', 50).execute()
```

#### Upsert (Insert or Update)
```python
supabase.table('posts').upsert(data, on_conflict='post_id').execute()
```

## Error Handling

```python
from supabase import Client
from config import get_client

try:
    supabase = get_client()
    response = supabase.table('posts').select("*").execute()
    print(response.data)
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Database error: {e}")
```

## Files Created

- `config/supabase_client.py` - Client configuration with singleton pattern
- `config/__init__.py` - Config module exports
- `examples/supabase_example.py` - Usage examples
- `SUPABASE_SETUP.md` - This documentation

## Next Steps

1. Set your Supabase credentials in `.env`
2. Create database tables using the SQL schemas above
3. Test connection with `examples/supabase_example.py`
4. Start storing Reddit data and extracted features
