from typing import List, Tuple, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from src.fetcher import fetch_html

def parse_catalogue_page(html: str, base_url: str) -> Tuple[List[str], str | None]:
    """
    Parse a catalogue page HTML:
    - Extracts all product links as absolute URLs using urljoin.
    - Finds the relative URL for the 'next' page if present.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_links: List[str] = []

    # Product cards are wrapped in article.product_pod
    for item in soup.select("article.product_pod h3 a"):
        href = item.get("href")
        if href:
            absolute_url = urljoin(base_url, href.strip())
            book_links.append(absolute_url)

    # Next page link
    next_btn = soup.select_one("li.next a")
    next_url = None
    if next_btn and next_btn.get("href"):
        next_url = urljoin(base_url, next_btn["href"].strip())

    return book_links, next_url

def crawl_catalogue(start_url: str, max_pages: int = 3) -> Dict[str, any]:
    """
    Politely traverse catalogue up to max_pages:
    - Discovers book links across pages.
    - Follows the site's own pagination links (no hardcoded links).
    - Removes duplicate URLs.
    """
    current_url = start_url
    pages_crawled = 0
    all_discovered: List[str] = []
    page_urls: List[str] = []
    url_to_source_page: Dict[str, str] = {}

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        page_urls.append(current_url)
        cache_name = f"catalogue-page-{pages_crawled}.html"

        html, _ = fetch_html(current_url, cache_filename=cache_name)
        book_links, next_url = parse_catalogue_page(html, current_url)

        for link in book_links:
            all_discovered.append(link)
            if link not in url_to_source_page:
                url_to_source_page[link] = current_url

        current_url = next_url

    # Deduplicate preserving discovery order
    unique_urls = list(dict.fromkeys(all_discovered))

    return {
        "catalogue_pages": pages_crawled,
        "discovered": len(all_discovered),
        "unique_urls": unique_urls,
        "url_to_source_page": url_to_source_page,
        "page_urls": page_urls
    }
