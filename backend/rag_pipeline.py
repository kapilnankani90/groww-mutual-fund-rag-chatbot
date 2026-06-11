import os
import sys
import pickle
import re
from typing import Dict, Any, Tuple, List
from dotenv import load_dotenv

# Ensure stdout uses UTF-8 on Windows

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path to ensure module resolution works regardless of cwd
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Load environment variables from absolute path at workspace root
base_dir = os.path.dirname(backend_dir)
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path)

from guardrails import process_query_guardrails
from static_knowledge import lookup_static_knowledge

# Configuration
SIMILARITY_THRESHOLD = 1.65  # Raised to include overview/management chunks (distance ~1.46-1.58); true off-scope queries score >1.8
DEFAULT_MODEL = "llama-3.1-8b-instant"


def retrieve_context(query: str, db_path: str, vectorizer_path: str) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
    """
    Retrieves the most similar chunks from local ChromaDB using TF-IDF encoding.
    """
    import chromadb
    
    # Load TF-IDF Vectorizer
    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"TF-IDF vectorizer not found at {vectorizer_path}. Please run backend/embedder.py first.")
        
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
        
    # Transform query to vector
    query_vector = vectorizer.transform([query]).toarray().tolist()[0]
    
    # Initialize Chroma Client
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(name="mutual_fund_faqs")
    
    # Query database — retrieve top 7 to get full cross-section coverage for same fund
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=7
    )
    
    # Extract results safely
    documents = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    distances = results['distances'][0] if results['distances'] else []
    
    return documents, metadatas, distances

def count_sentences(text: str) -> int:
    """
    Rough programmatic sentence counter using regex.
    """
    # Exclude footers/URLs from sentence count
    clean_text = re.sub(r'Last updated from sources:.*', '', text, flags=re.IGNORECASE)
    clean_text = re.sub(r'https?://\S+', '', clean_text)
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', clean_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)

def enforce_sentence_limit(text: str, limit: int = 3) -> str:
    """
    Programmatic response post-processor to guarantee a maximum sentence count.
    """
    # Find footer if exists
    footer_match = re.search(r'(Last updated from sources:.*)', text, flags=re.IGNORECASE)
    footer = footer_match.group(1) if footer_match else ""
    
    # Clean text to split sentences
    main_body = re.sub(r'Last updated from sources:.*', '', text, flags=re.IGNORECASE).strip()
    
    # Split sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', main_body)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > limit:
        main_body = " ".join(sentences[:limit])
        if not main_body.endswith('.') and not main_body.endswith('?'):
            main_body += '.'
            
    # Combine back with footer
    if footer:
        return f"{main_body}\n\n{footer}"
    return main_body

def query_assistant(query: str) -> Dict[str, Any]:
    """
    Executes the full RAG pipeline:
    1. Guardrails check
    2. Context retrieval
    3. Similarity threshold validation
    4. Groq LLM response generation
    5. Programmatic constraint enforcement
    """
    # 1. Input Guardrails Check
    guardrail_result = process_query_guardrails(query)
    if guardrail_result["should_refuse"]:
        return {
            "query": query,
            "refused": True,
            "refusal_reason": guardrail_result["refusal_reason"],
            "response": guardrail_result["response"],
            "sources": []
        }

    # 1b. Static Knowledge Lookup (procedural/regulatory queries)
    static_result = lookup_static_knowledge(query)
    if static_result:
        return static_result
        
    # Paths
    base_dir = os.path.dirname(backend_dir)
    db_path = os.path.join(base_dir, "data", "vector_store")
    vectorizer_path = os.path.join(base_dir, "data", "tfidf_vectorizer.pkl")
    
    # 2. Retrieve Context
    try:
        documents, metadatas, distances = retrieve_context(query, db_path, vectorizer_path)
    except Exception as e:
        return {
            "query": query,
            "refused": False,
            "error": str(e),
            "response": "Error: Database is not initialized. Please run backend/embedder.py first.",
            "sources": []
        }
        
    # Check if empty database or no results
    if not documents or not distances:
        return {
            "query": query,
            "refused": False,
            "response": "I am sorry, but I do not have factual information regarding this question in my knowledge base.",
            "sources": []
        }
        
    # 3. Apply Similarity Threshold
    best_distance = distances[0]
    if best_distance > SIMILARITY_THRESHOLD:
        # Out-of-Scope Fallback (No citation)
        return {
            "query": query,
            "refused": False,
            "refusal_reason": "OUT_OF_SCOPE",
            "response": "I am sorry, but I do not have factual information regarding this question in my knowledge base.",
            "sources": []
        }
        
    # Select best matching chunk and group all chunks from the same fund
    best_metadata = metadatas[0]
    best_fund = best_metadata.get("fund_title", "")
    source_url = best_metadata.get("source_url", "")
    last_updated = best_metadata.get("last_updated", "unknown date")
    
    # Collect all retrieved chunks that belong to the same top-ranked fund
    # This ensures expense ratio, managers, etc. are all available to the LLM
    same_fund_docs = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        if meta.get("fund_title") == best_fund and dist <= SIMILARITY_THRESHOLD:
            same_fund_docs.append(f"[{meta.get('section_type', 'info')}]\n{doc}")
    
    # Combine all same-fund chunks as the context
    best_context = "\n\n---\n".join(same_fund_docs) if same_fund_docs else documents[0]
    
    # 4. Generate LLM Response using Groq
    # Reload .env file dynamically on every request to pick up key changes without server restarts
    load_dotenv(dotenv_path, override=True)
    groq_api_key = os.environ.get("GROQ_API_KEY")
    
    if not groq_api_key or groq_api_key == "your-api-key-here":
        # Fallback if API key is not configured yet (useful for dry runs / setup validation)
        return {
            "query": query,
            "refused": False,
            "response": f"[Dry Run - Groq API Key Not Configured]\nContext matches: {best_metadata.get('fund_title')} - {best_metadata.get('section_type')}\nSource: {source_url}\nLast updated: {last_updated}",
            "sources": [source_url]
        }

        
    try:
        from groq import Groq
        groq_client = Groq(api_key=groq_api_key)
        
        system_prompt = (
            "You are a strict, facts-only Mutual Fund FAQ Assistant. Answer ONLY using the exact facts from the provided context.\n\n"
            "ABSOLUTE RULES — violating any rule makes your answer WRONG:\n"
            "1. DO NOT speculate, infer, assume, or say what is 'typical' or 'usually' the case. If the context does not explicitly state a value, say the refusal phrase.\n"
            "2. DO NOT provide investment advice, opinions, recommendations, predictions, or comparisons.\n"
            "3. Your answer must be a MAXIMUM of 3 short sentences. Be direct and concise.\n"
            "4. Always include the source as a markdown hyperlink in this EXACT format at the END of your answer: [View Source](<source_url>)\n"
            "   Replace <source_url> with the actual URL from the context.\n"
            "5. Do NOT include any date, timestamp, or 'Last updated' line in your response.\n"
            "6. If the context does NOT explicitly contain the answer, respond with EXACTLY this one sentence (no URL, no date):\n"
            "   'I am sorry, but I do not have factual information regarding this question in my knowledge base.'\n"
            "7. Never say 'not explicitly mentioned', 'not provided', 'not available', or 'typically' — just use the refusal phrase.\n"
            "8. Never add disclaimers, caveats, or extra commentary beyond the factual answer + source link."
        )
        
        user_prompt = (
            f"Context:\n{best_context}\n\n"
            f"Scrape Date: {last_updated}\n"
            f"Source URL: {source_url}\n\n"
            f"User Question: {query}\n"
        )
        
        import time
        max_retries = 5
        retry_delay = 2.0
        for attempt in range(max_retries):
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=DEFAULT_MODEL,
                    temperature=0.0,  # Zero temperature for deterministic, factual outputs
                    max_tokens=300
                )
                break
            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e) or "limit reached" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                raise e
        
        raw_response = chat_completion.choices[0].message.content.strip()
        
        # 5. Programmatic Post-Processing Validation
        # Check if LLM refused (returned the refusal phrase)
        REFUSAL_PHRASE = "I am sorry, but I do not have factual information"
        if REFUSAL_PHRASE in raw_response:
            # Strip any accidentally added URLs or footers from refusal
            clean_refusal = "I am sorry, but I do not have factual information regarding this question in my knowledge base."
            return {
                "query": query,
                "refused": False,
                "response": clean_refusal,
                "sources": []
            }

        # Remove any 'Last updated from sources' date line the LLM may have added
        clean_response = re.sub(r'\n*Last updated from sources:.*', '', raw_response, flags=re.IGNORECASE).strip()
        
        # Enforce maximum 3 sentences
        clean_response = enforce_sentence_limit(clean_response, limit=3)
            
        # Ensure citation URL is present as a markdown link [View Source](url)
        if source_url and source_url not in clean_response:
            clean_response = f"{clean_response}\n\n[View Source]({source_url})"
            
        return {
            "query": query,
            "refused": False,
            "response": clean_response,
            "sources": [source_url]
        }
        
    except Exception as e:
        return {
            "query": query,
            "refused": False,
            "error": str(e),
            "response": f"An error occurred while calling the LLM: {str(e)}",
            "sources": [source_url]
        }

if __name__ == "__main__":
    # Small test query when run directly
    print("Testing Query Assistant...")
    res = query_assistant("What is the exit load of Large Cap fund?")
    print(f"Response:\n{res['response']}")
