import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from embed import embed_jobs

load_dotenv()

INPUT_PATH = Path(__file__).parent.parent / "data" / "deduped" / "a16z_build.json"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INSERT_URL = f"{SUPABASE_URL}/rest/v1/companies?on_conflict=content_hash"

if __name__ == "__main__":
    jobs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    embeddings = embed_jobs(jobs)
    print(f"Embedded {len(embeddings)} jobs")

    rows = [
        {
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "industry": job["industry"],
            "date_posted": job["date_posted"],
            "date_scraped": job["date_scraped"],
            "source": job["source"],
            "raw_text": job["raw_text"],
            "content_hash": job["content_hash"],
            "embedding": embedding,
        }
        for job, embedding in zip(jobs, embeddings)
    ]

    response = requests.post(
        INSERT_URL,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=ignore-duplicates",
        },
        data=json.dumps(rows),
    )
    print(response.status_code)
    if response.status_code >= 300:
        print(response.text)
    else:
        print(f"Inserted rows into Supabase (duplicates on content_hash ignored)")
