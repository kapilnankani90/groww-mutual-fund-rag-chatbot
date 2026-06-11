import sys
import os

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from rag_pipeline import query_assistant

def run_accuracy_tests():
    # Format: (query, expected_substrings_list)
    tests = [
        (
            "What is the expense ratio of Icici Prudential Silver ETF FoF Direct Growth?",
            ["0.2%", "Silver ETF"]
        ),
        (
            "What is the exit load of Large Cap fund?",
            ["1%", "1 month"]
        ),
        (
            "What is the minimum SIP investment for ICICI Prudential Balanced Advantage Fund Direct Growth?",
            ["100"]
        ),
        (
            "Who manages the ICICI Prudential Corporate Bond Fund?",
            ["Manish Banthia", "Ritesh Lunawat"]
        ),
        (
            "What is the benchmark index of ICICI Prudential Large Cap Fund?",
            ["NIFTY 100"]
        ),
        (
            "Is there a lock-in period for Silver ETF FoF?",
            ["no lock-in", "No lock-in"]
        )
    ]
    
    print("======================================================================")
    print("Running Accuracy & Hallucination Tests...")
    print("======================================================================\n")
    
    failed = 0
    for i, (query, expected_subs) in enumerate(tests):
        print(f"Test {i+1}: Q: '{query}'")
        res = query_assistant(query)
        response_text = res.get("response", "")
        
        print(f"A: {response_text}")
        
        missing = [sub for sub in expected_subs if sub.lower() not in response_text.lower()]
        
        if missing:
            print(f"❌ FAILED: Missing expected factual terms: {missing}")
            failed += 1
        else:
            print("✅ PASSED")
        print("-" * 70)
        
    print(f"Accuracy Testing Summary: {len(tests) - failed}/{len(tests)} passed.")
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_accuracy_tests()
