import requests
from bs4 import BeautifulSoup, Tag
import json
import os
import re
from datetime import datetime
from typing import Optional

# Target URLs for ICICI Prudential Funds (de-duplicated)
URLS: list[str] = [
    "https://groww.in/mutual-funds/icici-prudential-silver-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-balanced-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-liquid-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/icici-prudential-corporate-bond-fund-direct-plan-growth"
]


HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(text: str) -> str:
    """Remove excess whitespace and newlines from a string."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def scrape_fund_page(url: str) -> Optional[dict]:
    """Scrape a single Groww mutual fund page and return structured data."""
    print(f"Scraping: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Decompose noise elements to get clean content
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            if isinstance(tag, Tag):
                tag.decompose()

        # Extract title
        title_tag = soup.find('h1')
        title: str = (
            title_tag.get_text().strip()
            if title_tag
            else url.split('/')[-1].replace('-', ' ').title()
        )
        
        # Override title for the Balanced Advantage Fund URL to match the problem statement naming
        if "icici-prudential-balanced-direct-growth" in url:
            title = "ICICI Prudential Balanced Advantage Fund Direct Growth"

        # Get clean text line by line, deduplicating consecutive identical lines
        lines: list[str] = []
        raw_text: str = soup.get_text(separator='\n')
        for line in raw_text.splitlines():
            cleaned = clean_text(line)
            if cleaned and len(cleaned) > 5:
                if not lines or lines[-1] != cleaned:
                    lines.append(cleaned)

        full_text: str = "\n".join(lines)

        return {
            "title": title,
            "url": url,
            "raw_text": full_text,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    except requests.exceptions.Timeout:
        print(f"Timeout scraping {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error scraping {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error scraping {url}: {e}")
        return None
    except ValueError as e:
        print(f"Parsing error scraping {url}: {e}")
        return None


def main() -> None:
    """Main entry point: scrape all fund URLs and save corpus to JSON."""
    os.makedirs("data", exist_ok=True)
    corpus: list[dict] = []

    for url in URLS:
        data = scrape_fund_page(url)
        if data:
            corpus.append(data)

    output_path = os.path.join("data", "mutual_funds_corpus.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"Scraping complete. Saved {len(corpus)} documents to {output_path}")


if __name__ == "__main__":
    main()
