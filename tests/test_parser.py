from pathlib import Path
import pytest
from pydantic import ValidationError

from src.models import normalize_price, BookRecord
from src.parser import parse_book_detail
from src.crawler import parse_catalogue_page
from src.extras import export_to_csv, detect_changes

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# 1. Price Normalization Test
def test_price_normalization():
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("£0.00") == 0.00
    assert normalize_price("  £19.99  ") == 19.99
    assert normalize_price("12.50") == 12.50
    assert normalize_price("£100") == 100.0

    with pytest.raises(ValueError):
        normalize_price("Not a price")

# 2. Relative to Absolute URLs Test
def test_relative_to_absolute_urls():
    catalogue_html = """
    <html><body>
        <article class="product_pod">
            <h3><a href="../a-light-in-the-attic_1000/index.html">A Light in the Attic</a></h3>
        </article>
        <li class="next"><a href="page-2.html">next</a></li>
    </body></html>
    """
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    links, next_url = parse_catalogue_page(catalogue_html, base_url)

    assert len(links) == 1
    assert links[0] == "https://books.toscrape.com/a-light-in-the-attic_1000/index.html"
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"
    assert all(l.startswith("https://") for l in links)

# 3. Missing Description Handled Safely (Never invent text, store None/null)
def test_missing_description():
    html = (FIXTURES_DIR / "sample_book_no_description.html").read_text(encoding="utf-8")
    record = parse_book_detail(
        html=html,
        product_url="https://books.toscrape.com/catalogue/no-desc_1/index.html",
        source_page="https://books.toscrape.com/catalogue/page-1.html"
    )

    assert record["title"] == "Book Without Description"
    assert record["description"] is None
    assert record["rating_text"] == "Five"

# 4. Duplicate URLs Deduplicated
def test_duplicate_urls_deduplicated():
    raw_urls = [
        "https://books.toscrape.com/catalogue/book-1/index.html",
        "https://books.toscrape.com/catalogue/book-2/index.html",
        "https://books.toscrape.com/catalogue/book-1/index.html",
        "https://books.toscrape.com/catalogue/book-3/index.html",
        "https://books.toscrape.com/catalogue/book-2/index.html"
    ]
    unique_urls = list(dict.fromkeys(raw_urls))
    assert len(unique_urls) == 3
    assert unique_urls == [
        "https://books.toscrape.com/catalogue/book-1/index.html",
        "https://books.toscrape.com/catalogue/book-2/index.html",
        "https://books.toscrape.com/catalogue/book-3/index.html"
    ]

# 5. Malformed Fixture Handling
def test_malformed_fixture():
    html = (FIXTURES_DIR / "sample_book_malformed.html").read_text(encoding="utf-8")
    record = parse_book_detail(
        html=html,
        product_url="https://books.toscrape.com/catalogue/malformed_99/index.html",
        source_page="https://books.toscrape.com/catalogue/page-1.html"
    )

    # Empty string title and price
    assert record["title"] == ""
    assert record["price_text"] == ""

    # Fails schema validation as expected (catches bad records)
    with pytest.raises(ValidationError):
        BookRecord(
            title=record["title"],
            product_url=record["product_url"],
            price_text=record["price_text"],
            price_gbp=0.0,
            availability_text="In stock",
            rating_text="One",
            description=None,
            source_page=record["source_page"],
            fetched_at="2026-10-21T18:00:00Z"
        )

# 6. Schema Validation Success & Enforces https://
def test_schema_validation():
    valid_data = {
        "title": "Clean Code",
        "product_url": "https://books.toscrape.com/catalogue/clean-code/index.html",
        "price_text": "£29.99",
        "price_gbp": 29.99,
        "availability_text": "In stock (5 available)",
        "rating_text": "Five",
        "description": "A handbook of agile software craftsmanship.",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-21T18:00:00Z"
    }
    rec = BookRecord(**valid_data)
    assert rec.price_gbp == 29.99
    assert rec.product_url.startswith("https://")

    # Reject non-https URL
    invalid_data = dict(valid_data)
    invalid_data["product_url"] = "http://insecure.site/book"
    with pytest.raises(ValidationError):
        BookRecord(**invalid_data)

# 7. CSV Export
def test_csv_export(tmp_path):
    records = [{
        "title": "Test Book",
        "product_url": "https://books.toscrape.com/catalogue/test_1/index.html",
        "price_text": "£10.00",
        "price_gbp": 10.0,
        "availability_text": "In stock",
        "rating_text": "Four",
        "description": "Short description",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-21T18:00:00Z"
    }]
    csv_file = tmp_path / "test_books.csv"
    export_to_csv(records, csv_file)
    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "Test Book" in content
    assert "10.0" in content

# 8. Change Detection
def test_change_detection(tmp_path):
    state_file = tmp_path / ".test_state.json"
    records_v1 = [{
        "title": "Book A",
        "product_url": "https://books.toscrape.com/catalogue/book-a/index.html",
        "price_gbp": 15.0,
        "availability_text": "In stock",
        "rating_text": "Three",
        "description": "Desc A"
    }]

    # Run 1: 1 new record
    chg1 = detect_changes(records_v1, state_file)
    assert chg1["new"] == 1
    assert chg1["changed"] == 0

    # Run 2: Same record -> unchanged
    chg2 = detect_changes(records_v1, state_file)
    assert chg2["unchanged"] == 1
    assert chg2["new"] == 0

    # Run 3: Price changed
    records_v2 = list(records_v1)
    records_v2[0] = dict(records_v1[0])
    records_v2[0]["price_gbp"] = 18.5
    chg3 = detect_changes(records_v2, state_file)
    assert chg3["changed"] == 1
