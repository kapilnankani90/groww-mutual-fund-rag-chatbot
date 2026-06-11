import sys, os
sys.stdout.reconfigure(encoding='utf-8')
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.rag_pipeline import retrieve_context

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'data', 'vector_store')
vectorizer_path = os.path.join(base_dir, 'data', 'tfidf_vectorizer.pkl')

tests = [
    "What is the expense ratio of Icici Prudential Silver ETF FoF Direct Growth?",
    "Who manages the Silver ETF FoF fund?",
]

for q in tests:
    print(f"\nQ: {q}")
    docs, metas, dists = retrieve_context(q, db_path, vectorizer_path)
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        print(f"  Result {i+1}: distance={dist:.4f}, section={meta.get('section_type')}, fund={meta.get('fund_title','')[:40]}")
        print(f"    Text preview: {doc[:150]}")
