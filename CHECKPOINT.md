# Checkpoint — 2026-08-11

## Stack (locked in, see PLAN.md "Tech choices")

- Python, venv at `.venv/`
- Extraction: Kimi K3 via OpenRouter (`moonshotai/kimi-k3`)
- Embedding + rerank: Cohere (`embed-v3`, `rerank-v3.5`)
- Storage: Supabase (Postgres + pgvector)
- All keys live in `.env` (gitignored): `OPENROUTER_API_KEY`, `COHERE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` — all confirmed loading correctly.

## Progress against build order

- [x] **Step 1 — Scraper**: `scraper/a16z_build.py` + `scraper/run.py`. Pulls the a16z Build Substack RSS feed (`https://a16zbuild.substack.com/feed`), extracts clean text from `content:encoded`. Output: `data/raw/a16z_build.json` (20 posts).
- [x] **Step 2 — LLM extraction**: `extraction/extract.py` + `extraction/run.py`. One Kimi K3 call per post (JSON-schema-constrained output). Fields: `company`, `title`, `location`, `industry` (enum, 12 categories + `OTHER` — added mid-Step-6, see below). `max_tokens=8000` (raised from an original 3000 — see Step 6 notes). Output: `data/extracted/a16z_build.json` (239 jobs from 20 posts, current run).
- [x] **Step 3 — Dedup**: `dedup/dedup.py` (hash of normalized company+title) + `dedup/run.py`. Output: `data/deduped/a16z_build.json` (234 unique jobs, current run — 5 duplicates correctly caught each run, real repeats across newsletter issues).
- [x] **Step 4 — Embedding + storage**: `embedding/embed.py` + `embedding/run.py`. `companies` table + pgvector extension created via Supabase SQL Editor (`industry text` column added later via `alter table`). Embeds `"{title} at {company}, a {industry} company"` per job (location deliberately excluded from the embedded text — see Step 6 notes) via Cohere `embed-english-v3.0` (note: model ID is `embed-english-v3.0`, not `embed-v3.0`), `input_type="search_document"`, batched at 96 texts/call. Inserts via Supabase REST (`requests`, not the `supabase` client library) with `Prefer: resolution=ignore-duplicates` on `content_hash` so reruns are safe. 234/234 rows confirmed in Supabase (current run).
  - Embedding text deliberately excludes `raw_text` — it's the whole newsletter post and identical across every job extracted from that post, so including it would blur per-job semantic distinctness (see DESIGN_DECISIONS.md #2: only title/description-type text should be embedded).
- [x] **Step 5 — Query path**: `query/search.py` + `query/run.py`. Postgres RPC function `match_companies` (created manually in Supabase SQL Editor) does cosine similarity search over `embedding`, with optional `filter_location` (ILIKE substring) and `min_date_posted` (casts the `text` column to `timestamptz` at query time) params applied before ranking. `embed_query()` uses Cohere `embed-english-v3.0` with `input_type="search_query"` (asymmetric with `search_document` used at insert time). Top-50 vector matches get reranked with Cohere `rerank-v3.5` against the same text shape used for the stored embeddings. CLI: `python query/run.py "<nl query>" [--location X] [--min-date-posted ISO8601] [--top-k N]`. Verified end-to-end.
- [x] **Step 6 — Dashboard**: `dashboard/app.py`, Streamlit. NL query box + optional location filter + result-count slider, wired to `query/search.py`. Results show company, title, industry only (per PLAN.md scope — location is used as a filter but not displayed, `OTHER` industry is hidden rather than shown as a label). Run with `python -m streamlit run dashboard/app.py`. Verified in-browser via claude-in-chrome: query "machine learning engineer at an early-stage AI startup" returned relevant AI/ML roles with correct industry tags.
  - Mid-step schema change: added enum-constrained `industry` field (12 categories + `OTHER`) to extraction — see DESIGN_DECISIONS.md #8 for why enum-in-extraction-call was chosen over a separate normalization pass, and #2/#7 context for why location was then dropped from the embedded text (redundant with the existing `ILIKE` filter, and the same "embeddings have no reliable notion of geography" reasoning applies). Required: re-running extraction, re-dedup, clearing + re-inserting the `companies` table, and recreating `match_companies` (Postgres won't let `CREATE OR REPLACE` change a function's return columns — needed `DROP FUNCTION` first, then recreate with `industry` added to the return table).
  - `max_tokens` in `extraction/extract.py` had to go 3000 → 4500 → 8000 across two failed runs (`content: None`, then mid-string JSON truncation) once the industry field increased per-job output size on dense posts (a16z posts run up to ~20 jobs each).
  - Environment gotcha: `pip`/`python` on this machine can resolve to different Python installs (3.11 WindowsApps vs 3.14 pythoncore). Plain `pip install <pkg>` silently installed streamlit into the wrong interpreter, so `import streamlit` failed under `python`. Use `python -m pip install <pkg>` to guarantee it lands in the interpreter `python` actually runs.
- [ ] Step 7 — Scheduler
- [ ] Step 8 — Add VC Hiring as second source
- [ ] Step 9 — Add Newcomer or Not Boring

## Repo layout so far

```
find_my_job_please/
  .env                  # gitignored, has all 4 keys
  .venv/
  PLAN.md
  DESIGN_DECISIONS.md
  CHECKPOINT.md          # this file
  scraper/{a16z_build.py, run.py}
  extraction/{extract.py, run.py}
  dedup/{dedup.py, run.py}
  embedding/{embed.py, run.py}
  query/{search.py, run.py}
  dashboard/app.py
  data/{raw,extracted,deduped}/a16z_build.json
```

## To resume

Pick up at Step 7 — Scheduler. Everything through Step 6 (scrape → extract → dedup → embed/store → query → dashboard) is built and verified end-to-end for the a16z Build source. Dashboard: `python -m streamlit run dashboard/app.py`.
