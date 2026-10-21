"""
The Polite Scraper - Entry Point
FlyRank Backend Internship - Week 5 Assignment A9
"""
import json
from src.crawler import crawl_catalogue
from src.fetcher import fetch_html
from src.parser import parse_book_detail

START_URL = "https://books.toscrape.com/catalogue/page-1.html"

def main():
    print("--- Stage 3 Checkpoint: Extract book details ---")
    crawl_result = crawl_catalogue(START_URL, max_pages=3)
    unique_urls = crawl_result["unique_urls"]
    url_to_source = crawl_result["url_to_source_page"]

    raw_records = []
    for idx, url in enumerate(unique_urls, 1):
        # Deterministic cache filename for each book detail page
        slug = url.rstrip("/").split("/")[-2]
        cache_name = f"book-{slug}.html"
        html, _ = fetch_html(url, cache_filename=cache_name)
        source_page = url_to_source.get(url, START_URL)
        record = parse_book_detail(html, product_url=url, source_page=source_page)
        raw_records.append(record)

    # Print one complete sample raw record
    if raw_records:
        print("Sample Raw Record:")
        print(json.dumps(raw_records[0], indent=2))

    print(f"detail_pages={len(raw_records)}")

if __name__ == "__main__":
    main()
