-- match_companies: cosine-similarity search over companies.embedding,
-- with structured pre-filters applied before ranking (location, date, industry).
--
-- Run this in the Supabase SQL Editor to (re)create the function. Postgres
-- won't let CREATE OR REPLACE change a function's parameter list, so drop
-- first (matches the approach used when `industry` was added to the return
-- columns — see CHECKPOINT.md Step 6).
--
-- Refinement (2026-08-12): added filter_industry as a keyword/exact-match
-- pre-filter, so industry is no longer folded into the embedded text or
-- matched semantically — see DESIGN_DECISIONS.md #9.

drop function if exists match_companies(vector, int, text, text);
drop function if exists match_companies(vector, int, text, text, text);

create or replace function match_companies(
  query_embedding vector(1024),
  match_count int,
  filter_location text default null,
  min_date_posted text default null,
  filter_industry text default null
)
returns table (
  id bigint,
  company text,
  title text,
  location text,
  industry text,
  date_posted text,
  date_scraped text,
  source text,
  raw_text text,
  content_hash text,
  similarity float
)
language sql stable
as $$
  select
    c.id,
    c.company,
    c.title,
    c.location,
    c.industry,
    c.date_posted,
    c.date_scraped,
    c.source,
    c.raw_text,
    c.content_hash,
    1 - (c.embedding <=> query_embedding) as similarity
  from companies c
  where (filter_location is null or c.location ilike '%' || filter_location || '%')
    and (min_date_posted is null or c.date_posted::timestamptz >= min_date_posted::timestamptz)
    and (filter_industry is null or c.industry = filter_industry)
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
