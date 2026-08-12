# Design Decisions

Log of non-obvious architectural tradeoffs. Only decisions where a real alternative was weighed and rejected for a substantive reason.

---

## 1. Per-post LLM extraction, not batched

**Decision:** One LLM extraction call per scraped post. Not one call per scheduled batch (e.g. all 4 sources at 6:30am).

**Alternative considered:** Batch all articles from a scheduled run into a single call.

**Why rejected:**

- **Attribution errors.** Multiple articles in one context means company/title pairs can bind to the wrong company. Worse when sources are structurally similar (a16z Build and VC Hiring look near-identical to a model). Per-post makes this class of error nearly impossible.
- **Recall decay.** Emitting 80+ records in one response degrades thoroughness mid-list. Per-post keeps output at ~15-25 records, where recall stays high.
- **Silent truncation.** Large outputs can hit max output tokens and truncate. With no error handling in v1, this looks like "fewer jobs today" rather than a visible failure.
- **Positional bias.** Middle-of-context articles get attended to less reliably.
- **Per-source prompts.** Sources aren't uniform. a16z Build and VC Hiring are semi-structured lists; Newcomer and Not Boring bury hiring signal in prose. These need different prompts. Batching forces one generic prompt that underperforms on both.

**What batching would have bought:** Effectively nothing at this volume. 4 calls/day vs 1 call/day is a rounding error on cost and latency. Batching pays off at thousands of calls, not four.

**Open question:** Per-post may be too _coarse_, not too fine. A single a16z Build issue with 60 roles might extract better if chunked (by section, or N roles per call). Worth measuring once real data exists.

---

## 2. Structured filters for date and location, not semantic matching

**Decision:** Parse date and location into structured columns and filter/sort on them directly. Only title and description text go through embedding + reranking.

**Alternative considered:** Embed the whole job record and let semantic similarity handle the full query, including "posted this week" and "in Toronto".

**Why rejected:** Recency and location aren't semantic properties. An embedding model has no reliable notion of "last 14 days" and treats city names as weak text similarity rather than a geographic constraint. Hybrid retrieval — structured filter first, semantic rank second — is meaningfully more accurate for queries that mix both, which is the expected query shape here.

---

## 3. Supabase (Postgres + pgvector) over SQLite

**Decision:** Supabase.

**Alternative considered:** SQLite — genuinely cheaper (file-based, zero infra) and adequate for the row volume.

**Why rejected:**

- Embeddings need a vector store. SQLite would require bolting on a separate vector DB, adding a second system to manage.
- SQLite has no server, users, or infra to administer, so it demonstrates little about database management — an explicit goal for this project as a portfolio piece.

**Cost of the choice:** Free-tier dependency and a network hop per query that SQLite wouldn't have. Acceptable at this scale.

---

## 4. Narrative newsletters as sources, not job boards

**Decision:** Scrape startup news/newsletters where hiring signal lives in prose. Explicitly not job boards.

**Alternative considered:** Job boards (Work at a Startup, etc.) — already structured, trivially parseable, far higher volume.

**Why rejected:** Structured boards would make the LLM extraction step nearly vacuous, removing the part of the project that's actually interesting to build and learn from. Newsletters also surface roles earlier and in context, before they're formally posted.

**Cost of the choice:** Extraction is now the hardest part of the pipeline rather than a solved step, and `date_posted` is unreliable — newsletters bundle roles posted weeks earlier, so what's actually captured is "date the newsletter mentioned it."

---

## 5. X/Twitter ruled out as a source

**Decision:** No X sources in v1, despite good accounts posting startup hiring news.

**Why:** API read access starts around $200/month; scraping outside the API violates ToS. Substack-hosted narrative newsletters (Newcomer, Not Boring) cover the same ground in the same voice with no cost or ToS friction.

---

## 6. Hash-based dedup, not semantic dedup

**Decision:** Hash of normalized company + title, checked before insert.

**Alternative considered:** Embedding-similarity dedup, which would catch near-duplicates ("ML Engineer" vs "Machine Learning Engineer" at the same company).

**Why rejected for v1:** Hashing is deterministic, debuggable, and free. Semantic dedup requires a similarity threshold that has to be tuned against real data — and picking that threshold blind, before knowing what the duplicate distribution actually looks like, means guessing. Start with hashing, measure what it misses, then decide whether semantic dedup is warranted.

---

## 7. Structured filters passed as explicit args, not parsed from the NL query

**Decision:** Date/location filters for the query path (Step 5) are supplied as explicit function/CLI args (e.g. `location="Toronto"`, `days=14`), applied before the vector search. Not parsed out of the free-text query itself.

**Alternative considered:** Parse the NL query text (e.g. "remote roles from the last 2 weeks") with an LLM call to extract structured filter values automatically, then apply them the same way.

**Why rejected for v1:** Per decision #2, date and location are structured filters, not semantic matches — that part is settled. What's open is *how the filter values get populated*. Auto-parsing adds another LLM call, another point of failure, and effort spent designing an extraction step before it's clear what a real UI actually needs to pass through. There's no dashboard yet (Step 6), so the shape of the input is still unknown. Explicit args keep the query path simple and testable now; NL parsing of filters can be added later once the dashboard defines what natural input actually looks like, without requiring rework of the vector-search/rerank logic underneath.

---

## 8. Industry as an enum with `OTHER`, classified in the original extraction call — not a separate normalization step

**Decision:** `industry` is extracted as a fixed enum (12 categories + `OTHER`) directly in the existing per-post extraction call (decision #1), by constraining the JSON schema. Not extracted as free text and then normalized in a second pass.

**Alternative considered:** Extract `industry` as open free text first, then run a second step — either another LLM call or an embedding-similarity match against the enum labels — to map the free text onto the closest fixed category.

**Why rejected:**

- **Less context, not more.** A second normalization step only sees the freeform label produced by step one, not the original post text. The first-pass model already has full context when it extracts; deferring the categorical decision to a step with strictly less information can't improve accuracy.
- **Embedding-similarity matching is unreliable on short, overlapping labels.** Enum values like "Robotics & Hardware", "Autonomous Vehicles & Logistics", and "Defense & Aerospace" are close together in embedding space. Matching a 2-4 word freeform label against 2-4 word enum labels by cosine similarity is exactly the kind of ambiguous case that needs contextual judgment, not vector-space nearness of short strings.
- **No added cost.** Constraining the existing extraction call's schema from `string` to enum is free — same call, same context, just a stricter output shape. A second LLM call would add latency and cost for a worse-informed decision.

**Why `OTHER` (not a strict closed enum, and not left as open free text):** A hard-forced enum with no escape hatch guarantees misclassification on jobs that don't fit any category (EdTech, legal tech, a copywriter role where the company's product is irrelevant to the role) — the model would be forced to pick a wrong bucket rather than surface the miss. That's the same silent-failure shape flagged in decision #1 ("looks like fewer jobs today" instead of a visible failure). `OTHER` makes a bad fit visible in the data instead of hiding it inside a wrong category, while still keeping industry structured/filterable — unlike leaving the field as unconstrained free text, which was the original (rejected) approach that made downstream filtering unreliable in the first place.

---

## 9. Industry as a structured pre-filter, not folded into the embedded/reranked text

**Decision:** `industry` is applied as an exact-match filter (`match_companies`'s new `filter_industry` param, and a dropdown in the dashboard) before vector search runs — same pattern as the existing `filter_location` and `min_date_posted` filters (decision #2). `embed_text()` and the reranker's document text no longer append `", a {industry} company"`.

**Alternative considered (what v1 shipped):** Blend industry into the embedded text (`"{title} at {company}, a {industry} company"`) and let cosine similarity/rerank handle it implicitly alongside the free-text query.

**Why rejected:** Industry is already a closed enum by the time it reaches embedding (decision #8) — it's categorical, not a semantic property of the text. Folding a categorical value into the embedding makes it a soft, unreliable signal (exactly the "short, overlapping labels are close together in embedding space" problem already flagged in decision #8) when it could instead be an exact, deterministic `WHERE industry = ...` filter, applied before the semantic ranking step even runs. This is the same hybrid-retrieval argument as decision #2: structured filter first, semantic rank second, for anything that isn't actually a semantic property.

**Cost of the choice:** Existing embeddings were generated with the old (industry-inclusive) text and must be regenerated — re-run `embedding/run.py` against `data/deduped/a16z_build.json` and re-insert (or truncate + reinsert) `companies` — since the embedding vectors for old rows no longer match the current `embed_text()` shape. The `match_companies` Postgres function also needs to be recreated from `sql/match_companies.sql` (see that file's header) since it was previously managed by hand in the Supabase SQL Editor and had no `filter_industry` param.
