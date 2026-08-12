# Startup Underground

An untraditional approach to tech-job hunting. Instead of relying on job boards that scrape formal job postings, Startup Underground finds the undeground startups that aren't even posting for jobs.

A lot of articles have been written on the shift in job hunting, especially for students/juniors in tech. This product was formed from the idea of going through side-doors. Find startups that are solving problems you find cool and you are qualified for. These startups typically don't have job postings yet, so they aren't on your traditional job boards.

In a nutshell, Startup Undeground scrapes VC/startup hiring newsletters multiple times a week,
extracts structured job data with an LLM, and searches it with a hybrid of
structured filters (industry, location, date) and semantic search + reranking.

## How it works

```
Newsletter source
    -> Scraper (fetch raw post text)
    -> LLM extraction (Kimi K3): company, title, location, industry (enum)
    -> Dedup (hash of normalized company + title)
    -> Embed (Cohere embed-v3) + insert into Supabase (Postgres + pgvector),
       tagged with its industry
    -> Dashboard: pick an industry (exact filter) + type a query
       -> embed query -> pgvector similarity search (pre-filtered by
          industry/location/date) -> Cohere rerank -> ranked results
```

Industry is classified into a fixed enum by the same LLM call that extracts
the job fields (see `DESIGN_DECISIONS.md` #8), and applied as a structured
`WHERE` filter before semantic ranking runs — not blended into the embedding
(`DESIGN_DECISIONS.md` #9). Location and date are handled the same way
(`DESIGN_DECISIONS.md` #2).

Full build log and rationale for every non-obvious choice: `PLAN.md`,
`DESIGN_DECISIONS.md`, `CHECKPOINT.md`.

## Sources

Currently scrapes **a16z Build** (a16zbuild.substack.com). See `PLAN.md` for
the full source list and rollout order.

## Stack

- Python
- Extraction: Kimi K3 via OpenRouter
- Embedding + rerank: Cohere (`embed-english-v3.0`, `rerank-v3.5`)
- Storage: Supabase (Postgres + pgvector)
- Dashboard: Streamlit

## Running it locally

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Create a `.env` in the project root with:

```
OPENROUTER_API_KEY=...
COHERE_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

Run the pipeline stages in order:

```
python scraper/run.py
python extraction/run.py
python dedup/run.py
python embedding/run.py
```

Then either query from the CLI:

```
python query/run.py "machine learning engineer" --industry "AI & Data Infrastructure" --location remote --top-k 10
```

or launch the dashboard:

```
python -m streamlit run dashboard/app.py
```

## Database setup

`companies` table (Postgres + pgvector extension) and the `match_companies`
RPC function (`sql/match_companies.sql`) are created in the Supabase SQL
Editor — paste `sql/match_companies.sql` in to (re)create the search
function after schema changes.

## Deploying

The dashboard is a Streamlit app, deployed on Streamlit Community Cloud
(share.streamlit.io) pointed at `dashboard/app.py`, with the four `.env`
variables above set as app secrets.
