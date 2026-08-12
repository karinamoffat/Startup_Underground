import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "moonshotai/kimi-k3"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

INDUSTRIES = [
    "Defense & Aerospace",
    "Robotics & Hardware",
    "FinTech & InsurTech",
    "Healthcare & BioTech",
    "AI & Data Infrastructure",
    "Enterprise SaaS & B2B",
    "Consumer & E-Commerce",
    "Energy & ClimateTech",
    "Cybersecurity & Trust",
    "Gaming, Media & Entertainment",
    "PropTech & Real Estate",
    "Autonomous Vehicles & Logistics",
    "OTHER",
]

SYSTEM_PROMPT = f"""You extract job openings from a startup/VC hiring newsletter post.

Read the post text and return every distinct open role mentioned, with:
- company: the hiring company's name
- title: the job title
- location: the location as stated (city, "remote", etc.), or null if not stated
- industry: classify what the company does into exactly one of these categories,
  based on the description given in the text: {", ".join(INDUSTRIES)}.
  Use "OTHER" if the company's industry doesn't clearly fit any other category,
  or if the text gives no indication of what the company does.

Only include roles the text presents as an actual open position to apply for.
Do not invent roles, companies, or locations not grounded in the text."""

JOBS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "extracted_jobs",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "title": {"type": "string"},
                            "location": {"type": ["string", "null"]},
                            "industry": {"type": "string", "enum": INDUSTRIES},
                        },
                        "required": ["company", "title", "location", "industry"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["jobs"],
            "additionalProperties": False,
        },
    },
}


def extract_jobs(raw_text: str) -> list[dict]:
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_text},
            ],
            "response_format": JOBS_SCHEMA,
            "max_tokens": 8000,
        },
    )
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)["jobs"]
