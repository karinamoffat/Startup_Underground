import argparse

from search import search

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for jobs")
    parser.add_argument("query", help="Natural language job query")
    parser.add_argument("--location", default=None, help="Filter by location (substring match)")
    parser.add_argument("--min-date-posted", default=None, help="Filter by earliest date_posted (ISO 8601)")
    parser.add_argument("--industry", default=None, help="Filter by industry (exact match on enum)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return")
    args = parser.parse_args()

    results = search(
        args.query,
        location=args.location,
        min_date_posted=args.min_date_posted,
        industry=args.industry,
        top_k=args.top_k,
    )

    if not results:
        print("No results.")
    for r in results:
        print(f"{r['company']} - {r['title']} ({r['location'] or 'location unknown'})")
