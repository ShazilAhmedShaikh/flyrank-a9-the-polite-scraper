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
    """Return deterministic cache file path for a URL."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if custom_filename:
        return CACHE_DIR / custom_filename
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
    clean_name = url.split("/")[-2] if url.endswith("/index.html") else url.split("/")[-1]
    clean_name = "".join(c for c in clean_name if c.isalnum() or c in ("-", "_", ".")).strip()
    return CACHE_DIR / f"{clean_name}_{url_hash}.html"

def fetch_html(
    url: str,
    cache_filename: Optional[str] = None,
    delay: float = POLITE_DELAY_SECONDS,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = 1
) -> Tuple[str, bool]:
    """
    Polite fetcher with local caching and single retry on transient failures:
    - Returns (html_content, is_cache_hit).
    - If cached: returns local file without network call.
    - If not cached: waits polite delay, sends honest User-Agent, checks status 200.
    - Retry policy: Retries once on timeout or 5xx server error.
    - Never retries 404 (Not Found) or 403 (Forbidden).
    """
    cache_path = get_cache_path(url, custom_filename=cache_filename)

    # 1. Check local disk cache
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"[CACHE HIT] {url} ({len(html)} bytes from {cache_path})")
        return html, True

    # 2. Network request with controlled retry
    attempt = 0
    headers = {"User-Agent": USER_AGENT}

    while attempt <= max_retries:
        attempt += 1
        # Polite rate limiting before network request
        if delay > 0:
            time.sleep(delay)

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            status_code = response.status_code

            # Do NOT retry client errors (404 Not Found, 403 Forbidden)
            if status_code in (404, 403):
                raise requests.HTTPError(
                    f"HTTP {status_code} for {url} (client error: will not retry)",
                    response=response
                )

            # Retry on 5xx Server Error
            if 500 <= status_code < 600:
                if attempt <= max_retries:
                    print(f"[RETRY] HTTP {status_code} on {url}, retrying attempt {attempt + 1}...")
                    time.sleep(1.0)
                    continue
                else:
                    raise requests.HTTPError(f"HTTP {status_code} for {url} after retries", response=response)

            if status_code != 200:
                raise requests.HTTPError(f"Unexpected status HTTP {status_code} for {url}", response=response)

            response.encoding = response.apparent_encoding or "utf-8"
            html = response.text
            cache_path.write_text(html, encoding="utf-8")
            print(f"[FETCH] {url} ({len(html)} bytes, HTTP {status_code} saved to {cache_path})")
            return html, False

        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt <= max_retries:
                print(f"[RETRY] Network timeout/error for {url}: {exc}. Retrying once...")
                time.sleep(1.0)
                continue
            raise exc
