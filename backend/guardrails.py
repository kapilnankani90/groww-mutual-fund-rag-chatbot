import re
from typing import Dict, Any, Tuple

# Regex patterns for Indian PII details
PAN_PATTERN = re.compile(r'\b[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}\b')
AADHAAR_PATTERN = re.compile(r'\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b')
# Support standard 10-digit numbers with optional country code, spaces, or hyphens
PHONE_PATTERN = re.compile(r'\b(?:\+?91[\s\-]?)?[6-9](?:\s?\d){9}\b')
EMAIL_PATTERN = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

# Advisory check words / patterns
ADVISORY_KEYWORDS = [
    r"should\s+i",
    r"buy\s+or\s+sell",
    r"best\s+fund",
    r"recommend",
    r"suggest",
    r"better",
    r"compare",
    r"comparison",
    r"where\s+should\s+i\s+put",
    r"portfolio\s+allocation",
    r"portfolio\s+advice",
    r"investment\s+advice",
    r"advise\s+me",
    r"top\s+fund\s+to\s+grow",
    r"make\s+money",
    r"is\s+it\s+safe\s+to\s+invest",
    r"good\s+choice",
    r"wealth\s+creation",
    r"maximize\s+returns",
    r"guaranteed\s+return",
    r"financial\s+advice",
    r"advice\s+on\s+investing",
    r"is\s+it\s+worth"
]

ADVISORY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ADVISORY_KEYWORDS]

def detect_pii(query: str) -> Tuple[bool, str]:
    """
    Scans the query for personal identifiable information (PAN, Aadhaar, phone numbers, emails).
    Returns (has_pii, pii_type).
    """
    if PAN_PATTERN.search(query):
        return True, "PAN Card"
    if AADHAAR_PATTERN.search(query):
        return True, "Aadhaar Card"
    if PHONE_PATTERN.search(query):
        return True, "Phone Number"
    if EMAIL_PATTERN.search(query):
        return True, "Email Address"
    return False, ""

def is_advisory_query(query: str) -> bool:
    """
    Scans the query for keywords indicating investment advisory requests.
    """
    for pattern in ADVISORY_PATTERNS:
        if pattern.search(query):
            return True
    return False

def process_query_guardrails(query: str) -> Dict[str, Any]:
    """
    Main entry point for processing query guardrails.
    Returns a dictionary indicating safety status and refusal response if needed.
    """
    # 1. PII Check
    has_pii, pii_type = detect_pii(query)
    if has_pii:
        return {
            "is_safe": False,
            "should_refuse": True,
            "refusal_reason": f"PII_DETECTED_{pii_type.upper().replace(' ', '_')}",
            "response": (
                "For your security and privacy, please do not share personal details "
                "such as PAN numbers, Aadhaar numbers, phone numbers, or email addresses. "
                "How can I help you with factual mutual fund details instead?"
            )
        }

    # 2. Advisory Check
    if is_advisory_query(query):
        return {
            "is_safe": False,
            "should_refuse": True,
            "refusal_reason": "ADVISORY_QUERY",
            "response": (
                "I can only provide factual details about these ICICI Prudential mutual funds. "
                "I am not authorized to offer investment advice or recommendations. "
                "For investment advice, please consult a SEBI-registered advisor. "
                "You can learn more about mutual funds on the official "
                "[AMFI](https://www.amfiindia.com) or [SEBI](https://www.sebi.gov.in) websites."
            )
        }

    # 3. Query is Safe
    return {
        "is_safe": True,
        "should_refuse": False,
        "refusal_reason": None,
        "response": None
    }
