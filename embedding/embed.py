import os

import cohere
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
MODEL = "embed-english-v3.0"
BATCH_SIZE = 96

client = cohere.Client(COHERE_API_KEY)


def embed_text(job: dict) -> str:
    return f"{job['title']} at {job['company']}"


def embed_jobs(jobs: list[dict]) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        response = client.embed(
            texts=[embed_text(job) for job in batch],
            model=MODEL,
            input_type="search_document",
        )
        embeddings.extend(response.embeddings)
    return embeddings
