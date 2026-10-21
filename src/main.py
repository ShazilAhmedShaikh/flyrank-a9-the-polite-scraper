"""
The Polite Scraper - Entry Point
FlyRank Backend Internship - Week 5 Assignment A9
"""
from src.crawler import crawl_catalogue

START_URL = "https://books.toscrape.com/catalogue/page-1.html"

def main():
    print("--- Stage 2 Checkpoint: Find all three catalogue pages ---")
    crawl_result = crawl_catalogue(START_URL, max_pages=3)
    
    pages = crawl_result["catalogue_pages"]
    discovered = crawl_result["discovered"]
    unique_count = len(crawl_result["unique_urls"])

    print(f"catalogue_pages={pages}, discovered={discovered}, unique_urls={unique_count}")

if __name__ == "__main__":
    main()
