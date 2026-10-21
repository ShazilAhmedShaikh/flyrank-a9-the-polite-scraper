# The Polite Scraper

> **FlyRank Backend Internship — Week 5 · Assignment A9**  
> A resilient, polite web scraping pipeline built with Python, Requests, Beautiful Soup, and Pydantic. Downloads the first three catalogue pages of Books to Scrape, visits all 60 book detail pages, turns messy HTML into clean, checked JSON records, survives broken pages without crashing, and generates an honest run report.

---

## 🎯 Target Classification

- **Target Site:** Books to Scrape (`https://books.toscrape.com`)
- **Site Purpose & Permission:** Books to Scrape is a public practice sandbox explicitly built by Scrapinghub / Zyte so developers can safely practice scraping without legal or operational barriers.
- **Robots Exclusion Protocol (`robots.txt`) Check:**
  - Request URL: `https://books.toscrape.com/robots.txt`
  - Result: HTTP `404 Not Found` — *no robots file found*. (Note: A missing robots file is not blanket permission; site classification as a sandbox provides our explicit authorization).
- **Collection Scope:** Exactly the first three catalogue pages (`page-1.html`, `page-2.html`, `page-3.html`), yielding a total of 60 unique book detail pages.
- **Data Collected:** Book title, canonical product URL, raw price text, numeric price in GBP (`price_gbp`), availability string, star rating string, product description (optional/nullable), source catalogue page, and ISO 8601 UTC fetch timestamp.
- **Why This is Appropriate Here:** Collecting 60 public records from a purpose-built sandbox with local caching, request timeouts, and at least 500 ms delay between network calls introduces negligible server load and adheres to polite scraping practices.
- **Commitment:** *"I will not reuse this code on another site without checking its rules and terms first."*
