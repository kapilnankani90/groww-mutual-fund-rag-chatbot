"""
static_knowledge.py - Handles queries that require static/procedural knowledge
not present in the fund-specific corpus (e.g., how to download statements,
ELSS lock-in rules, platform navigation).
"""

import re
from typing import Optional, Dict, Any

# ----- Static Knowledge Base -----
# Each entry: (list_of_regex_patterns, answer_text, source_url)
STATIC_KNOWLEDGE: list = [
    # --- Download Account Statement ---
    (
        [
            r"download.*statement",
            r"account.*statement.*download",
            r"get.*statement",
            r"statement.*download",
            r"how.*statement",
        ],
        (
            "To download your account statement on Groww: "
            "log in to the Groww app or website → go to **Portfolio** → tap **Mutual Funds** → "
            "select **Statements** → choose a date range and fund, then tap **Download**. "
            "Alternatively, you can request a consolidated account statement (CAS) from "
            "[CAMS](https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement) "
            "or [KFintech](https://mfs.kfintech.com/investor/General/ConsolidatedAccountStatement) "
            "using your registered email address."
        ),
        "https://groww.in/p/mutual-funds",
    ),

    # --- Capital Gains Report ---
    (
        [
            r"capital.?gain",
            r"cg.*report",
            r"tax.*report.*mutual",
            r"download.*capital",
        ],
        (
            "To download your Capital Gains report on Groww: "
            "log in → go to **Profile** (top right) → tap **Reports** → select **Capital Gains** → "
            "choose the financial year and click **Download**. "
            "This report is also available via CAMS or KFintech by selecting 'Capital Gains Statement' "
            "on their self-service portals."
        ),
        "https://groww.in/p/mutual-funds",
    ),

    # --- ELSS Lock-in Period ---
    (
        [
            r"elss.*lock.?in",
            r"lock.?in.*elss",
            r"tax.?saving.*fund.*lock",
            r"lock.?in.*tax.?saving",
            r"elss.*period",
            r"equity.?linked.*saving.*lock",
        ],
        (
            "ELSS (Equity Linked Savings Scheme) funds have a mandatory statutory lock-in period of **3 years** "
            "from the date of each investment instalment, as mandated by SEBI regulations. "
            "This means units purchased via lump sum or SIP cannot be redeemed before completing 3 years from "
            "the respective purchase date. ELSS investments qualify for tax deduction under Section 80C of the "
            "Income Tax Act (up to ₹1,50,000 per financial year)."
        ),
        "https://www.sebi.gov.in",
    ),
]


def _compile_patterns(patterns: list) -> list:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Pre-compile all patterns
_COMPILED_KNOWLEDGE = [
    (_compile_patterns(patterns), answer, source)
    for patterns, answer, source in STATIC_KNOWLEDGE
]


def lookup_static_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """
    Checks the query against the static knowledge base.
    Returns a formatted response dict if a match is found, else None.
    """
    query_lower = query.lower()
    for compiled_patterns, answer, source in _COMPILED_KNOWLEDGE:
        for pattern in compiled_patterns:
            if pattern.search(query_lower):
                return {
                    "query": query,
                    "refused": False,
                    "response": f"{answer}\n\n[View Source]({source})",
                    "sources": [source],
                    "static": True,
                }
    return None
