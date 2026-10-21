"""
The Polite Scraper - Entry Point
FlyRank Backend Internship - Week 5 Assignment A9
"""
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from pydantic import ValidationError

from src.crawler import crawl_catalogue
from src.fetcher import fetch_html
from src.parser import parse_book_detail
from src.models import BookRecord, normalize_price

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
OUTPUT_DIR = Path("output")
FAKE_TEST_URL = "https://books.toscrape.com/catalogue/deliberately-broken-fake-book_9999/index.html"

def run_pipeline(inject_fake_url: bool = False) -> Dict[str, Any]:
    """
    Execute complete scraping pipeline with failure isolation and run reporting:
    - Survives broken pages without crashing.
    - Collects provenance and timing metrics.
    - Writes output/books.json and output/run-report.json.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_clock = time.time()

    pages_fetched = 0
    cache_hits = 0

    # 1. Crawl catalogue pages
    crawl_result = crawl_catalogue(START_URL, max_pages=3)
    unique_urls = list(crawl_result["unique_urls"])
    url_to_source = crawl_result["url_to_source_page"]

    # In Stage 5 checkpoint: inject one fake URL to prove fault tolerance
    if inject_fake_url and FAKE_TEST_URL not in unique_urls:
        print(f"[TEST INJECTION] Adding deliberate broken URL: {FAKE_TEST_URL}")
        unique_urls.append(FAKE_TEST_URL)

    valid_records: List[Dict[str, Any]] = []
    invalid_records: List[Dict[str, Any]] = []
    failed_urls: List[str] = []
    seen_urls = set()

    # 2. Visit each detail page with isolated failure handling
    for url in unique_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        slug = url.rstrip("/").split("/")[-2]
        cache_name = f"book-{slug}.html"

        try:
            html, is_cache = fetch_html(url, cache_filename=cache_name)
            if is_cache:
                cache_hits += 1
            else:
                pages_fetched += 1

            source_page = url_to_source.get(url, START_URL)
            raw = parse_book_detail(html, product_url=url, source_page=source_page)

            # Normalize and Validate against schema
            try:
                price_gbp = normalize_price(raw["price_text"])
                validated = BookRecord(
                    title=raw["title"],
                    product_url=raw["product_url"],
                    price_text=raw["price_text"],
                    price_gbp=price_gbp,
                    availability_text=raw["availability_text"],
                    rating_text=raw["rating_text"],
                    description=raw["description"],
                    source_page=raw["source_page"],
                    fetched_at=raw["fetched_at"]
                )
                valid_records.append(validated.model_dump())
            except (ValidationError, ValueError) as val_err:
                invalid_records.append({
                    "product_url": url,
                    "raw_record": raw,
                    "error": str(val_err)
                })

        except Exception as exc:
            # Page failure isolated: 1 bad page must not kill the run!
            print(f"[ERROR ISOLATED] Failed to process {url}: {exc}")
            failed_urls.append(url)

    # 3. Store valid records
    books_file = OUTPUT_DIR / "books.json"
    books_file.write_text(json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. Store schema validation errors if any
    errors_file = OUTPUT_DIR / "errors.json"
    if invalid_records:
        errors_file.write_text(json.dumps(invalid_records, indent=2, ensure_ascii=False), encoding="utf-8")
    elif errors_file.exists():
        errors_file.unlink()

    # 5. Generate Run Report
    end_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    duration_seconds = round(time.time() - start_clock, 2)

    report = {
        "start_time": start_time_iso,
        "end_time": end_time_iso,
        "duration_seconds": duration_seconds,
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": len(failed_urls),
        "failed_urls": failed_urls
    }

    report_file = OUTPUT_DIR / "run-report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report

def main():
    inject_fake = "--inject-fake-url" in sys.argv
    print(f"--- Stage 5 Checkpoint: Survive failures, report the run (inject_fake={inject_fake}) ---")
    report = run_pipeline(inject_fake_url=inject_fake)
    
    print("\nRun Report Summary:")
    print(json.dumps(report, indent=2))
    print(f"\nCHECKPOINT: books.json has {report['valid_records']} good records | failed_pages: {report['failed_pages']}")

if __name__ == "__main__":
    main()
