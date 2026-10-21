import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

def normalize_price(price_text: str) -> float:
    """
    Extract numeric price in GBP from raw text string (e.g. '£51.77' -> 51.77).
    """
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if not match:
        raise ValueError(f"Unable to parse numeric price from: {price_text!r}")
    return round(float(match.group(1)), 2)

class BookRecord(BaseModel):
    """
    Schema for validated and normalized book record.
    The raw value (price_text) and clean value (price_gbp) live side by side.
    """
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical product URL (must start with https://)")
    price_text: str = Field(..., min_length=1, description="Original raw price text from page")
    price_gbp: float = Field(..., ge=0.0, description="Clean numeric price in GBP")
    availability_text: str = Field(..., description="Raw stock availability string")
    rating_text: str = Field(..., description="Rating text ('One' to 'Five')")
    description: Optional[str] = Field(None, description="Product description, null if missing")
    source_page: str = Field(..., description="Catalogue page URL where link was discovered")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp of fetch")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL must start with 'https://', received: {v}")
        return v
