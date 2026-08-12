import feedparser
from bs4 import BeautifulSoup

SOURCE = "a16z_build"
FEED_URL = "https://a16zbuild.substack.com/feed"


def fetch_posts():
    feed = feedparser.parse(FEED_URL)
    posts = []
    for entry in feed.entries:
        html = entry.content[0].value
        raw_text = BeautifulSoup(html, "html.parser").get_text(separator="\n").strip()
        posts.append({
            "source": SOURCE,
            "url": entry.link,
            "title": entry.title,
            "author": entry.get("author"),
            "date_posted": entry.published,
            "raw_text": raw_text,
        })
    return posts
