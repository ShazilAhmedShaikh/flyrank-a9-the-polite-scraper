import os
import time
import hashlib
from pathlib import Path
from typing import Tuple, Optional
import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/ShazilAhmedShaikh/flyrank-a9-the-polite-scraper)"
DEFAULT_TIMEOUT = 10.0
POLITE_DELAY_SECONDS = 0.5
CACHE_DIR = Path("cache")

def get_cache_path(url: str, custom_filename: Optional[str] = None) -> Path:
    """Return cache file path for a URL."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if custom_filename:
        return CACHE_DIR / custom_filename
    # Generate deterministic safe filename from URL
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
    clean_name = url.split("/")[-2] if url.endswith("/index.html") else url.split("/")[-1]
    clean_name = "".join(c for c in clean_name if c.isalnum() or c in ("-", "_", ".")).strip()
    return CACHE_DIR / f"{clean_name}_{url_hash}.html"

def fetch_html(
    url: str,
    cache_filename: Optional[str] = None,
    delay: float = POLITE_DELAY_SECONDS,
    timeout: float = DEFAULT_TIMEOUT
) -> Tuple[str, bool]:
    """
    Polite fetcher with local caching:
    - Returns (html_content, is_cache_hit)
    - If cached: returns local file without network call.
    - If not cached: waits polite delay, sends honest User-Agent, checks status 200, caches response.
    """
    cache_path = get_cache_path(url, custom_filename=cache_filename)

    # 1. Check local disk cache
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"[CACHE HIT] {url} ({len(html)} bytes from {cache_path})")
        return html, True

    # 2. Polite rate limiting before network request
    if delay > 0:
        time.sleep(delay)

    # 3. Honest network request with timeout
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)

    # 4. Strictly check status code (only 200 means page arrived)
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Failed to fetch {url}: HTTP {response.status_code}",
            response=response
        )

    html = response.text
    # 5. Save copy to cache
    cache_path.write_text(html, encoding="utf-8")
    print(f"[FETCH] {url} ({len(html)} bytes, HTTP {response.status_code} saved to {cache_path})")
    return html, False
