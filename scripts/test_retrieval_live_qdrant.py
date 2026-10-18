"""
Tests retrieval directly against the live Qdrant container for C-01 and C-02.
"""
import sys
sys.path.insert(0, "backend")

from app.services.retrieval import RetrievalEngine

def run():
    print("=== Testing C-01 Retrieval against Live Qdrant ===")
    chunks_c01, auth1, ref1 = RetrievalEngine.retrieve_for_client("C-01", "What was the global smart water meter market size in 2024?", limit=5)
    print(f"C-01 Authorized reports: {auth1}")
    print(f"C-01 Chunks returned: {len(chunks_c01)}")
    for c in chunks_c01:
        print(f"  [{c.get('report_id')} p.{c.get('page')}] score={c.get('score')} | {c.get('text')[:60]}...")

    print("\n=== Testing C-02 Retrieval against Live Qdrant ===")
    chunks_c02, auth2, ref2 = RetrievalEngine.retrieve_for_client("C-02", "What was the global smart water meter market size in 2024?", limit=5)
    print(f"C-02 Authorized reports: {auth2}")
    print(f"C-02 Chunks returned: {len(chunks_c02)}")
    for c in chunks_c02:
        print(f"  [{c.get('report_id')} p.{c.get('page')}] score={c.get('score')} | {c.get('text')[:60]}...")

if __name__ == "__main__":
    run()
