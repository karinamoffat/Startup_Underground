import os

import cohere
import requests
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = "embed-english-v3.0"
RERANK_MODEL = "rerank-v3.5"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RPC_URL = f"{SUPABASE_URL}/rest/v1/rpc/match_companies"

client = cohere.Client(COHERE_API_KEY)


def embed_query(text: str) -> list[float]:
    response = client.embed(
        texts=[text],
        model=EMBED_MODEL,
        input_type="search_query",
    )
    return response.embeddings[0]


def vector_search(
    query_embedding: list[float],
    match_count: int = 50,
    location: str | None = None,
    min_date_posted: str | None = None,
    industry: str | None = None,
) -> list[dict]:
    response = requests.post(
        RPC_URL,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query_embedding": query_embedding,
            "match_count": match_count,
            "filter_location": location,
            "min_date_posted": min_date_posted,
            "filter_industry": industry,
        },
    )
    response.raise_for_status()
    return response.json()


def rerank(query_text: str, candidates: list[dict], top_k: int = 10) -> list[dict]:
    if not candidates:
        return []
    documents = [f"{c['title']} at {c['company']}" for c in candidates]
    response = client.rerank(
        model=RERANK_MODEL,
        query=query_text,
        documents=documents,
        top_n=min(top_k, len(candidates)),
    )
    return [candidates[r.index] for r in response.results]


def search(
    query_text: str,
    location: str | None = None,
    min_date_posted: str | None = None,
    industry: str | None = None,
    match_count: int = 50,
    top_k: int = 10,
) -> list[dict]:
    query_embedding = embed_query(query_text)
    candidates = vector_search(
        query_embedding,
        match_count=match_count,
        location=location,
        min_date_posted=min_date_posted,
        industry=industry,
    )
    return rerank(query_text, candidates, top_k=top_k)
