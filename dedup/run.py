import json
from pathlib import Path

from dedup import content_hash

INPUT_PATH = Path(__file__).parent.parent / "data" / "extracted" / "a16z_build.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "deduped" / "a16z_build.json"

if __name__ == "__main__":
    jobs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    seen = {}
    deduped = []
    duplicates = []

    for job in jobs:
        h = content_hash(job["company"], job["title"])
        job["content_hash"] = h
        if h in seen:
            duplicates.append((job, seen[h]))
        else:
            seen[h] = job
            deduped.append(job)

    print(f"{len(jobs)} jobs -> {len(deduped)} unique, {len(duplicates)} duplicates skipped")
    for dup, original in duplicates:
        print(f"  DUP: {dup['company']} - {dup['title']} (first seen in: {original['url']})")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(deduped, indent=2), encoding="utf-8")
    print(f"Wrote deduped jobs -> {OUTPUT_PATH}")
