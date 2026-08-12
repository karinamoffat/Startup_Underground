import json
from datetime import datetime, timezone
from pathlib import Path

from a16z_build import fetch_posts

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "a16z_build.json"

if __name__ == "__main__":
    posts = fetch_posts()
    date_scraped = datetime.now(timezone.utc).isoformat()
    for post in posts:
        post["date_scraped"] = date_scraped

    OUTPUT_PATH.write_text(json.dumps(posts, indent=2), encoding="utf-8")
    print(f"Scraped {len(posts)} posts -> {OUTPUT_PATH}")
