# Job scraper — project plan

Task: use semantic + keyword searching to identify career opportunities from predefined sources that align with the user's natural language input.

## What this is

Scrapes easy-to-scrape blogs/newsletters (e.g. a16z Build Substack) for US tech/AI/ML job postings, extracts structured fields with an LLM, dedupes, stores in Supabase, and serves a simple-structured dashboard (company, industry, and if available an open job position title) that prioritizes readability.

## Goals (v1)

- Scrape the sources listed below
- Extract structured job data following shape listed below, via LLM from unstructured newsletter text
- Dedupe via hashing before storing
- Store in Supabase (Postgres + pgvector)
- Query via natural language text box → embed → vector search → rerank
- Dashboard shows ranked list: company name, industry, and (optional) job title only

## Sources

- **a16z Build** (a16zbuild.substack.com) — structured weekly hiring lists across a16z portfolio companies. Build and test the pipeline against this first.
- **VC Hiring** (vchiring.substack.com) — same Substack structure as a16z Build, weekly, startup/VC job opportunities. Second source, reuses most of the first parser.
- **Newcomer** (newcomer.co) by Eric Newcomer — single-author narrative style, hiring signal buried in prose rather than listed. Add once the pipeline works end-to-end, to stress-test LLM extraction against messier text.
- **Not Boring** (notboring.co) by Mario Gabriele — narrative-style startup/VC coverage. Candidate source alongside or after Newcomer.

## Explicitly out of scope for v1 DO NOT INCLUDE

- test cases
- Error handling / retries / alerting
- Job links in output
- Auth, multi-user support
- Sources beyond the four listed above

## Architecture

Two independent pipelines sharing one Supabase instance:

**Ingestion (batch, scheduled)**
Sources → Scheduler (per-source frequency) → Scraper → LLM extraction → Dedup (hash) → Supabase

**Query (on-demand)**
NL query box → Embedding model → pgvector similarity search → Reranker (cross-encoder) → Dashboard

## Data model (Supabase)

- `companies` table: `id`, `company`, `title`, `location`, `date_posted` (as stated in source), `date_scraped`, `source`, `raw_text`, `content_hash` (for dedup), `embedding` (vector)
- Unique constraint or lookup on `content_hash` to prevent duplicate inserts

## Tech choices (decided)

- Language: Python
- DB: Supabase (Postgres + pgvector)
- Extraction: Kimi K3 (via OpenRouter), one LLM call per scraped post → structured JSON (company, title, location, date)
- Dedup: hash of normalized company+title (or similar) checked before insert
- Embedding + reranking: Cohere `embed-v3` for embeddings, Cohere `rerank-v3.5` for reranking top-N vector matches
- Scheduler: frequency per source, based on how often each source publishes

## Build order

1. **Scraper for one source** (a16z Build) — fetch raw post content, store raw text in Supabase
2. **LLM extraction** — one LLM call per post, turn raw text into structured fields; validate against a handful of real posts by hand
3. **Dedup** — hash check before insert; test against reposted/duplicate listings
4. **Embedding + storage** — embed job text on insert, store vector in `companies`
5. **Query path** — NL text box → embed query → pgvector search → rerank → return top results
6. **Dashboard** — minimal UI rendering company, industry, (if available) job title from query results
7. **Scheduler** — wire up recurring runs per source
8. **Add VC Hiring** as second source once the pipeline works end-to-end for a16z Build
9. **Add Newcomer or Not Boring** once both structured sources work, to stress-test LLM extraction against narrative (non-listy) text

## Notes for Claude Code

- Build and test each pipeline stage independently before wiring the next (scraper → extraction → dedup → embedding → query → dashboard)
- Prioritize getting one source fully working end-to-end before adding more sources
- No error handling needed yet — let failures surface directly during v1 development
