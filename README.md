# The Polite Scraper

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![BeautifulSoup4](https://img.shields.io/badge/HTML%20Parser-BeautifulSoup4-38bdf8.svg)](https://www.crummy.com/software/BeautifulSoup/)
[![Pydantic](https://img.shields.io/badge/Schema%20Validation-Pydantic%20v2-e11d48.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-8%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **FlyRank Backend Internship — Week 5 · Assignment A9**  
> A polite, resilient, and deterministic scraping pipeline that crawls the first 3 catalogue pages of Books to Scrape, visits all 60 book detail pages, turns messy HTML into validated JSON records, survives broken pages without crashing, and generates an honest execution report.

---

## 📑 Table of Contents
1. [Target Classification & Permission](#-target-classification--permission)
2. [Architecture & Pipeline Stages](#-architecture--pipeline-stages)
3. [Quickstart & Run Command](#-quickstart--run-command)
4. [Record Schema & Validation](#-record-schema--validation)
5. [Politeness Rules & Safety Guarantees](#-politeness-rules--safety-guarantees)
6. [Failure Isolation & Resilience](#-failure-isolation--resilience)
7. [Proof of Run (Live `run-report.json`)](#-proof-of-run-live-run-reportjson)
8. [Why No Browser Was Needed](#-why-no-browser-was-needed)
9. [Web Scraping Ethics Note](#-web-scraping-ethics-note)
10. [Honest Limitations](#-honest-limitations)
11. [Unit Tests & Fixtures](#-unit-tests--fixtures)
12. [Stage 7: AI Rematch ("AI vs Me")](#-stage-7-the-ai-rematch-ai-vs-me)

---

## 🎯 Target Classification & Permission

- **Target Site:** Books to Scrape (`https://books.toscrape.com`)
- **Site Purpose & Legal Permission:** Books to Scrape is an official practice sandbox created by Scrapinghub / Zyte explicitly so that developers can test and refine scraping pipelines without legal or operational concerns.
- **Robots Exclusion Protocol (`robots.txt`) Check:**
  - Endpoint Checked: `https://books.toscrape.com/robots.txt`
  - Result: HTTP `404 Not Found` (*"no robots file found"*). A missing file is not blanket permission; site classification as an explicit practice sandbox provides our operational authorization.
- **Scope Limit:** Strictly the first 3 catalogue pages (`page-1.html`, `page-2.html`, `page-3.html`), yielding exactly 60 unique book detail pages.
- **Data Collected:** Book title, canonical product URL, raw price text, normalized numeric price (`price_gbp`), availability string, star rating string, product description (or `null` if missing), source catalogue page, and ISO 8601 UTC timestamp.
- **Why This Scope is Appropriate:** Collecting 60 records from a public sandbox with 500ms delay and local caching introduces zero burden on server resources.
- **Mandatory Statement:**  
  > *"I will not reuse this code on another site without checking its rules and terms first."*

---

## 🏛️ Architecture & Pipeline Stages

```
   ┌────────────────────┐
   │ 1. CRAWL (Stage 2) │ ◄── Discover catalogue page 1 -> 2 -> 3 (follow "next" link)
   └─────────┬──────────┘
             ▼
   ┌────────────────────┐
   │ 2. FETCH (Stage 1) │ ◄── Check cache/ first. If miss: polite delay (500ms) + User-Agent
   └─────────┬──────────┘
             ▼
   ┌────────────────────┐
   │ 3. EXTRACT(Stage 3)│ ◄── Scoped CSS selectors: title, raw price, rating, description
   └─────────┬──────────┘
             ▼
   ┌────────────────────┐
   │ 4. CLEAN  (Stage 4)│ ◄── Parse numeric float price_gbp, keep raw price_text side-by-side
   └─────────┬──────────┘
             ▼
   ┌────────────────────┐
   │ 5. VALIDATE(Stage 4│ ◄── Validate against Pydantic schema (bad records -> errors.json)
   └─────────┬──────────┘
             ▼
   ┌────────────────────┐
   │ 6. STORE & REPORT  │ ◄── Write output/books.json, output/books.csv, output/run-report.json
   └────────────────────┘
```

---

## ⚡ Quickstart & Run Command

### 1. Installation
Clone the repository and install the lightweight dependencies (no heavy browser or database needed):
```bash
git clone https://github.com/ShazilAhmedShaikh/flyrank-a9-the-polite-scraper.git
cd flyrank-a9-the-polite-scraper
pip install -r requirements.txt
```

### 2. Single Documented Run Command
```bash
python -m src.main
```

### 3. Verify Fault Tolerance (Injecting Broken URL)
```bash
python -m src.main --inject-fake-url
```

---

## 📋 Record Schema & Validation

All scraped records are validated against a strict **Pydantic v2** schema before writing to disk. Invalid records are quarantined in `output/errors.json` and never pollute `output/books.json`.

| Field Name | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `title` | `str` | `min_length=1` | Title of the book |
| `product_url` | `str` | Must start with `https://` | Canonical product detail URL |
| `price_text` | `str` | `min_length=1` | Raw price string as displayed (e.g. `£51.77`) |
| `price_gbp` | `float` | `>= 0.0` | Clean normalized numeric price in GBP |
| `availability_text` | `str` | Non-empty | Raw stock availability (e.g. `In stock (22 available)`) |
| `rating_text` | `str` | Word format | Rating extracted from class (e.g. `Three`) |
| `description` | `str \| None` | Optional | Product synopsis (`null` if absent on page) |
| `source_page` | `str` | Must start with `https://` | Provenance receipt: catalogue page of discovery |
| `fetched_at` | `str` | ISO 8601 UTC | Provenance timestamp when the record was captured |

### Sample Validated Record:
```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-10-21T17:55:41Z"
}
```

---

## 🤝 Politeness Rules & Safety Guarantees

1. **Honest User-Agent:** Every HTTP request carries an explicit header:  
   `FlyRankInternship-A9/1.0 (+https://github.com/ShazilAhmedShaikh/flyrank-a9-the-polite-scraper)`  
   This allows webmasters to review who is making requests and contact the repository.
2. **Polite Request Delays:** Enforces a minimum **500 ms delay** (`time.sleep(0.5)`) prior to any network request.
3. **Hard Request Timeout:** Configured with a **10.0-second timeout** to ensure connection hangs never lock the worker.
4. **Local Disk Caching (`cache/`):** All downloaded HTML pages are cached locally. Rerunning tests reads from disk without sending a single network packet to the host.
5. **Idempotency:** Re-running the pipeline multiple times always produces the exact same 60 records, overwriting safely without duplicate accumulation.

---

## 🛡️ Failure Isolation & Resilience

In web scraping, pages break, networks flake, and servers drop connections. Our pipeline implements **page-level isolation**:
- **Transient Failures (Timeouts, 5xx):** The fetcher waits 1 second and retries once.
- **Permanent Client Failures (404, 403):** Does **not** retry. Retrying a 404 won't make a missing page exist; retrying a 403 turns a polite robot into an attacker.
- **Isolated Failure Scope:** If one detail page fails, the error is logged, incremented in `failed_pages`, and the remaining 59 records are successfully stored.

---

## 📊 Proof of Run (Live `run-report.json`)

The following is an exact snippet from a verified execution on 60 book pages:

```json
{
  "start_time": "2026-10-21T17:55:41Z",
  "end_time": "2026-10-21T17:55:43Z",
  "duration_seconds": 2.0,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_urls": [],
  "change_detection": {
    "new": 60,
    "changed": 0,
    "unchanged": 0,
    "gone": 0,
    "total_current": 60
  }
}
```

When run with `--inject-fake-url`, the run report demonstrates failure isolation:
```json
{
  "valid_records": 60,
  "failed_pages": 1,
  "failed_urls": [
    "https://books.toscrape.com/catalogue/deliberately-broken-fake-book_9999/index.html"
  ]
}
```

---

## 🌐 Why No Browser Was Needed

**This assignment needed no browser: the data is already in the HTML the server sends, so a browser would only add cost.**

### Browser Cost Comparison (Quotes to Scrape JS vs Books to Scrape):
- **Dynamic JS Sites (`quotes.toscrape.com/js`):** HTML source arrives empty without quotes; quotes are rendered by client-side JavaScript. Scraping requires a headless browser (Playwright / Puppeteer), consuming **~150 MB RAM** and **1.8+ seconds** per process start.
- **Server-Rendered Sites (`books.toscrape.com`):** Complete catalogue and detail data are embedded directly in the initial HTTP response. Plain **Requests + Beautiful Soup** extracts the entire page in **<50 ms** consuming **<25 MB RAM** — delivering 10x higher throughput at zero browser overhead.

---

## ⚖️ Web Scraping Ethics Note

1. **Check for APIs First:** Always check if the service provides an official REST/GraphQL API before writing scraping scripts.
2. **Never Bypass Security Controls:** Never circumvent authentication walls, paywalls, CAPTCHAs, or IP bans.
3. **Respect Server Resources:** Always throttle request rates, implement request caching during development, and identify your scraper with an honest user-agent and contact link.
4. **Data Minimization:** Extract and store only the minimal subset of data fields necessary for your specific application.

---

## ⚠️ Honest Limitations

- **In-Memory Concurrency Scope:** This scraper is optimized for single-process, polite sequential crawling of small-to-medium catalogue batches (up to several hundred pages).
- **Scale Horizon:** Scaling to thousands or millions of pages would require replacing the synchronous `requests` library with `httpx` / `asyncio`, switching local file caching to Redis/S3, and orchestrating requests via a distributed task queue (Celery/BullMQ).

---

## 🧪 Unit Tests & Fixtures

The pipeline includes **8 automated unit tests** verifying parsers, relative URL conversions, and error handling without hitting the live network:

```bash
python -m pytest -v
```

### Verified Test Cases:
1. `test_price_normalization`: Validates float conversion across currency symbols and edge formats.
2. `test_relative_to_absolute_urls`: Verifies `urljoin` relative path resolution for both book cards and pagination links.
3. `test_missing_description`: Confirms missing descriptions safely evaluate to `None` without fabricating placeholder text.
4. `test_duplicate_urls_deduplicated`: Tests order-preserving URL deduplication.
5. `test_malformed_fixture`: Proves that broken HTML triggers Pydantic schema validation errors and is prevented from entering clean storage.
6. `test_schema_validation`: Enforces required fields and mandatory `https://` protocols.
7. `test_csv_export`: Validates `output/books.csv` formatting and comma escaping.
8. `test_change_detection`: Confirms hashing logic detects new, changed, and unchanged records.

---

## 🤖 Stage 7: The AI Rematch ("AI vs Me")

In Stage 7, an independent prompt was provided to an AI model in quarantine (`ai-version/scraper.py`) to build the same scraping pipeline.

### Full Prompt Specified:
```text
"Write a polite web scraper in Python using Requests and BeautifulSoup to scrape the Books to Scrape website (https://books.toscrape.com).
Requirements:
1. Crawl only the first 3 catalogue pages by dynamically finding the 'next' button link.
2. Discover all book links from those 3 pages (should be 60 books total) and deduplicate them.
3. Visit every book page and extract: title, product_url, price_text, availability_text, rating_text, description (None if missing), source_page, and fetched_at timestamp.
4. Normalize the price into a numeric float price_gbp alongside price_text.
5. Be polite: send a custom User-Agent identifying the bot, use a request timeout, wait at least 500ms between requests, and cache fetched pages to disk so reruns do not hammer the site.
6. Validate records using Pydantic and save to output/books.json. Rerunning should not duplicate records.
7. If one book URL fails (e.g. 404), catch the error, log it, and continue so the other 59 books are saved.
8. Output a run report with statistics."
```

### AI Implementation Flaws & Critical Differences:
1. **URL Concatenation vs. `urljoin`**:
   - *AI Code*: Built URLs via naive string concatenation (`BASE_URL + href`). On relative paths with `../`, this produced invalid addresses like `https://books.toscrape.com/catalogue/../book_1000/index.html`.
   - *Our Implementation*: Uses standard `urllib.parse.urljoin`, correctly resolving relative directories according to RFC standards.
2. **Missing Character Encoding Handling**:
   - *AI Code*: Left default `requests` encoding untouched, causing `£51.77` to be decoded in Latin-1 as corrupt mojibake (`Â£51.77`).
   - *Our Implementation*: Explicitly applies `response.apparent_encoding` or UTF-8, ensuring currency symbols and accents remain pristine.
3. **Hardcoded Pagination vs. Dynamic Discovery**:
   - *AI Code*: Hardcoded a `range(1, 4)` loop generating `page-1.html`, `page-2.html`, `page-3.html`, ignoring the requirement to follow the site's dynamic `"next"` button.
   - *Our Implementation*: Follows the DOM's `li.next a` link dynamically, stopping exactly when the target page limit is satisfied.
4. **Lack of Isolated Page Failure Handlers**:
   - *AI Code*: Wrapped the book fetch inside a generic try-except block that dumped raw stack traces without reporting metrics or tracking failed URLs.
   - *Our Implementation*: Isolates failures cleanly, captures the failed URL into `output/run-report.json`, and preserves clean execution metrics.
