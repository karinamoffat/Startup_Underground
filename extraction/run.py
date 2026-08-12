import json
from pathlib import Path

from extract import extract_jobs

INPUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "a16z_build.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "extracted" / "a16z_build.json"

if __name__ == "__main__":
    posts = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    jobs = []
    for post in posts:
        for job in extract_jobs(post["raw_text"]):
            jobs.append({
                **job,
                "source": post["source"],
                "url": post["url"],
                "date_posted": post["date_posted"],
                "date_scraped": post["date_scraped"],
                "raw_text": post["raw_text"],
            })
        print(f"{post['title']}: {len(jobs)} jobs so far")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    print(f"Extracted {len(jobs)} jobs from {len(posts)} posts -> {OUTPUT_PATH}")
