import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

def extract_rating(soup: BeautifulSoup) -> str:
    """Extract rating text (e.g. 'One', 'Two', 'Three', 'Four', 'Five') from star-rating class."""
    rating_el = soup.select_one("p.star-rating")
    if not rating_el:
        return "Zero"
    classes = rating_el.get("class", [])
    rating_classes = [c for c in classes if c != "star-rating"]
    return rating_classes[0] if rating_classes else "Zero"

def parse_book_detail(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse a book detail HTML page into the canonical raw record structure:
    Aim selectors strictly at the product area.
    Never invent text. If description is missing, store None.
    """
    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")

    # 1. Title
    title_el = product_main.select_one("h1") if product_main else soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # 2. Price text
    price_el = product_main.select_one("p.price_color") if product_main else soup.select_one("p.price_color")
    price_text = price_el.get_text(strip=True).replace("\u00c2", "").strip() if price_el else ""

    # 3. Availability text
    avail_el = product_main.select_one("p.instock.availability") if product_main else soup.select_one("p.instock.availability")
    availability_text = " ".join(avail_el.get_text().split()) if avail_el else ""

    # 4. Rating text
    rating_text = extract_rating(soup)

    # 5. Description (optional: #product_description ~ p)
    # If no description header or text exists, store None (null in JSON)
    desc_header = soup.select_one("#product_description")
    desc_el = desc_header.find_next_sibling("p") if desc_header else None
    description = desc_el.get_text(strip=True) if desc_el else None

    # Timestamp
    if not fetched_at:
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }
