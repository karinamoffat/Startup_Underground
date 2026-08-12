Current Issues:

1. how are we filtering location? i don't remember scraping for this, is it in the companies table?
2. [RESOLVED 2026-08-12] industry now filters as a structured pre-filter (exact match) before semantic search, not blended into the embedding — see DESIGN_DECISIONS.md #9. Dashboard has an industry dropdown instead of tabs. Needs: re-run `sql/match_companies.sql` in Supabase, and re-embed/re-insert existing rows (old embeddings still have industry baked into the text).
