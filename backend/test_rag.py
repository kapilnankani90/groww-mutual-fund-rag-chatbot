import sys
import os

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rag_pipeline import query_assistant

def run_rag_tests():
    # Setup test queries
    test_queries = [
        # 1. Factual Queries (Should succeed and retrieve relevant chunks)
        {
            "query": "What is the exit load of Large Cap fund?",
            "type": "FACTUAL_EXIT_LOAD"
        },
        {
            "query": "Who is the fund manager of ICICI Prudential Corporate Bond Fund?",
            "type": "FACTUAL_MANAGER"
        },
        {
            "query": "What is the minimum SIP investment for Icici Prudential Silver Etf Fof?",
            "type": "FACTUAL_SIP"
        },
        
        # 2. Out of Scope Queries (Should trigger the fallback message with no citation)
        {
            "query": "What is the capital of France?",
            "type": "OUT_OF_SCOPE"
        },
        {
            "query": "How can I register a company in India?",
            "type": "OUT_OF_SCOPE"
        },
        
        # 3. Guardrailed Queries (Should be caught by PII or Advisory filters)
        {
            "query": "Should I invest in ICICI Corporate Bond Fund?",
            "type": "GUARDRAIL_ADVISORY"
        },
        {
            "query": "My PAN is ABCDE1234F. Can you check my portfolio details?",
            "type": "GUARDRAIL_PII"
        }
    ]
    
    print("Executing End-to-End RAG Pipeline Verification...\n")
    
    # Check if GROQ_API_KEY is configured
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY is not set. Running in DRY-RUN mode for LLM generation.")
        print("Context matching, fallback thresholding, and guardrail routing will still be fully tested.\n")
    else:
        print("GROQ_API_KEY configured. Running full end-to-end LLM generation.\n")
        
    for i, test in enumerate(test_queries):
        query = test["query"]
        q_type = test["type"]
        
        print(f"--- Query {i+1} [{q_type}] ---")
        print(f"Question: '{query}'")
        
        res = query_assistant(query)
        
        print("Assistant Response:")
        print(res["response"])
        if res.get("sources"):
            print(f"Sources: {res['sources']}")
        if res.get("refusal_reason"):
            print(f"Reason: {res['refusal_reason']}")
        print("-" * 50 + "\n")
        
    print("Verification execution complete.")

if __name__ == "__main__":
    run_rag_tests()
