import sys, os
sys.stdout.reconfigure(encoding='utf-8')
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.rag_pipeline import query_assistant

tests = [
    # --- Previously working ---
    ("EXPENSE RATIO",        "What is the expense ratio of Icici Prudential Silver ETF FoF Direct Growth?"),
    ("EXIT LOAD",            "What is the exit load of Large Cap fund?"),
    ("MIN SIP",              "What is the minimum SIP investment for Silver ETF FoF?"),
    ("FUND MANAGERS",        "Who manages the Silver ETF FoF fund?"),
    # --- New requirements ---
    ("RISKOMETER",           "What is the riskometer classification of ICICI Prudential Silver ETF FoF?"),
    ("BENCHMARK",            "What is the benchmark index of ICICI Prudential Large Cap Fund?"),
    ("ELSS LOCK-IN",         "What is the lock-in period for ELSS funds?"),
    ("LOCK-IN SILVER",       "Is there a lock-in period for Silver ETF FoF?"),
    ("DOWNLOAD STATEMENT",   "How do I download my mutual fund account statement from Groww?"),
    ("CAPITAL GAINS",        "How can I download my capital gains report?"),
    ("FUND MGR TENURE",      "Since when is Manish Banthia managing the Silver ETF FoF?"),
    ("FUND MGR EDUCATION",   "What is the education background of Ashwini Bharucha?"),
]

print("=" * 70)
for label, q in tests:
    result = query_assistant(q)
    print(f"\n[{label}]")
    print(f"Q: {q}")
    print(f"A: {result['response']}")
    print("-" * 60)
