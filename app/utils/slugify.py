import re
import unicodedata


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")
