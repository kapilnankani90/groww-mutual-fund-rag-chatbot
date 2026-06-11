import json
import re
from typing import List, Dict, Any

def clean_and_extract_sections(raw_text: str) -> Dict[str, str]:
    """
    Cleans raw scraper text and extracts logical sections.
    """
    # 1. Strip top header boilerplate
    # Usually ending with "Pricing\nBrokerage and charges on Groww" or similar
    header_marker = "Brokerage and charges on Groww"
    idx = raw_text.find(header_marker)
    if idx != -1:
        content = raw_text[idx + len(header_marker):].strip()
    else:
        content = raw_text.strip()

    # 2. Strip bottom footer boilerplate
    # Usually starting with "Contact Us", "Download the App"
    footer_markers = ["Contact Us", "Download the App", "PRODUCTS", "© 2016-"]
    for marker in footer_markers:
        f_idx = content.find(marker)
        if f_idx != -1:
            content = content[:f_idx].strip()
            break

    # 3. Parse content into lines for structured scanning
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    sections: Dict[str, List[str]] = {
        "overview": [],
        "holdings": [],
        "min_investments": [],
        "returns": [],
        "fees_and_tax": [],
        "management": [],
        "objective_and_info": []
    }
    
    current_section = "overview"
    
    # We will use simple heuristics to detect section changes:
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Section changes detection
        if line.lower() == "holdings (" or line.lower().startswith("holdings ("):
            current_section = "holdings"
            sections[current_section].append(line)
            i += 1
            continue
        elif line.lower() == "minimum investments":
            current_section = "min_investments"
            sections[current_section].append(line)
            i += 1
            continue
        elif line.lower() in ["returns and rankings", "historic returns", "annualised returns", "absolute returns"]:
            current_section = "returns"
            sections[current_section].append(line)
            i += 1
            continue
        elif line.lower() in ["exit load, stamp duty and tax", "exit load", "exit load, stamp duty & tax"]:
            current_section = "fees_and_tax"
            sections[current_section].append(line)
            i += 1
            continue
        elif line.lower() == "fund management":
            current_section = "management"
            sections[current_section].append(line)
            i += 1
            continue
        elif line.lower() in ["investment objective", "fund benchmark", "scheme information document(sid)"]:
            current_section = "objective_and_info"
            sections[current_section].append(line)
            i += 1
            continue

        # Add line to current section with specific rules (like ignoring other schemes list)
        if current_section == "management":
            # If we see "Also manages these schemes", we want to skip until we see the next manager name
            # or the next section.
            if line.lower() == "also manages these schemes":
                # Skip lines until we hit a new section marker or a manager-like line
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # If it's a section header, stop skipping
                    if (next_line.lower() in ["investment objective", "fund benchmark", "scheme information document(sid)",
                                              "minimum investments", "returns and rankings", "exit load, stamp duty and tax", 
                                              "exit load", "holdings ("] or 
                        next_line.lower().startswith("holdings (")):
                        break
                    
                    # If it looks like a manager's name (e.g. Venus Ahuja, Nishit Patel, Sharmila D'Silva, etc.
                    # which are followed by months/years like "Nov 2025", "Jan 2022", "Mar 2026", "- Present")
                    # Let's check the next line to see if it is a date marker like "Jan 2022" or "Nov 2025"
                    if i + 1 < len(lines) and re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}$', lines[i+1]):
                        break
                    if i + 1 < len(lines) and lines[i+1] == "- Present":
                        break
                    
                    i += 1
                continue
            else:
                sections[current_section].append(line)
        elif current_section == "holdings":
            # If we are in holdings, limit holdings to top 10 instruments to avoid huge lists of holdings
            # Let's count how many holdings we've parsed.
            # Typically holdings are grouped in triples or lines: Asset, Sector/Instrument, %
            # Let's just keep the first 30 lines of the holdings section to be safe, which covers about 10 holdings.
            if len(sections["holdings"]) < 35:
                sections[current_section].append(line)
        else:
            sections[current_section].append(line)
            
        i += 1

    # Join lines back into clean paragraphs/strings
    cleaned_sections: Dict[str, str] = {}
    for name, list_lines in sections.items():
        cleaned_sections[name] = "\n".join(list_lines).strip()
        
    return cleaned_sections

def chunk_sections(fund_title: str, url: str, last_updated: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Creates chunks from the extracted sections with appropriate size/metadata.
    """
    chunks = []
    
    # 1. Overview chunk
    if sections.get("overview"):
        chunks.append({
            "text": f"Fund: {fund_title}\nOverview Details:\n{sections['overview']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "overview"
            }
        })
        
    # 2. Holdings chunk
    if sections.get("holdings") and len(sections["holdings"]) > 20:
        chunks.append({
            "text": f"Fund: {fund_title}\n{sections['holdings']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "holdings"
            }
        })

    # 3. Minimum Investments chunk
    if sections.get("min_investments"):
        chunks.append({
            "text": f"Fund: {fund_title}\n{sections['min_investments']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "minimum_investments"
            }
        })

    # 4. Returns chunk
    if sections.get("returns"):
        chunks.append({
            "text": f"Fund: {fund_title}\nReturns and Performance:\n{sections['returns']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "returns"
            }
        })

    # 5. Fees & Tax chunk
    if sections.get("fees_and_tax"):
        chunks.append({
            "text": f"Fund: {fund_title}\nFees, Exit Load, Stamp Duty and Tax Implications:\n{sections['fees_and_tax']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "exit_load_and_expenses"
            }
        })

    # 6. Fund Management chunk
    # Managers are listed sequentially, we can keep them in one chunk or split if extremely long.
    # Since we stripped "Also manages these schemes", it should fit comfortably in one chunk.
    if sections.get("management"):
        chunks.append({
            "text": f"Fund: {fund_title}\nFund Management Team:\n{sections['management']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "management"
            }
        })

    # 7. Objective & Info chunk
    if sections.get("objective_and_info"):
        chunks.append({
            "text": f"Fund: {fund_title}\nInvestment Objective & General Info:\n{sections['objective_and_info']}",
            "metadata": {
                "fund_title": fund_title,
                "source_url": url,
                "last_updated": last_updated,
                "section_type": "objective_and_info"
            }
        })

    return chunks

def process_corpus(corpus_file_path: str) -> List[Dict[str, Any]]:
    with open(corpus_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    all_chunks = []
    for item in data:
        title = item.get("title", "")
        url = item.get("url", "")
        raw_text = item.get("raw_text", "")
        last_updated = item.get("last_updated", "")
        
        sections = clean_and_extract_sections(raw_text)
        chunks = chunk_sections(title, url, last_updated, sections)
        all_chunks.extend(chunks)
        
    return all_chunks

if __name__ == "__main__":
    import os
    import sys
    # Reconfigure stdout to use UTF-8 on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    corpus_path = os.path.join(os.path.dirname(__file__), "..", "data", "mutual_funds_corpus.json")
    if os.path.exists(corpus_path):
        chunks = process_corpus(corpus_path)
        print(f"Successfully generated {len(chunks)} chunks.")
        # Print a sample chunk
        if chunks:
            print("\n--- SAMPLE CHUNK (Type: {}): ---".format(chunks[0]['metadata']['section_type']))
            print(chunks[0]['text'][:500] + "...")
    else:
        print(f"Corpus file not found at {corpus_path}")

