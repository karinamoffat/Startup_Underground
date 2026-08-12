import hashlib
import re


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def content_hash(company: str, title: str) -> str:
    key = f"{normalize(company)}|{normalize(title)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
