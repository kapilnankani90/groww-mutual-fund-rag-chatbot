import os
import sys
import pickle
from typing import List, Dict, Any

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path to ensure module resolution works regardless of cwd
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

def index_corpus() -> None:
    try:
        import chromadb
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as e:
        print(f"Error importing required packages: {e}")
        print("Please ensure you have installed all requirements from backend/requirements.txt")
        sys.exit(1)
        
    from chunker import process_corpus
    
    # Paths — resolve data directory with fallback for Railway deployment
    # Local dev: data/ is at ../data/ (sibling of backend/)
    # Railway (root=backend/): data/ is at ./data/ (inside backend/)
    base_dir = os.path.dirname(backend_dir)
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(os.path.join(data_dir, "mutual_funds_corpus.json")):
        data_dir = os.path.join(backend_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    corpus_path = os.path.join(data_dir, "mutual_funds_corpus.json")
    db_path = os.path.join(data_dir, "vector_store")
    vectorizer_path = os.path.join(data_dir, "tfidf_vectorizer.pkl")
    
    print(f"Processing corpus from {corpus_path}...")
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus file not found at {corpus_path}")
        sys.exit(1)
        
    chunks = process_corpus(corpus_path)
    print(f"Generated {len(chunks)} chunks.")
    
    if not chunks:
        print("No chunks generated. Exiting.")
        sys.exit(0)
        
    # Prepare data for vectorizer and DB insertion
    documents = []
    metadatas = []
    ids = []
    
    for idx, chunk in enumerate(chunks):
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        ids.append(f"chunk_{idx}")
        
    # 2. Fit TF-IDF Vectorizer
    print("Fitting TF-IDF Vectorizer on corpus...")
    # Using 384 features to match MiniLM's typical dimensionality size
    vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
    embeddings = vectorizer.fit_transform(documents).toarray()
    
    # Save the fitted vectorizer so we can use it to encode query texts during retrieval
    print(f"Saving fitted TF-IDF Vectorizer to {vectorizer_path}...")
    os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
        
    # 3. Setup ChromaDB client
    print(f"Initializing local ChromaDB at {db_path}...")
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Recreate the collection to ensure we have a clean index
    collection_name = "mutual_fund_faqs"
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Deleted existing collection '{collection_name}' for clean indexing.")
    except Exception:
        # Collection might not exist yet
        pass
        
    collection = chroma_client.create_collection(name=collection_name)
    
    # 4. Insert chunks and TF-IDF embeddings
    print("Upserting chunks to ChromaDB...")
    embeddings_list = embeddings.tolist()
    
    collection.add(
        documents=documents,
        embeddings=embeddings_list,
        metadatas=metadatas,
        ids=ids
    )
    
    print("Successfully indexed all chunks into ChromaDB!")
    
    # Run a quick self-test
    print("\n--- Running self-test query ---")
    query = "What is the exit load of Large Cap fund?"
    print(f"Query: '{query}'")
    
    # Transform query using the fitted TF-IDF vectorizer
    query_vector = vectorizer.transform([query]).toarray().tolist()[0]
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=2
    )
    
    for i in range(len(results['documents'][0])):
        print(f"\nResult {i+1} (Distance: {results['distances'][0][i]}):")
        print(f"Source URL: {results['metadatas'][0][i]['source_url']}")
        print(f"Section Type: {results['metadatas'][0][i]['section_type']}")
        print(f"Snippet: {results['documents'][0][i][:250]}...")

if __name__ == "__main__":
    index_corpus()
