import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

def export_to_csv(records: List[Dict[str, Any]], csv_path: Path) -> Path:
    """
    Export validated records to CSV format.
    Flattens records and ensures proper CSV escaping for quotes/commas.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        csv_path.write_text("", encoding="utf-8")
        return csv_path

    fieldnames = [
        "title",
        "product_url",
        "price_text",
        "price_gbp",
        "availability_text",
        "rating_text",
        "description",
        "source_page",
        "fetched_at"
    ]

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: (r.get(k) if r.get(k) is not None else "") for k in fieldnames})

    return csv_path

def hash_record(record: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of core scraped fields."""
    core_data = {
        "title": record.get("title"),
        "price_gbp": record.get("price_gbp"),
        "availability_text": record.get("availability_text"),
        "rating_text": record.get("rating_text"),
        "description": record.get("description")
    }
    dumped = json.dumps(core_data, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()

def detect_changes(current_records: List[Dict[str, Any]], state_path: Path) -> Dict[str, Any]:
    """
    Compare current scrape against previous state file to detect:
    new, changed, unchanged, and gone records.
    """
    current_map = {r["product_url"]: hash_record(r) for r in current_records}
    previous_map = {}

    if state_path.exists():
        try:
            previous_map = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            previous_map = {}

    new_urls = [url for url in current_map if url not in previous_map]
    gone_urls = [url for url in previous_map if url not in current_map]
    changed_urls = [url for url in current_map if url in previous_map and current_map[url] != previous_map[url]]
    unchanged_urls = [url for url in current_map if url in previous_map and current_map[url] == previous_map[url]]

    # Save new state
    state_path.write_text(json.dumps(current_map, indent=2), encoding="utf-8")

    return {
        "new": len(new_urls),
        "changed": len(changed_urls),
        "unchanged": len(unchanged_urls),
        "gone": len(gone_urls),
        "total_current": len(current_records)
    }

def generate_dashboard_html(report: Dict[str, Any], records: List[Dict[str, Any]], output_path: Path) -> Path:
    """Generate a clean, standalone HTML dashboard visualizing run stats and metrics."""
    prices = [r["price_gbp"] for r in records if isinstance(r.get("price_gbp"), (int, float))]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>The Polite Scraper - Live Run Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: #1e293b; padding: 1.5rem; border-radius: 8px; border: 1px solid #334155; }}
        .card-val {{ font-size: 2rem; font-weight: bold; color: #38bdf8; }}
        .card-label {{ color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; margin-top: 0.5rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; font-size: 0.875rem; }}
        th {{ background: #0f172a; color: #cbd5e1; }}
        tr:hover {{ background: #334155; }}
        .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: #0284c7; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>The Polite Scraper Dashboard</h1>
        <div class="subtitle">Execution Report: {report.get('start_time')} | Target: Books to Scrape</div>
        
        <div class="grid">
            <div class="card">
                <div class="card-val">{report.get('valid_records', 0)}</div>
                <div class="card-label">Validated Records</div>
            </div>
            <div class="card">
                <div class="card-val">{report.get('cache_hits', 0)}</div>
                <div class="card-label">Cache Hits</div>
            </div>
            <div class="card">
                <div class="card-val">£{avg_price}</div>
                <div class="card-label">Average Price (Range: £{min_price} - £{max_price})</div>
            </div>
            <div class="card">
                <div class="card-val">{report.get('failed_pages', 0)}</div>
                <div class="card-label">Failed Pages Isolated</div>
            </div>
        </div>

        <h2>Sample Scraped Records (First 5 of {len(records)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Price</th>
                    <th>Rating</th>
                    <th>Availability</th>
                </tr>
            </thead>
            <tbody>
"""
    for r in records[:5]:
        html += f"""                <tr>
                    <td><strong>{r.get('title')}</strong></td>
                    <td>£{r.get('price_gbp')}</td>
                    <td><span class="badge">{r.get('rating_text')} Stars</span></td>
                    <td>{r.get('availability_text')}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
