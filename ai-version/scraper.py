"""
AI Generated Implementation of Books to Scrape Pipeline (Quarantined)
Created for Bonus Stage: The AI Rematch comparison.
"""
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl
from typing import Optional

BASE_URL = "https://books.toscrape.com/catalogue/"
HEADERS = {"User-Agent": "AIBot/1.0"}

class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

def get_page(url):
    # AI Mistake 1: String-based URL handling without proper urljoin
    # AI Mistake 2: Missing apparent_encoding leads to Â£ currency corruption
    # AI Mistake 3: Naive cache without atomic file operations or status code assertions
    res = requests.get(url, headers=HEADERS, timeout=5)
    return res.text

def main():
    books = []
    # AI Flaw: Hardcoded pagination range instead of dynamic next button parsing
    for page_num in range(1, 4):
        url = f"{BASE_URL}page-{page_num}.html"
        html = get_page(url)
        soup = BeautifulSoup(html, "html.parser")
        for item in soup.select("article.product_pod h3 a"):
            href = item["href"]
            # AI Flaw: String concatenation instead of urljoin
            book_url = BASE_URL + href
            try:
                book_html = get_page(book_url)
                b_soup = BeautifulSoup(book_html, "html.parser")
                title = b_soup.select_one("h1").text
                price = b_soup.select_one("p.price_color").text
                # AI Flaw: Naive float conversion crashes on unexpected non-numeric characters
                price_num = float(price.replace("£", ""))
                books.append({"title": title, "url": book_url, "price": price_num})
            except Exception as e:
                print("Failed book:", e)

    os.makedirs("output", exist_ok=True)
    with open("output/ai_books.json", "w") as f:
        json.dump(books, f, indent=2)

if __name__ == "__main__":
    main()
