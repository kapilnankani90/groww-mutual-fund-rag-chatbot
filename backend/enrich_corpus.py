"""
enrich_corpus.py - Enriches the scraped corpus with JS-rendered fields
(expense ratio, minimum investment amounts, fund manager details) by fetching 
from Groww's internal API.

Run this once after scraping to patch the corpus JSON:
  python backend/enrich_corpus.py
"""
import json
import os
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

GROWW_API_TEMPLATE = "https://groww.in/v1/api/data/mf/web/v4/scheme/search/{slug}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_groww_fund_data(url: str) -> dict:
    """Fetches complete fund data from Groww's internal API."""
    slug = url.rstrip("/").split("/")[-1]
    api_url = GROWW_API_TEMPLATE.format(slug=slug)
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            return resp.json()
        print(f"  API returned {resp.status_code} for {slug}")
        return {}
    except Exception as e:
        print(f"  API error for {slug}: {e}")
        return {}


def fmt_inr(amount) -> str:
    """Format a number as Indian Rupee string."""
    if amount is None:
        return ""
    try:
        val = float(amount)
        if val >= 1_00_00_000:
            return f"₹{val/1_00_00_000:.2f} Cr"
        if val >= 1_00_000:
            return f"₹{val/1_00_000:.2f} L"
        return f"₹{int(val):,}"
    except (ValueError, TypeError):
        return str(amount)


def extract_fields(data: dict) -> dict:
    """Extract all key fields from the Groww API response."""
    result = {}

    # Expense ratio
    er = data.get("expense_ratio")
    if er is not None:
        result["expense_ratio"] = f"{er}%"

    # Min lump sum investment
    min_lump = data.get("min_investment_amount")
    if min_lump:
        result["min_lump"] = fmt_inr(min_lump)

    # Min additional investment
    mini_add = data.get("mini_additional_investment")
    if mini_add:
        result["min_additional"] = fmt_inr(mini_add)

    # Min SIP
    min_sip = data.get("min_sip_investment")
    if min_sip:
        result["min_sip"] = fmt_inr(min_sip)

    # AUM
    aum = data.get("aum")
    if aum:
        result["aum"] = fmt_inr(aum) + " Cr" if isinstance(aum, float) else fmt_inr(aum)

    # Exit load text
    exit_load = data.get("exit_load")
    if exit_load:
        result["exit_load"] = str(exit_load)

    # Stamp duty
    stamp_duty = data.get("stamp_duty")
    if stamp_duty:
        result["stamp_duty"] = str(stamp_duty)

    # Riskometer — risk level classification
    # 'risk' field in Groww API contains the riskometer label (e.g. 'Very High', 'Moderate')
    risk = data.get("risk")
    if risk:
        result["riskometer"] = str(risk)
    
    # nfo_risk as fallback riskometer label
    nfo_risk = data.get("nfo_risk")
    if nfo_risk and not result.get("riskometer"):
        result["riskometer"] = str(nfo_risk)

    # Benchmark index
    benchmark = data.get("benchmark_name") or data.get("benchmark")
    if benchmark:
        result["benchmark"] = str(benchmark)

    # Tax impact / category info
    cat_info = data.get("category_info") or {}
    tax_impact = cat_info.get("tax_impact") if isinstance(cat_info, dict) else None
    if tax_impact:
        result["tax_impact"] = str(tax_impact)

    # Lock-in period (mainly relevant for ELSS funds)
    lock_in = data.get("lock_in") or {}
    if isinstance(lock_in, dict):
        years = lock_in.get("years")
        months = lock_in.get("months")
        days = lock_in.get("days")
        if years:
            result["lock_in"] = f"{years} year(s)"
        elif months:
            result["lock_in"] = f"{months} month(s)"
        elif days:
            result["lock_in"] = f"{days} day(s)"
        else:
            result["lock_in"] = "No lock-in period"
    
    # Category and sub-category
    category = data.get("category")
    sub_cat = data.get("sub_category")
    if category:
        result["category"] = str(category)
    if sub_cat:
        result["sub_category"] = str(sub_cat)

    # Fund manager details
    mgr_details = data.get("fund_manager_details", [])
    if mgr_details and isinstance(mgr_details, list):
        mgrs = []
        for mgr in mgr_details:
            # Groww API uses 'person_name' and 'date_from' (not 'name' and 'managing_since')
            name = mgr.get("person_name") or mgr.get("name", "")
            date_from = mgr.get("date_from", "")
            # Convert ISO date to readable format
            since = date_from[:7] if date_from else ""  # e.g. "2025-10"
            education = mgr.get("education", "")
            experience = mgr.get("experience", "")
            if name:
                mgrs.append({
                    "name": name,
                    "since": since,
                    "education": education,
                    "experience": experience,
                })
        if mgrs:
            result["fund_managers"] = mgrs

    return result


def build_enriched_text_block(fields: dict, fund_title: str) -> str:
    """Build a clean, structured text block from enriched fields."""
    lines = [f"Fund: {fund_title}", ""]

    if fields.get("category"):
        cat_line = fields["category"]
        if fields.get("sub_category"):
            cat_line += f" - {fields['sub_category']}"
        lines.append(f"Fund Category: {cat_line}")

    if fields.get("riskometer"):
        lines.append(f"Riskometer / Risk Classification: {fields['riskometer']}")

    if fields.get("benchmark"):
        lines.append(f"Benchmark Index: {fields['benchmark']}")

    if fields.get("lock_in"):
        lines.append(f"Lock-in Period: {fields['lock_in']}")

    if fields.get("expense_ratio"):
        lines.append(f"Expense Ratio: {fields['expense_ratio']}")

    if fields.get("min_lump"):
        lines.append(f"Minimum Lumpsum Investment (1st): {fields['min_lump']}")

    if fields.get("min_additional"):
        lines.append(f"Minimum Additional Investment: {fields['min_additional']}")

    if fields.get("min_sip"):
        lines.append(f"Minimum SIP Investment: {fields['min_sip']}")

    if fields.get("aum"):
        lines.append(f"Assets Under Management (AUM): {fields['aum']}")

    if fields.get("exit_load"):
        lines.append(f"Exit Load: {fields['exit_load']}")

    if fields.get("stamp_duty"):
        lines.append(f"Stamp Duty: {fields['stamp_duty']}")

    if fields.get("tax_impact"):
        lines.append(f"Tax Implication: {fields['tax_impact']}")

    if fields.get("fund_managers"):
        mgr_names = ", ".join(m["name"] for m in fields["fund_managers"])
        lines.append(f"Fund Managers: {mgr_names}")
        for mgr in fields["fund_managers"]:
            since = mgr.get("since", "")
            edu = mgr.get("education", "")
            exp = mgr.get("experience", "")[:150]
            lines.append(f"  - {mgr['name']} (Managing Since: {since})")
            if edu:
                lines.append(f"    Education: {edu}")
            if exp:
                lines.append(f"    Experience: {exp}")

    return "\n".join(lines)



def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, "data", "mutual_funds_corpus.json")

    print(f"Loading corpus from {corpus_path}...")
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    print(f"Enriching {len(corpus)} fund entries via Groww API...\n")

    for item in corpus:
        url = item.get("url", "")
        title = item.get("title", "")
        print(f"Processing: {title}")

        data = fetch_groww_fund_data(url)
        if not data:
            print(f"  Skipping — no data returned\n")
            continue

        fields = extract_fields(data)
        print(f"  Extracted fields: { {k: v for k, v in fields.items() if k != 'fund_managers'} }")
        if fields.get("fund_managers"):
            print(f"  Fund managers: {[m['name'] for m in fields['fund_managers']]}")

        # Store raw enriched fields for reference
        item["enriched_fields"] = {k: v for k, v in fields.items() if k != "fund_managers"}

        # Build a clean structured text block and PREPEND it to raw_text
        # This ensures the chunker sees the key financial metrics in the overview section
        enriched_block = build_enriched_text_block(fields, title)
        
        # Insert enriched block right after the header marker so the chunker picks it up
        marker = "Brokerage and charges on Groww"
        if marker in item["raw_text"]:
            item["raw_text"] = item["raw_text"].replace(
                marker,
                marker + "\n\n" + enriched_block + "\n\n",
                1
            )
        else:
            # Fallback: prepend to raw text
            item["raw_text"] = enriched_block + "\n\n" + item["raw_text"]

        print()

    # Save enriched corpus
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"Enrichment complete. Corpus saved to {corpus_path}")
    print("\nNext step: Re-run the embedder to rebuild the vector index:")
    print("  python backend/embedder.py")


if __name__ == "__main__":
    main()
