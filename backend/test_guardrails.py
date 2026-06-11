import sys
import os

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardrails import process_query_guardrails

def run_tests():
    # Format of test cases: (query, expected_should_refuse, expected_reason)
    test_cases = [
        # 1. Safe Queries
        ("What is the exit load of the ICICI Prudential Liquid Fund?", False, None),
        ("Who is the fund manager of Large Cap Fund?", False, None),
        ("Show me the NAV details of Silver ETF FoF.", False, None),
        
        # 2. Advisory Queries
        ("Should I invest in ICICI Prudential Large Cap Fund?", True, "ADVISORY_QUERY"),
        ("Which fund is better: Liquid Fund or Large Cap?", True, "ADVISORY_QUERY"),
        ("Can you recommend where to invest my savings?", True, "ADVISORY_QUERY"),
        ("What is the best fund for wealth creation?", True, "ADVISORY_QUERY"),
        ("Is it safe to invest in Silver ETF FoF direct growth?", True, "ADVISORY_QUERY"),
        
        # 3. PII Queries
        ("My PAN card number is ABCDE1234F, tell me my returns.", True, "PII_DETECTED_PAN_CARD"),
        ("Please update my phone number to +91 98765 43210.", True, "PII_DETECTED_PHONE_NUMBER"),
        ("My Aadhaar number is 123456789012, check my account status.", True, "PII_DETECTED_AADHAAR_CARD"),
        ("Can you send the document to investor.help@domain.com?", True, "PII_DETECTED_EMAIL_ADDRESS"),
    ]
    
    print("Running Guardrails Verification Tests...\n")
    failed = 0
    
    for i, (query, exp_refuse, exp_reason) in enumerate(test_cases):
        res = process_query_guardrails(query)
        refused = res["should_refuse"]
        reason = res["refusal_reason"]
        
        status = "PASSED"
        if refused != exp_refuse or (exp_refuse and reason != exp_reason):
            status = "FAILED"
            failed += 1
            
        print(f"Test {i+1}: '{query}'")
        print(f"  Result: Refused={refused}, Reason={reason} -> {status}")
        if refused:
            print(f"  Response: {res['response']}")
        print()
        
    print(f"Verification Summary: {len(test_cases) - failed}/{len(test_cases)} passed.")
    if failed > 0:
        print("Error: Some guardrail tests failed.")
        sys.exit(1)
    else:
        print("Success: All guardrail tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
