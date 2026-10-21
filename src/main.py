"""
The Polite Scraper - Entry Point
FlyRank Backend Internship - Week 5 Assignment A9
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import ValidationError

from src.crawler import crawl_catalogue
from src.fetcher import fetch_html
from src.parser import parse_book_detail
from src.models import BookRecord, normalize_price

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
OUTPUT_DIR = Path("output")

def run_pipeline() -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    crawl_result = crawl_catalogue(START_URL, max_pages=3)
    unique_urls = crawl_result["unique_urls"]
    url_to_source = crawl_result["url_to_source_page"]

    valid_records: List[Dict[str, Any]] = []
    invalid_records: List[Dict[str, Any]] = []
    seen_urls = set()

    for url in unique_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        slug = url.rstrip("/").split("/")[-2]
        cache_name = f"book-{slug}.html"
        html, _ = fetch_html(url, cache_filename=cache_name)
        source_page = url_to_source.get(url, START_URL)
        raw = parse_book_detail(html, product_url=url, source_page=source_page)

        # Normalize and Validate against Pydantic schema
        try:
            price_gbp = normalize_price(raw["price_text"])
            validated_record = BookRecord(
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
            valid_records.append(validated_record.model_dump())
        except (ValidationError, ValueError) as err:
            invalid_records.append({
                "product_url": url,
                "raw_record": raw,
                "error": str(err)
            })

    # Save to output/books.json (idempotent write)
    books_file = OUTPUT_DIR / "books.json"
    books_file.write_text(json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8")

    # If any invalid records, store in output/errors.json
    errors_file = OUTPUT_DIR / "errors.json"
    if invalid_records:
        errors_file.write_text(json.dumps(invalid_records, indent=2, ensure_ascii=False), encoding="utf-8")
    elif errors_file.exists():
        errors_file.unlink()

    return {
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "records": valid_records
    }

def main():
    print("--- Stage 4 Checkpoint: Clean it, check it, store it ---")
    result = run_pipeline()
    records = result["records"]
    
    count = len(records)
    all_prices_numeric = all(isinstance(r["price_gbp"], (int, float)) for r in records)
    all_urls_https = all(r["product_url"].startswith("https://") for r in records)

    print(f"books.json has {count} records")
    print(f"every price_gbp is a number: {all_prices_numeric}")
    print(f"every URL starts with https://: {all_urls_https}")

if __name__ == "__main__":
    main()
