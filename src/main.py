"""
The Polite Scraper - Entry Point
FlyRank Backend Internship - Week 5 Assignment A9
"""
from src.fetcher import fetch_html

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"

def main():
    print("--- Stage 1 Checkpoint: Fetch once, cache once ---")
    html, is_cache = fetch_html(CATALOGUE_PAGE_1, cache_filename="catalogue-page-1.html")
    status_str = "CACHE HIT" if is_cache else "FETCH"
    print(f"Result: {status_str} | Size: {len(html)} characters")

if __name__ == "__main__":
    main()
